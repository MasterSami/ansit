# Phase 6 — Mobile app (Flutter)

## Goal

The same product as the web app, as a Flutter app for Android and iOS.

## Scope

1. **Stack** (from the brief): Flutter stable, Riverpod, go_router, dio,
   `record`, `permission_handler`, `just_audio`, drift.
2. **RTL + Arabic**: `ar` locale, strings in an ARB file generated from the
   web app's `messages/ar.json` so the two apps cannot drift apart.
3. **Theme** from the §8 tokens as a `ThemeExtension`; dark, light, system.
   Fonts bundled (IBM Plex Sans Arabic, Amiri, Amiri Quran; all OFL).
4. **Screens**: home, listen, result, ambiguous result, history / saved,
   reciter, settings, mushaf "soon"; every error and empty state.
5. **Permission flow**: the app's explainer always comes before the system
   dialog; "denied" offers to ask again; "permanently denied" links to the
   app's settings page.
   - Android: `RECORD_AUDIO`, `INTERNET`.
   - iOS: `NSMicrophoneUsageDescription` (Arabic + English).
6. **Haptics** on start, stop and result; animations off under reduce-motion.
7. **Tests**: widget tests for each screen state with every device service
   faked; the record → upload → result flow as a widget test and as an
   `integration_test` for a device.
8. **CI**: `flutter analyze`, `flutter test`, and a debug APK as a download.

## Decisions

- **Raw audio stream → WAV in memory, instead of AAC/Opus files.** The brief
  suggests AAC/M4A or Opus. Those encoders in `record` write to a file. The
  PCM stream never touches storage, which makes "the clip is deleted after
  identification" true by construction. Cost: a 10 s clip is about 320 KB
  instead of about 80 KB; the server limit is 2 MB.
- **Device services behind small interfaces** (recorder, permission, haptics,
  audio output, history store), so every screen state is testable without a
  phone.
- **Server address editable in debug builds only**, to try the app against a
  server on the local network.
- **History rows store the entry as JSON** plus the columns needed to order
  them; no migrations needed for new result fields.

## Acceptance

- `flutter analyze` clean, `flutter test` green, in CI.
- CI produces an installable debug APK.

## Cannot be done from this environment

- Running the app on a phone or emulator (no Android SDK reachable, no macOS).
- Building for iOS.
