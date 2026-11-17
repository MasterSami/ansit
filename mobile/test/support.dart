import 'dart:async';
import 'dart:typed_data';

import 'package:ansit/api/api_client.dart';
import 'package:ansit/api/models.dart';
import 'package:ansit/app.dart';
import 'package:ansit/data/history.dart';
import 'package:ansit/l10n/app_localizations.dart';
import 'package:ansit/screens/result_screen.dart';
import 'package:ansit/services/platform.dart';
import 'package:ansit/services/recorder.dart';
import 'package:ansit/state/providers.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// The app's Arabic strings, so tests never retype interface text.
final t = lookupAppLocalizations(const Locale('ar'));

// Placeholder only: real ayah text always comes from the server.
const placeholderText = 'نص تجريبي للاختبار';

final fixedNow = DateTime(2026, 11, 17, 15);

Ayah ayahFixture({
  int surah = 67,
  int ayah = 1,
  String nameAr = 'الملك',
  String nameEn = 'Al-Mulk',
}) => Ayah(
  surah: surah,
  surahNameAr: nameAr,
  surahNameEn: nameEn,
  ayah: ayah,
  textUthmani: placeholderText,
  juz: 29,
  page: 562,
  revelation: 'meccan',
  ayahCount: 30,
);

const identifiedReciter = ReciterResult(
  identified: true,
  id: 'alafasy',
  nameAr: 'مشاري العفاسي',
  style: 'murattal',
  similarity: 0.82,
);

const unknownReciter = ReciterResult(
  identified: false,
  alternatives: [
    ReciterAlternative(
      id: 'shatri',
      nameAr: 'أبو بكر الشاطري',
      style: 'murattal',
      similarity: 0.69,
    ),
  ],
);

IdentifyResponse matchResponse({
  String id = 'id-match',
  ReciterResult? reciter = identifiedReciter,
}) => IdentifyResponse(
  id: id,
  status: 'match',
  ayah: ayahFixture(),
  textConfidence: 0.96,
  reciter: reciter,
);

IdentifyResponse ambiguousResponse() => IdentifyResponse(
  id: 'id-ambiguous',
  status: 'ambiguous',
  ayah: ayahFixture(surah: 55, ayah: 13, nameAr: 'الرحمن', nameEn: 'Ar-Rahman'),
  textConfidence: 0.97,
  candidates: const [
    Candidate(
      surah: 55,
      surahNameAr: 'الرحمن',
      ayah: 13,
      score: 0.97,
      contextBefore: placeholderText,
    ),
    Candidate(
      surah: 55,
      surahNameAr: 'الرحمن',
      ayah: 16,
      score: 0.95,
      contextBefore: placeholderText,
    ),
  ],
  repeatedCount: 31,
  reciter: unknownReciter,
);

IdentifyResponse noMatchResponse(String reason) =>
    IdentifyResponse(id: 'id-none', status: 'no_match', reason: reason);

HistoryEntry entryFixture({
  String id = 'id-match',
  DateTime? at,
  bool saved = false,
  ReciterResult? reciter = identifiedReciter,
}) => HistoryEntry.fromResponse(
  matchResponse(id: id, reciter: reciter),
  at ?? fixedNow.subtract(const Duration(minutes: 10)),
)!.copyWith(saved: saved);

class FakeApi implements AnsitApi {
  /// What `identify` returns: an [IdentifyResponse] or an exception to throw.
  Object identifyResult = matchResponse();
  final uploads = <Uint8List>[];
  final previousIds = <String?>[];
  final feedback = <FeedbackReport>[];
  Object? reciterError;
  bool noReciters = false;
  Completer<void>? identifyGate;

  @override
  Future<IdentifyResponse> identify(
    Uint8List wav, {
    String? previousIdentifyId,
    CancelToken? cancel,
  }) async {
    uploads.add(wav);
    previousIds.add(previousIdentifyId);
    await identifyGate?.future;
    final result = identifyResult;
    if (result is IdentifyResponse) return result;
    throw result;
  }

  @override
  Future<List<Surah>> surahs() async => const [
    Surah(number: 1, nameAr: 'الفاتحة', ayahCount: 7),
    Surah(number: 55, nameAr: 'الرحمن', ayahCount: 78),
    Surah(number: 67, nameAr: 'الملك', ayahCount: 30),
  ];

  @override
  Future<Ayah> ayah(int surah, int ayah) async =>
      ayahFixture(surah: surah, ayah: ayah, nameAr: 'الرحمن');

  @override
  Future<List<ReciterSummary>> reciters() async => noReciters
      ? const []
      : const [
          ReciterSummary(id: 'alafasy', nameAr: 'مشاري العفاسي'),
          ReciterSummary(id: 'husary', nameAr: 'محمود خليل الحصري'),
        ];

  @override
  Future<ReciterDetail> reciter(String id) async {
    if (reciterError != null) throw reciterError!;
    return ReciterDetail(
      id: id,
      nameAr: 'مشاري العفاسي',
      styles: const ['murattal', 'mujawwad'],
      audioTemplates: const {
        'murattal': 'https://audio.test/murattal/{sss}{aaa}.mp3',
        'mujawwad': 'https://audio.test/mujawwad/{sss}{aaa}.mp3',
      },
    );
  }

  @override
  Future<void> sendFeedback(FeedbackReport f) async => feedback.add(f);
}

class FakeRecorder implements ClipRecorder {
  bool failToStart = false;
  int starts = 0;
  int stops = 0;
  int cancels = 0;
  final _levels = StreamController<double>.broadcast();

  @override
  Stream<double> get levels => _levels.stream;

  @override
  Future<void> start() async {
    if (failToStart) throw StateError('no microphone');
    starts++;
  }

  @override
  Future<Uint8List> stop() async {
    stops++;
    return wavFromPcm(Uint8List(3200));
  }

  @override
  Future<void> cancel() async => cancels++;
}

class FakeMic implements MicPermission {
  FakeMic(this.current, {MicStatus? afterRequest})
    : afterRequest = afterRequest ?? MicStatus.granted;

  MicStatus current;
  MicStatus afterRequest;
  int requests = 0;
  int settingsOpened = 0;

  @override
  Future<MicStatus> status() async => current;

  @override
  Future<MicStatus> request() async {
    requests++;
    return current = afterRequest;
  }

  @override
  Future<void> openSettings() async => settingsOpened++;
}

class FakeHaptics implements Haptics {
  final events = <String>[];

  @override
  Future<void> start() async => events.add('start');

  @override
  Future<void> stop() async => events.add('stop');

  @override
  Future<void> result() async => events.add('result');
}

class FakeSink implements AudioSink {
  final urls = <String>[];
  bool fail = false;
  int stops = 0;
  final _completed = StreamController<void>.broadcast();

  void finishTrack() => _completed.add(null);

  @override
  Stream<void> get completed => _completed.stream;

  @override
  Future<void> playUrl(String url) async {
    if (fail) throw StateError('cannot play');
    urls.add(url);
  }

  @override
  Future<void> pause() async {}

  @override
  Future<void> resume() async {}

  @override
  Future<void> stop() async => stops++;
}

/// Everything a test can inspect after driving the app.
class Harness {
  final api = FakeApi();
  final recorder = FakeRecorder();
  final haptics = FakeHaptics();
  final sink = FakeSink();
  final store = MemoryHistoryStore();
  final shared = <String>[];
  FakeMic mic = FakeMic(MicStatus.granted);
  late SharedPreferences prefs;
}

/// Pump the whole app on a phone-sized screen with every device service faked.
Future<Harness> pumpApp(
  WidgetTester tester, {
  String location = '/',
  MicStatus mic = MicStatus.granted,
  MicStatus? afterRequest,
  List<HistoryEntry> history = const [],
  void Function(Harness h)? setup,
}) async {
  tester.view.physicalSize = const Size(402, 874);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);

  SharedPreferences.setMockInitialValues({});
  final h = Harness()
    ..mic = FakeMic(mic, afterRequest: afterRequest)
    ..prefs = await SharedPreferences.getInstance();
  for (final entry in history) {
    await h.store.put(entry);
  }
  setup?.call(h);

  await tester.pumpWidget(
    ProviderScope(
      retry: (_, _) => null,
      overrides: [
        prefsProvider.overrideWithValue(h.prefs),
        historyStoreProvider.overrideWithValue(h.store),
        apiProvider.overrideWithValue(h.api),
        recorderProvider.overrideWithValue(h.recorder),
        micPermissionProvider.overrideWithValue(h.mic),
        hapticsProvider.overrideWithValue(h.haptics),
        audioSinkProvider.overrideWithValue(h.sink),
        clockProvider.overrideWithValue(() => fixedNow),
        shareProvider.overrideWithValue((text) async => h.shared.add(text)),
      ],
      child: AnsitApp(initialLocation: location),
    ),
  );
  await settle(tester);
  return h;
}

/// Let pending futures and short animations finish without waiting for the
/// endless ones (the home button's rings, progress spinners).
Future<void> settle(WidgetTester tester, [int frames = 6]) async {
  for (var i = 0; i < frames; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}
