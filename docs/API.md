# API

Interactive docs: `http://localhost:8000/docs` (OpenAPI at `/openapi.json`).

Every response carries an `X-Request-ID` header. A client may send its own
(`[A-Za-z0-9._-]`, up to 64 characters); anything else is replaced by a UUID.

## Ops endpoints (Phase 0)

| Method | Path       | Purpose                                                                                                              |
| ------ | ---------- | -------------------------------------------------------------------------------------------------------------------- |
| GET    | `/healthz` | Liveness. Always `200 {"status": "ok"}` while the process serves.                                                    |
| GET    | `/readyz`  | Readiness. `200` once startup tasks (model loading) have finished and the configured stores answer; otherwise `503`. |
| GET    | `/metrics` | Prometheus text format.                                                                                              |

### `/readyz` body

```json
{
  "status": "ready",
  "components": { "asr_model": "ready" },
  "dependencies": { "database": true, "redis": true }
}
```

- `status`: `ready` or `not_ready`.
- `components`: one entry per startup task — `pending`, `ready` or `failed`.
  Empty until Phase 2 registers the first model loader.
- `dependencies`: one entry per configured store (`DATABASE_URL`, `REDIS_URL`).
  A store that is not configured is omitted.

### Metrics

| Name                                  | Type      | Labels                                 |
| ------------------------------------- | --------- | -------------------------------------- |
| `ansit_http_requests_total`           | counter   | `method`, `route` (template), `status` |
| `ansit_http_request_duration_seconds` | histogram | `method`, `route`                      |
| `ansit_ready`                         | gauge     | —                                      |

## `/v1` endpoints

Not implemented yet. `/v1/identify` and the metadata, reciter and feedback
endpoints arrive in Phase 4.
