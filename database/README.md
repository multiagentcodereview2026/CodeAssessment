# Local database workspace

This folder is for **local-only** PostgreSQL backup files. Database exports can
contain hidden test cases, so files such as `*.dump`, `*.sql`, and `*.db` are
ignored by Git and must never be pushed to a public repository.

## Create a backup

With the CodeAssessment Docker stack running, execute from the project root:

```powershell
docker compose exec postgres pg_dump -U codeassessment -d codeassessment -Fc -f /tmp/codeassessment.dump
docker compose cp postgres:/tmp/codeassessment.dump .\database\backups\codeassessment.dump
```

## Restore a trusted team backup

Copy the privately shared `codeassessment.dump` into `database/backups/`, then
execute from the project root:

```powershell
docker compose up -d postgres
docker compose cp .\database\backups\codeassessment.dump postgres:/tmp/codeassessment.dump
docker compose exec postgres pg_restore -U codeassessment -d codeassessment --clean --if-exists --no-owner --no-privileges /tmp/codeassessment.dump
```

Only trusted developers who are allowed to inspect hidden test data should be
given a database backup. In production, restore the backup from protected
deployment storage instead of copying it into the source repository.
