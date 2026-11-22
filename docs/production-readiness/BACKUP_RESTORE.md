# Backup and restore procedure

Audit date: 2026-11-22. No production data was used and no restore drill was run.

## Data inventory

- PostgreSQL holds reciter metadata, gallery embeddings/centroids, identify event metadata, and feedback. Audio and transcript are not stored.
- Redis holds rate-limit counters and short-lived ambiguous candidate positions; these are ephemeral and expire.
- Quran index, ASR/speaker models, gallery NPZ, and reciter registry are release artifacts. Preserve exact versions/checksums alongside the deployed image.
- Browser listening history is stored only in each user's IndexedDB and is outside the server backup scope.

## Backup policy to configure

- Use encrypted, access-controlled PostgreSQL snapshots plus periodic logical exports; define retention, RPO, and RTO with the service owner.
- Store artifact release manifests/checksums in immutable versioned storage. Keep the prior release for rollback.
- Redis does not require durable backup for the current ephemeral data model; ensure its max-memory/eviction policy does not unexpectedly affect application load.

## Safe logical backup/restore rehearsal

Run only against a disposable staging database, never production without an approved maintenance plan:

```powershell
$env:PGPASSWORD = '<staging-only-secret>'
pg_dump --format=custom --no-owner --file=ansit-staging.dump --dbname="$env:STAGING_DATABASE_URL"
createdb ansit_restore_check
pg_restore --clean --if-exists --no-owner --dbname="$env:RESTORE_DATABASE_URL" ansit-staging.dump
```

Then compare Alembic revision, table counts, active reciter count, gallery vector dimensions/counts, and a synthetic identify request. Destroy the disposable DB using the platform's reviewed procedure after evidence is retained. No commands above were run in this audit.

## Acceptance criteria

Record backup timestamp, encrypted location, restore duration, row/count checks, artifact checksums, and synthetic request result. Until a rehearsal passes, backup/restore is **NOT TESTED** and the final gate remains **NOT READY**.
