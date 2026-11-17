# Ansit web app

The browser client: tap, let it listen to 5–10 seconds of recitation, and see
the surah, the ayah and the reciter. Arabic-first and right-to-left, dark by
default with a light theme, installable as a PWA.

Built with Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4,
`next-intl` for the Arabic copy and IndexedDB (`idb`) for the local history.

## Run it

You need Node.js 22 or newer and the Ansit API running (see the root README).

```bash
npm install
```

```bash
npm run dev
```

Open <http://localhost:3000>. The app talks to the API at
`http://localhost:8000` unless you say otherwise. If the API runs on another
port, copy `.env.example` to `.env.local` and change `NEXT_PUBLIC_API_URL`,
for example `NEXT_PUBLIC_API_URL=http://localhost:8765`.

The API must allow the web app's address: start it with
`CORS_ORIGINS=http://localhost:3000`.

Browsers only allow the microphone on `https://` pages and on `localhost`. To
try it from a phone on the same network you need HTTPS in front of both the
web app and the API.

## Checks

| Command             | What it does                                           |
| ------------------- | ------------------------------------------------------ |
| `npm run lint`      | ESLint                                                 |
| `npm run typecheck` | TypeScript, no emit                                    |
| `npm test`          | Vitest unit tests for `src/lib`                        |
| `npm run e2e`       | Playwright: main flow with a mocked API and a fake mic |
| `npm run build`     | Production build                                       |
| `npm run icons`     | Re-render the PNG icons from `public/icons/icon.svg`   |

## Layout

| Path               | Contents                                                        |
| ------------------ | --------------------------------------------------------------- |
| `src/app/`         | Routes. Each page is a thin wrapper around a screen component.  |
| `src/components/`  | Screens (`HomeScreen`, `ListenScreen`, …) and shared UI.        |
| `src/lib/`         | API client, recorder, local history, Arabic numerals and dates. |
| `messages/ar.json` | Every piece of interface text.                                  |
| `public/sw.js`     | Service worker: app shell offline. Never touches API requests.  |
| `tests/`           | `unit/` (Vitest) and `e2e/` (Playwright).                       |

Routes use query parameters (`/result?id=…`, `/reciter?id=…`) instead of
dynamic segments, so every page is static and the app can be hosted anywhere.

## Privacy

- The microphone is opened only after the user taps Listen, and is released
  as soon as recording stops or the user leaves the screen.
- The clip lives in memory, is uploaded once, and is then dropped. It is never
  written to browser storage.
- The history holds results only (surah, ayah, reciter, time) and stays in this
  browser's IndexedDB.
- The service worker ignores every non-GET request and every request to
  another origin, so uploads and API answers are never cached.

## Quran text

No Quran text is typed into this code base: ayah text always comes from the
API (Tanzil Uthmani text). Test fixtures use placeholder text. The one
exception is the short motto under the app name on the home screen, which is
copied character for character from the approved design mockup.
