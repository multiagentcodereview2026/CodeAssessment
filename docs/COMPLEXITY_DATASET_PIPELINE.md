# Problem complexity metadata pipeline

Each problem can carry two curated targets:

- `target_time_complexity`: expected worst-case Big-O time.
- `target_space_complexity`: expected auxiliary-space Big-O, excluding the input and required output.

The only accepted values are `O(1)`, `O(log n)`, `O(n)`, `O(n log n)`, `O(n^2)`, `O(n^3)`, `O(2^n)`, and `O(n!)`.
They are distinct from Docker's observed runtime and memory, which cannot prove a program's theoretical complexity.

## Prepare the corpus

The source corpus remains outside Git because it contains hidden test cases.
First create the reviewed tag-curated copy:

```powershell
docker compose --profile tools run --rm newfacade-tag-curator
docker compose --profile tools run --rm newfacade-oracle-verifier
```

The oracle verifier compares all generated public/hidden stdin/stdout cases
with the source dataset's `input_output` oracle. It does not execute arbitrary
Python completions from the raw corpus.

Set `GROQ_API_KEY` in the shell (never commit it), then run this explicit Docker job:

```powershell
$env:GROQ_API_KEY = "your-key"
docker compose --profile tools run --rm newfacade-complexity-enricher `
  python -m dataset.enrich_newfacade_complexities `
  --source /newfacade/normalized-newfacade-stdio-tagged.jsonl `
  --output /newfacade/normalized-newfacade-stdio-complexity.jsonl `
  --limit 20
```

The `--limit 20` run is a safe first check. Remove `--limit` for the full corpus. The output is resumable: validated and review-required records are retained, while interrupted or failed records are retried. The prompt sends no test-case values to Groq.

Run the completeness gate before promoting it to the main problem bank:

```powershell
docker compose --profile tools run --rm newfacade-complexity-verifier
```

It passes only when every problem has an allowed, reviewed target TC/SC value.
The `newfacade-importer` service then uses this final complexity file as the
official main problem-bank source and rejects partial complexity metadata.

## Review and apply

Review records with `complexity_needs_review: true`. Only fully validated rows with values from the closed list are applied. Then run a dry run:

```powershell
docker compose --profile tools run --rm newfacade-complexity-importer `
  python -m dataset.migrate_problem_complexities `
  --dataset-path /newfacade/normalized-newfacade-stdio-complexity.jsonl `
  --dry-run
```

Remove `--dry-run` to update PostgreSQL. This migration changes only the five complexity metadata columns on `problems`; it does not delete or alter users, submissions, public cases, or hidden cases.

On startup, the backend adds those nullable columns safely to an existing `problems` table. A new database receives them through the normal SQLAlchemy model creation.
