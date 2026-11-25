# Ansit mobile app

The Flutter client for Android and iOS: tap, let it listen to 5–10 seconds of
recitation, and see the surah, the ayah and the reciter. Same screens, text and
colours as the web app; Arabic and right-to-left.

Flutter stable (3.50), Riverpod, go_router, dio, `record`,
`permission_handler`, `just_audio`, drift (SQLite) for the local history.

## Try it on an Android phone, without installing Flutter

Every push builds a debug APK on GitHub:

1. Open the repository's **Actions** tab, pick the latest **CI** run, and
   download the **ansit-debug-apk** artifact at the bottom of the page.
2. Unzip it, copy `app-debug.apk` to the phone and install it.
3. Start the Ansit server on your computer so the phone can reach it:
   `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8765`
   (phone and computer on the same Wi-Fi).
4. In the app: **Settings → Server address**, enter
   `http://<your computer's IP>:8765`, and save.

The server-address field exists only in debug builds.

## Run it from source

```bash
flutter pub get
```

```bash
flutter run --dart-define=API_URL=http://10.0.2.2:8765
```

`10.0.2.2` is the host computer as seen from the Android emulator. For a real
phone use the computer's address on the local network. Debug builds allow
plain `http`; release builds need `https`.

## Checks

| Command                         | What it does                                        |
| ------------------------------- | --------------------------------------------------- |
| `flutter analyze`               | Static analysis                                     |
| `flutter test`                  | Unit and widget tests (every screen state)          |
| `flutter test integration_test` | The record → upload → result flow on a device       |

After changing interface text in `web/messages/ar.json`, regenerate the
strings (from the repository root): `python mobile/tool/gen_arb.py`, then
`flutter gen-l10n`. After changing `lib/data/database.dart`:
`dart run build_runner build`.

## Layout

| Path             | Contents                                                      |
| ---------------- | ------------------------------------------------------------- |
| `lib/app.dart`   | Routes, theme, locale.                                        |
| `lib/screens/`   | Home, listen, result (and ambiguous), history, reciter, settings. |
| `lib/widgets/`   | Shared UI, bottom navigation, mini player, feedback sheet.    |
| `lib/state/`     | Riverpod providers: settings, history, player.                |
| `lib/services/`  | Recorder, microphone permission, haptics, audio output.       |
| `lib/api/`       | Server client and models.                                     |
| `lib/data/`      | History model and its SQLite store.                           |
| `lib/l10n/`      | Arabic strings (generated from the web app's copy).           |
| `test/`          | Fakes for every device service, and the tests.                |

## Privacy

- The microphone opens only on the Listen screen, after the app's own
  explanation and then the system's permission dialog. Leaving the screen
  releases it.
- **No audio file is ever created on the phone.** The recorder delivers raw
  audio to memory; it is wrapped as a WAV in memory, uploaded once, and
  dropped.
- The history holds results only and stays in the app's own database on the
  device.

## Known gaps

See `docs/PROGRESS.md` (Phase 6). In short: the app has not been run on a real
phone or emulator from this environment, and iOS needs one extra build setting
for the microphone permission that can only be added on a Mac.
