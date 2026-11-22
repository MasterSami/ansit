# Security audit

Audit date: 2026-11-22. Source review plus dependency scanners. Not a penetration test or a complete Git-history secret scan.

## Controls found

- No user accounts or administrative mutation endpoints exist; the exposed API surface is recognition, metadata, tafsir, and feedback. Authentication was not invented for this public, anonymous product flow.
- Identify requests are body-size capped before inference, capped again after upload read, decoded in memory, duration-limited, and concurrency-limited. Upload filenames and MIME type are not trusted for decoding.
- Errors use structured client-safe responses; request IDs are validated and returned. Logs record route/status/timing, not audio bytes or transcripts.
- CORS is allow-list driven and does not enable credentials. Proxy IP headers are ignored unless explicitly trusted.
- Added `nosniff`, frame denial, and strict referrer policy to API responses and the web application; the web permissions policy preserves microphone access for the site.
- Redis failure no longer disables rate limits: an in-process fixed-window fallback is used and a warning is logged. This is degraded, not globally coordinated enforcement.
- `.env`, `.env.*` are ignored except `.env.example`; the local environment files are not tracked. Their values were not printed.

## Scanner results

- `npm audit --omit=dev`: 0 findings across 47 production dependencies (542 total dependency nodes including dev/optional/peer groups).
- `npm audit`: 0 known findings across the full npm dependency tree.
- `uv audit --no-dev --no-group ml`: no known vulnerabilities or adverse project statuses in 56 production Python packages.
- Full `uv audit`: six advisories reported for `transformers 4.57.6`, which is only in the offline `ml` dependency group and is excluded from the runtime Docker install. One advisory has no fix version reported. The ML tooling group still needs isolated review before use on untrusted model/artifact inputs.
- No gitleaks/trufflehog/OSV binary was installed. A targeted working-tree search did not identify a committed credential, but all refs/history were not scanned; do not treat this as a clean-history attestation.

## Remaining security work

- Set production CORS origins, strong managed DB credentials, and Redis authentication/TLS according to the hosting network. Compose's `ansit` defaults are development-only.
- Put `/metrics`, interactive docs, and OpenAPI behind an internal network or ingress policy if they are not intended to be public.
- Terminate TLS at a maintained reverse proxy; configure HSTS there only once HTTPS is enforced.
- Add a dedicated secret-history scanner in CI and rotate any credential ever committed.
- Validate dependency alerts continuously; audit output is a point-in-time snapshot.

## Verdict

No known production Python or npm dependency advisories were reported in the scanned runtime groups. Production security is **NOT READY** until ingress, secrets, TLS, backup security, and a complete history scan are verified in the deployment environment.
