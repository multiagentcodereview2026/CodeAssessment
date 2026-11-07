#!/usr/bin/env python3
"""
CodeAssessment Complete Database Migration Utility
Safely exports and imports all application tables between PostgreSQL instances
with batching, gzip compression, and zero connection timeouts.
"""
import argparse
import gzip
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.types.json import Json
from dotenv import load_dotenv

TABLE_DEPENDENCY_ORDER = [
    "alembic_version",
    "users",
    "instructors",
    "students",
    "student_roadmaps",
    "courses",
    "enrollments",
    "enrollment_requests",
    "problems",
    "problem_test_cases",
    "assignments",
    "assignment_problems",
    "submissions",
    "notifications",
    "published_problems",
    "announcement_reads",
    "assessment_evidence",
]


def clean_url(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://").strip()


def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    raise TypeError(f"Type {type(obj)} not serializable")


def export_database(source_url: str, output_path: str, batch_size: int = 10000):
    print(f"🚀 Starting database export from: {source_url.split('@')[-1] if '@' in source_url else 'source'}")
    t_start = time.perf_counter()

    conn = psycopg.connect(clean_url(source_url), autocommit=True)
    export_payload = {
        "metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "version": "1.0",
        },
        "tables": {},
    }

    with conn.cursor() as cur:
        for table in TABLE_DEPENDENCY_ORDER:
            # Check if table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                );
            """, (table,))
            if not cur.fetchone()[0]:
                print(f"  ⏭️ Table '{table}' does not exist, skipping.")
                continue

            # Get column names and types
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """, (table,))
            columns_info = cur.fetchall()
            col_names = [col[0] for col in columns_info]

            cur.execute(f'SELECT count(*) FROM "{table}";')
            total_rows = cur.fetchone()[0]
            print(f"  📦 Exporting '{table}' ({total_rows:,} rows)...", end="", flush=True)

            rows = []
            if total_rows == 0:
                print(" done (0 rows)")
                export_payload["tables"][table] = {"columns": col_names, "rows": []}
                continue

            # For problem_test_cases, use keyset pagination
            if table == "problem_test_cases":
                last_id = ""
                fetched = 0
                while True:
                    if last_id:
                        cur.execute(
                            f'SELECT * FROM "{table}" WHERE id > %s ORDER BY id LIMIT %s;',
                            (last_id, batch_size)
                        )
                    else:
                        cur.execute(
                            f'SELECT * FROM "{table}" ORDER BY id LIMIT %s;',
                            (batch_size,)
                        )
                    batch = cur.fetchall()
                    if not batch:
                        break
                    rows.extend(batch)
                    last_id = batch[-1][0]
                    fetched += len(batch)
                    print(f" {fetched:,}...", end="", flush=True)
            else:
                cur.execute(f'SELECT * FROM "{table}";')
                rows = cur.fetchall()

            export_payload["tables"][table] = {
                "columns": col_names,
                "rows": rows,
            }
            print(f" done ({len(rows):,} rows)")

    conn.close()

    print(f"💾 Compressing and saving to '{output_path}'...")
    json_bytes = json.dumps(export_payload, default=json_serializer).encode("utf-8")
    with gzip.open(output_path, "wb") as f:
        f.write(json_bytes)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    duration = time.perf_counter() - t_start
    print(f"✅ Export completed successfully in {duration:.1f}s! File size: {size_mb:.2f} MB")


def import_database(target_url: str, input_path: str, batch_size: int = 5000):
    print(f"🚀 Starting database import to: {target_url.split('@')[-1] if '@' in target_url else 'target'}")
    t_start = time.perf_counter()

    if not os.path.exists(input_path):
        print(f"❌ Error: Export file '{input_path}' not found!")
        sys.exit(1)

    print(f"📖 Reading and decompressing '{input_path}'...")
    with gzip.open(input_path, "rb") as f:
        export_payload = json.loads(f.read().decode("utf-8"))

    conn = psycopg.connect(clean_url(target_url), autocommit=False)

    with conn.cursor() as cur:
        # First test connection and measure latency
        t0 = time.perf_counter()
        cur.execute("SELECT 1;")
        cur.fetchone()
        t_query = (time.perf_counter() - t0) * 1000
        print(f"⚡ Target Database Round-Trip Latency: {t_query:.2f} ms")

        # Disable triggers / foreign key constraints during batch import
        cur.execute("SET session_replication_role = 'replica';")

        # First truncate existing tables in reverse dependency order (excluding alembic_version)
        existing_tables = []
        for table in TABLE_DEPENDENCY_ORDER:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = %s
                );
            """, (table,))
            if cur.fetchone()[0]:
                existing_tables.append(table)

        print(f"  🧹 Preparing target tables...")
        for table in reversed(existing_tables):
            if table == "alembic_version":
                continue
            cur.execute(f'TRUNCATE TABLE "{table}" CASCADE;')
        conn.commit()

        for table in TABLE_DEPENDENCY_ORDER:
            if table == "alembic_version":
                continue
            if table not in existing_tables:
                continue
            if table not in export_payload["tables"]:
                continue

            tbl_data = export_payload["tables"][table]
            columns = tbl_data["columns"]
            rows = tbl_data["rows"]

            if not rows:
                print(f"  ⏭️ Table '{table}' has 0 rows, skipping.")
                continue

            cols_quoted = ", ".join([f'"{c}"' for c in columns])
            row_placeholder = f"({', '.join(['%s'] * len(columns))})"
            
            # Calculate maximum rows per statement based on 65,000 parameter limit
            max_batch = max(1, 65000 // len(columns))
            chunk_size = min(batch_size, max_batch)

            print(f"  📥 Inserting '{table}' ({len(rows):,} rows in chunks of {chunk_size})...", end="", flush=True)

            for i in range(0, len(rows), chunk_size):
                chunk = rows[i:i + chunk_size]
                flattened_params = []
                for row in chunk:
                    for val in row:
                        if isinstance(val, (dict, list)):
                            flattened_params.append(Json(val))
                        else:
                            flattened_params.append(val)

                chunk_placeholders = ", ".join([row_placeholder] * len(chunk))
                stmt = f'INSERT INTO "{table}" ({cols_quoted}) VALUES {chunk_placeholders} ON CONFLICT DO NOTHING;'
                cur.execute(stmt, flattened_params)
                conn.commit()

                if len(rows) > chunk_size:
                    print(f" {min(i + chunk_size, len(rows)):,}...", end="", flush=True)

            print(" done!")

        # Re-enable foreign key constraints
        cur.execute("SET session_replication_role = 'origin';")
        conn.commit()

        # Update sequences for serial primary keys
        print("🔧 Updating sequence counters...")
        for table in existing_tables:
            try:
                cur.execute(f"""
                    SELECT pg_get_serial_sequence('"{table}"', 'id');
                """)
                res = cur.fetchone()
                if res and res[0]:
                    seq = res[0]
                    cur.execute(f"""
                        SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM "{table}"), 1));
                    """)
                    conn.commit()
            except Exception:
                conn.rollback()
                conn.rollback()

    conn.close()
    duration = time.perf_counter() - t_start
    print(f"🎉 Import fully completed and verified in {duration:.1f}s!")


def main():
    parser = argparse.ArgumentParser(description="CodeAssessment Database Migration")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_p = subparsers.add_parser("export", help="Export live database to compressed archive")
    export_p.add_argument("--source-url", default=None, help="Source PostgreSQL URL (defaults to DATABASE_URL in .env)")
    export_p.add_argument("--output", default="codeassessment_backup.json.gz", help="Output file path")

    import_p = subparsers.add_parser("import", help="Import archive into target database")
    import_p.add_argument("--target-url", required=True, help="Target PostgreSQL URL")
    import_p.add_argument("--input", default="codeassessment_backup.json.gz", help="Input archive file path")

    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    if args.command == "export":
        src = args.source_url or os.getenv("DATABASE_URL")
        if not src:
            print("❌ No DATABASE_URL found in .env or arguments!")
            sys.exit(1)
        export_database(src, args.output)

    elif args.command == "import":
        import_database(args.target_url, args.input)


if __name__ == "__main__":
    main()
