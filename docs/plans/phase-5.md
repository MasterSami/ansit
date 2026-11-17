# Phase 5 — Web app (Next.js)

## Goal

A browser client for the Phase 4 API that follows the design mockups in
`docs/design/`: tap, listen, see surah + ayah + reciter.

## Scope

1. **Foundations**: Next.js 16 App Router, TypeScript strict, Tailwind 4 with
   the design tokens (dark default, light, follows the system until the user
   chooses), RTL, IBM Plex Sans Arabic / Amiri / Amiri Quran via `next/font`,
   all copy in `messages/ar.json` (`next-intl`).
2. **Screens**
   - Home: listen button, last result, bottom navigation.
   - Listen: permission explainer (only when the browser would prompt),
     recording with live level bars and timer, identifying steps, cancel.
   - Result: surah, ayah (Uthmani text from the API), text match, reciter with
     similarity or "unknown" with best guesses, continue listening, save,
     share, "wrong result?" feedback.
   - Ambiguous: candidate places with preceding context, "listen 10 s more"
     (`previous_identify_id`), manual confirmation.
   - History and Saved: search, filters, grouped by day.
   - Reciter: styles, surah list, per-surah playback, play all, favourite.
   - Settings: theme, privacy summary, clear history, attributions.
   - Mushaf tab: "coming soon" (not in the v1 scope).
   - States: no speech, too short, low confidence, mic denied / missing,
     offline, server error, busy, rate limited (with countdown), not found.
3. **Local-first history** in IndexedDB. Results only, never audio.
4. **Audio playback** of per-ayah files with automatic advance.
5. **PWA**: manifest, icons, service worker for the app shell.
6. **Accessibility**: labelled controls, 44 px targets, focus rings,
   reduced-motion handling, roles for tabs / radios / status / alerts.
7. **Tests**: Vitest for `src/lib`; Playwright for the main flow with a mocked
   API and Chromium's fake microphone. Both in CI.

## Decisions

- **Query parameters instead of dynamic routes** (`/result?id=`), so all pages
  are static and the result page reads from local history.
- **No audio persistence anywhere**: the clip is a Blob in memory, uploaded
  once and dropped; the service worker never handles POSTs or the API origin.
- **Recording limits**: stop is ignored before 3 s (the server minimum) and
  recording stops by itself at 10 s.
- **Initials avatars**, no reciter photos (brief).

## Acceptance

- `npm run lint`, `npm run typecheck`, `npm test`, `npm run e2e`,
  `npm run build` all pass.
- A real recitation clip fed through the browser microphone against the real
  backend lands on the right result page.
