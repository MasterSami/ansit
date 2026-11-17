import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart' show ThemeMode;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

import '../api/api_client.dart';
import '../api/models.dart';
import '../core/format.dart';
import '../data/history.dart';
import '../services/platform.dart';
import '../services/recorder.dart';

/// Default server address. Override at build time with
/// `--dart-define=API_URL=https://…`. 10.0.2.2 is the host machine as seen
/// from the Android emulator.
const defaultApiUrl = String.fromEnvironment(
  'API_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

// ---- things the app is given at start-up (overridden in main and in tests)

final prefsProvider = Provider<SharedPreferences>(
  (ref) => throw UnimplementedError('prefsProvider must be overridden'),
);

final historyStoreProvider = Provider<HistoryStore>(
  (ref) => throw UnimplementedError('historyStoreProvider must be overridden'),
);

final recorderProvider = Provider<ClipRecorder>((ref) => StreamClipRecorder());
final micPermissionProvider = Provider<MicPermission>(
  (ref) => DeviceMicPermission(),
);
final hapticsProvider = Provider<Haptics>((ref) => const Haptics());
final audioSinkProvider = Provider<AudioSink>((ref) => JustAudioSink());
final clockProvider = Provider<DateTime Function()>((ref) => DateTime.now);

// ---- settings

class ThemeModeNotifier extends Notifier<ThemeMode> {
  static const _key = 'ansit.theme';

  @override
  ThemeMode build() => switch (ref.watch(prefsProvider).getString(_key)) {
    'dark' => ThemeMode.dark,
    'light' => ThemeMode.light,
    _ => ThemeMode.system,
  };

  Future<void> set(ThemeMode mode) async {
    state = mode;
    final prefs = ref.read(prefsProvider);
    if (mode == ThemeMode.system) {
      await prefs.remove(_key);
    } else {
      await prefs.setString(_key, mode.name);
    }
  }
}

final themeModeProvider = NotifierProvider<ThemeModeNotifier, ThemeMode>(
  ThemeModeNotifier.new,
);

class ApiUrlNotifier extends Notifier<String> {
  static const _key = 'ansit.api_url';

  @override
  String build() => ref.watch(prefsProvider).getString(_key) ?? defaultApiUrl;

  Future<void> set(String url) async {
    final clean = url.trim().replaceAll(RegExp(r'/+$'), '');
    final prefs = ref.read(prefsProvider);
    if (clean.isEmpty) {
      await prefs.remove(_key);
      state = defaultApiUrl;
    } else {
      await prefs.setString(_key, clean);
      state = clean;
    }
  }
}

final apiUrlProvider = NotifierProvider<ApiUrlNotifier, String>(
  ApiUrlNotifier.new,
);

class FavouritesNotifier extends Notifier<Set<String>> {
  static const _key = 'ansit.favourites';

  @override
  Set<String> build() =>
      (ref.watch(prefsProvider).getStringList(_key) ?? const []).toSet();

  Future<void> toggle(String reciterId) async {
    final next = {...state};
    if (!next.remove(reciterId)) next.add(reciterId);
    state = next;
    await ref.read(prefsProvider).setStringList(_key, next.toList());
  }
}

final favouritesProvider = NotifierProvider<FavouritesNotifier, Set<String>>(
  FavouritesNotifier.new,
);

// ---- server

/// A random id kept on this device, used by the server only for rate limits.
String deviceIdFrom(SharedPreferences prefs) {
  const key = 'ansit.device';
  final existing = prefs.getString(key);
  if (existing != null) return existing;
  final id = const Uuid().v4();
  unawaited(prefs.setString(key, id));
  return id;
}

final apiProvider = Provider<AnsitApi>(
  (ref) => HttpAnsitApi(
    baseUrl: ref.watch(apiUrlProvider),
    deviceId: deviceIdFrom(ref.watch(prefsProvider)),
  ),
);

final surahsProvider = FutureProvider<List<Surah>>(
  (ref) => ref.watch(apiProvider).surahs(),
);

final recitersProvider = FutureProvider<List<ReciterSummary>>(
  (ref) => ref.watch(apiProvider).reciters(),
);

final reciterProvider = FutureProvider.family<ReciterDetail, String>(
  (ref, id) => ref.watch(apiProvider).reciter(id),
);

// ---- history

class HistoryNotifier extends AsyncNotifier<List<HistoryEntry>> {
  HistoryStore get _store => ref.read(historyStoreProvider);

  @override
  Future<List<HistoryEntry>> build() => ref.watch(historyStoreProvider).list();

  Future<void> put(HistoryEntry entry) async {
    await _store.put(entry);
    state = AsyncData(await _store.list());
  }

  Future<void> clear() async {
    await _store.clear();
    state = const AsyncData([]);
  }
}

final historyProvider =
    AsyncNotifierProvider<HistoryNotifier, List<HistoryEntry>>(
      HistoryNotifier.new,
    );

// ---- recitation player

class NowPlaying {
  const NowPlaying({
    required this.reciterId,
    required this.reciterName,
    required this.template,
    required this.surah,
    required this.ayah,
    required this.stopAtSurahEnd,
    this.paused = false,
  });

  final String reciterId;
  final String reciterName;
  final String template;
  final int surah;
  final int ayah;
  final bool stopAtSurahEnd;
  final bool paused;

  NowPlaying at(int surah, int ayah) => NowPlaying(
    reciterId: reciterId,
    reciterName: reciterName,
    template: template,
    surah: surah,
    ayah: ayah,
    stopAtSurahEnd: stopAtSurahEnd,
  );

  NowPlaying withPaused(bool paused) => NowPlaying(
    reciterId: reciterId,
    reciterName: reciterName,
    template: template,
    surah: surah,
    ayah: ayah,
    stopAtSurahEnd: stopAtSurahEnd,
    paused: paused,
  );
}

/// Plays per-ayah audio files one after another.
class PlayerNotifier extends Notifier<NowPlaying?> {
  AudioSink get _sink => ref.read(audioSinkProvider);

  @override
  NowPlaying? build() {
    final subscription = ref.watch(audioSinkProvider).completed.listen((_) {
      unawaited(_advance());
    });
    ref.onDispose(subscription.cancel);
    return null;
  }

  /// Returns false if the audio could not be started.
  Future<bool> play(NowPlaying track) async {
    state = track;
    try {
      await _sink.playUrl(
        ayahAudioUrl(track.template, track.surah, track.ayah),
      );
      return true;
    } catch (_) {
      state = null;
      return false;
    }
  }

  Future<void> toggle() async {
    final current = state;
    if (current == null) return;
    if (current.paused) {
      await _sink.resume();
    } else {
      await _sink.pause();
    }
    state = current.withPaused(!current.paused);
  }

  Future<void> stop() async {
    state = null;
    await _sink.stop();
  }

  Future<void> _advance() async {
    final current = state;
    if (current == null) return;
    final surahs = ref.read(surahsProvider).value;
    final count = surahs
        ?.where((s) => s.number == current.surah)
        .firstOrNull
        ?.ayahCount;
    if (count == null) return stop();
    if (current.ayah < count) {
      await play(current.at(current.surah, current.ayah + 1));
    } else if (!current.stopAtSurahEnd && current.surah < 114) {
      await play(current.at(current.surah + 1, 1));
    } else {
      await stop();
    }
  }
}

final playerProvider = NotifierProvider<PlayerNotifier, NowPlaying?>(
  PlayerNotifier.new,
);
