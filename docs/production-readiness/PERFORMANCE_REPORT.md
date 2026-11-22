# Performance report

Audit date: 2026-11-22.

## Current verification

- `npm run build` (also run as Playwright's production web server prerequisite): PASS. Next.js compiled, type-checked, and prerendered 11 static routes. This confirms build output, not browser Core Web Vitals.
- `npm run lint` and `npm run typecheck`: PASS.
- No Lighthouse run or live browser CWV sample completed in this audit; LCP, INP, and CLS are **NOT TESTED**.
- No new API or model benchmark was run against the existing local servers. Avoid interpreting their state as production capacity.

## Historical measured baseline

The repository's Phase 4 Locust report records a 4-vCPU Linux host, 75-second runs, mixed 5/8/12-second phone-like clips, direct Uvicorn, without Postgres/Redis:

| Concurrent users | Requests/s | p50 | p95 | p99 |
|---:|---:|---:|---:|---:|
| 1 | 1.18 | 0.87 s | 1.1 s | 1.2 s |
| 2 | 1.80 | 1.1 s | 1.6 s | 1.8 s |
| 4 | 1.77 | 2.3 s | 2.8 s | 2.9 s |

These are historical project measurements, not a repeatable production SLA. The 2.5 s p95 goal was exceeded at four users. Docker-stack capacity was not measured.

The earlier Phase 2 offline benchmark reports 2.17 s end-to-end p95 on 1,232 clips on 4 vCPU; this is model/evaluation data, not current web latency.

## Current architecture implications

- Frontend route output is static; audio capture and API interaction are client-side.
- ASR and speaker models are warmed at startup, inference runs on a bounded worker pool, and concurrent work is capped. Requests can receive 503 when the queue wait expires.
- A 4-vCPU deployment should begin with the measured two concurrent identify slots and be load-tested with the actual production artifact set before raising limits.

## Required before launch

Run Lighthouse on deployed HTTPS desktop/mobile and report LCP/INP/CLS with device/network profiles. Re-run model warm/cold inference and Locust against an isolated production-like stack with representative clips; record CPU, RSS, p50/p95/p99, throughput, and failures.
