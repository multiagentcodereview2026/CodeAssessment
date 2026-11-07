#!/usr/bin/env python3
"""
Reproducible Experiment Script: Database Latency & Handshake Benchmark
Measures TCP/TLS connection time and round-trip query latency.
"""
import json
import os
import sys
import time
from pathlib import Path
import psycopg
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / ".env")

def benchmark_db(url: str, trials: int = 10) -> dict:
    clean_url = url.replace("postgresql+psycopg://", "postgresql://").strip()
    
    # 1. Connect / Handshake
    handshake_times = []
    for _ in range(trials):
        t0 = time.perf_counter()
        conn = psycopg.connect(clean_url, autocommit=True)
        handshake_times.append((time.perf_counter() - t0) * 1000)
        conn.close()

    # 2. Query Round-Trip
    query_times = []
    conn = psycopg.connect(clean_url, autocommit=True)
    with conn.cursor() as cur:
        for _ in range(trials):
            t0 = time.perf_counter()
            cur.execute("SELECT 1;")
            cur.fetchone()
            query_times.append((time.perf_counter() - t0) * 1000)
    conn.close()

    return {
        "handshake_ms_avg": round(sum(handshake_times) / len(handshake_times), 2),
        "handshake_ms_min": round(min(handshake_times), 2),
        "handshake_ms_max": round(max(handshake_times), 2),
        "query_ms_avg": round(sum(query_times) / len(query_times), 2),
        "query_ms_min": round(min(query_times), 2),
        "query_ms_max": round(max(query_times), 2),
    }

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found in .env")
        sys.exit(1)

    print("Running database latency benchmark (10 trials)...")
    res = benchmark_db(db_url, trials=10)
    print(f"Average TLS Handshake: {res['handshake_ms_avg']} ms")
    print(f"Average Query Round-Trip: {res['query_ms_avg']} ms")

    out_file = ROOT_DIR / "research_paper" / "results" / "latency_benchmark.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"Benchmark results saved to: {out_file}")

if __name__ == "__main__":
    main()
