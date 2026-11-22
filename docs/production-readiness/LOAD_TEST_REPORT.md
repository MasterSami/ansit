# Load test report

Audit date: 2026-11-22.

## New run

**NOT TESTED.** This session had development API listeners on localhost, and the available local project does not prove those listeners are an isolated load-test environment. No load was sent to them. Do not use the historical figures below as current production capacity.

## Existing project run

Source: [`docs/PROGRESS.md`](../PROGRESS.md), Phase 4, Locust on a shared 4-vCPU host, same-host client, 75 seconds per run, 5/8/12 s phone-like audio, no PostgreSQL/Redis in that run.

| Users | RPS | p50 | p95 | p99 | Errors |
|---:|---:|---:|---:|---:|---:|
| 1 | 1.18 | 0.87 s | 1.1 s | 1.2 s | 0 |
| 2 | 1.80 | 1.1 s | 1.6 s | 1.8 s | 0 |
| 4 | 1.77 | 2.3 s | 2.8 s | 2.9 s | 0 |

The project report states the p95 target was met through two concurrent users and exceeded at four. Its shared client/server CPU means the result is not a clean capacity ceiling. The Docker stack was functionally exercised but not load-tested. 5/10/25/50-user scenarios remain **NOT TESTED** for this audit.

## Safe rerun procedure

1. Provision a disposable staging namespace/VM with synthetic or licensed test clips and isolated Postgres/Redis.
2. Confirm the target host, clip corpus, rate-limit override, and abort criteria.
3. Run 1, 5, 10, 25 users and only then 50 if error rate and resource headroom remain safe.
4. Capture Locust CSV plus CPU/RAM/disk, API p50/p95/p99, RPS, 429/5xx, queue timeouts, and model stage metrics.
5. Tear down only the staging environment and preserve the reports.
