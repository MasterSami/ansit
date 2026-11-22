# ANSIT threat model

Audit date: 2026-11-22. STRIDE-style repository review; no external penetration test was performed.

| Asset | Threat path | Existing controls | Residual risk / action |
|---|---|---|---|
| Uploaded recitation | oversized, malformed, or CPU-expensive media | 2 MB default body cap, 15 s decode cap, in-memory PyAV decode, multipart overhead cap, bounded inference slots | Fuzz media decoders and test resource limits in an isolated environment; keep PyAV/FFmpeg patched |
| Quran and speaker models | missing/corrupt files or resource exhaustion | loaded once at startup, readiness states, ONNX thread cap, ASR warm-up | Artifact provenance/checksums and production startup validation need release automation |
| Reciter gallery | wrong or incomplete embeddings | registry/gallery consistency check at startup; DB foreign keys | Validate all production gallery vectors and evaluate identity confusion before releases |
| Abuse capacity | repeated expensive `/v1/identify` requests | IP/device fixed-window rate limit; per-process concurrency cap; queue timeout | Redis outage uses local fallback but limits are no longer global; edge-level limits are still needed |
| Ambiguous follow-up state | forged/guessed prior result IDs | UUID identifiers, short TTL, Redis/memory store holds only word positions | Redis outage may lose cross-worker state; no sensitive audio/transcript is stored |
| Stored operational data | database compromise, backups exposed | schema stores outcomes/timing/embedding vectors, not uploaded audio/transcripts; local Compose ports bind loopback | Encrypt production DB/backups, least-privilege DB roles, define retention and restore access |
| Browser session/device | client-supplied IDs or versions abused | strict input patterns; no account/session authority is granted by these values | Treat IDs only as rate-limit hints, as implemented |
| External tafsir | upstream delay or tampered response | fixed HTTPS host, fixed source key, bounded timeout, coordinate validation, cache | No circuit breaker; upstream outage returns 502; outbound network policy should allow only required destinations |
| Admin/ops endpoints | public scrape of metrics or docs | no administrative mutation API is present | Restrict `/metrics` and `/docs` at ingress when publicly deployed; no authentication layer exists |

## Highest-priority paths

1. Resource exhaustion through repeated or adversarial audio uploads: body/duration/concurrency controls exist; validate at the reverse proxy and with adversarial media tests.
2. Distributed abuse if Redis is unavailable: the former fail-open was fixed to a local bounded limiter. Alert on `rate_limiter_unavailable` and keep the API behind an edge limit.
3. Deployment misconfiguration: weak Compose defaults are for local development only. Production secrets, TLS, restricted metrics, and database/Redis network isolation are not provisioned by this repository.
