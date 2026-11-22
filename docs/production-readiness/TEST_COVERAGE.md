# Test and validation report

Audit date: 2026-11-22.

## Results observed

| Check | Result | Evidence / limit |
|---|---|---|
| Backend Ruff lint | PASS | `ruff check ..` |
| Backend Ruff format | PASS | 110 files already formatted |
| Backend mypy | PASS | 76 source files, no issues |
| Backend pytest | PASS | 200 passed, 15 skipped in 27.09 s; all skips are real-model/eval-audio or PostgreSQL integration prerequisites not available locally |
| Web ESLint | PASS | `npm run lint` |
| Web TypeScript | PASS | `npm run typecheck` |
| Web Vitest | PASS | 20 tests passed |
| Web production build | PASS | Next.js build and 11 static routes completed |
| Web Playwright | PASS | Full CI-mode run: 10 passed. Separate browser-security-header check: 1 passed. A prior run exposed a stop-timing race and brittle mic permission wait; both were corrected before the passing run. |
| Flutter format/analyze/tests | BLOCKED | `flutter` executable is not installed in this workstation environment. |
| Docker image/Compose | NOT TESTED | Docker executable is unavailable. |
| Security scans | PASS with caveat | npm full tree 0; Python runtime 0; optional ML group has 6 advisories, see `SECURITY_AUDIT.md`. |
| Load / CWV / live API integration | NOT TESTED | No isolated production-like environment used. |

An earlier first backend attempt produced setup errors because Windows denied pytest's default temp directory; rerunning with a repository-local basetemp completed successfully. Do not count that first run as a code failure.

## Gaps

- Model-backed tests were skipped locally; CI has environment requirements for Quran artifacts and a Postgres service, but this session did not run GitHub Actions.
- No fresh deployment E2E against real models, audio, or database was performed.
- No live-model E2E was performed; Playwright mocks the API and uses a synthetic microphone.
