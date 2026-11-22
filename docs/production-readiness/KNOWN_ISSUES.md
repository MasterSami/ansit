# Known issues and follow-up queue

Audit date: 2026-11-22.

## Addressed in this hardening pass

- Redis rate limiting previously failed open. It now falls back to a per-process fixed-window limiter and logs a warning. Cross-instance enforcement still depends on Redis.
- API and Next.js responses now receive basic anti-sniffing, frame, and referrer headers; the web permissions policy keeps microphone access enabled for the same origin.

## Release blockers

1. **Production infrastructure unverified:** no Docker executable, reverse proxy/TLS, secret manager, production network policy, dashboard, or configured alert destination was available.
2. **No current load test or backup restore drill:** historical Locust report is not a current deployment test.
3. **Flutter verification unavailable:** Flutter CLI not installed.
4. **Model-backed CI coverage incomplete locally:** 15 tests skipped because model/evaluation audio or a test PostgreSQL URL was unavailable; CI must provide those artifacts/services.

## Non-blocking or accepted limitations

- Python `transformers` advisories are in the optional ML/offline group and are absent from the runtime image; review before executing converters on untrusted model inputs.
- If Redis is down, local rate limiting is not shared across replicas, and ambiguous follow-up state may be lost.
- GPU image remains untested; no GPU requirement is assumed.
- Metrics and API docs have no in-app authentication; restrict them at ingress if they are operational-only.
- No complete Git-history secret scan has been run.
- Lighthouse/Core Web Vitals were not measured.
