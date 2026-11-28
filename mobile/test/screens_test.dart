import 'dart:async';

import 'package:ansit/api/api_client.dart';
import 'package:ansit/api/models.dart' show ReciterSummary;
import 'package:ansit/core/format.dart';
import 'package:ansit/services/platform.dart';
import 'package:ansit/state/providers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';

import 'flow.dart';
import 'support.dart';

/// Start listening with the microphone already allowed, then stop at 3 s.
Future<Harness> listenAndStop(
  WidgetTester tester,
  void Function(Harness h) setup, {
  String location = '/listen',
}) async {
  final h = await pumpApp(tester, location: location, setup: setup);
  await tester.pump(const Duration(seconds: 5));
  await tester.tap(find.text(t.listenStop));
  await settle(tester);
  return h;
}

void main() {
  testWidgets('record, upload and see the result', recordUploadResultFlow);

  group('home', () {
    testWidgets('shows a hint when nothing was heard yet', (tester) async {
      await pumpApp(tester);
      expect(find.text(t.appVerse), findsOneWidget);
      expect(find.text(t.homeNothingYet), findsOneWidget);
    });

    testWidgets('shows the latest result and opens it', (tester) async {
      await pumpApp(tester, history: [entryFixture()]);
      expect(find.text(t.homeSurahAyah('١', 'الملك')), findsOneWidget);
      expect(find.textContaining('منذ ١٠ دقائق'), findsOneWidget);
      await tester.tap(find.text(t.homeSurahAyah('١', 'الملك')));
      await settle(tester);
      expect(find.text(t.resultTitle), findsOneWidget);
    });

    testWidgets('is laid out right-to-left', (tester) async {
      await pumpApp(tester);
      final context = tester.element(find.text(t.appVerse));
      expect(Directionality.of(context), TextDirection.rtl);
    });
  });

  group('listen', () {
    testWidgets('records at once when the microphone is allowed', (
      tester,
    ) async {
      final h = await pumpApp(tester, location: '/listen');
      expect(find.text(t.listenListening), findsOneWidget);
      expect(h.mic.requests, 0);
      expect(h.recorder.starts, 1);
    });

    testWidgets('stops by itself after ten seconds', (tester) async {
      final h = await pumpApp(tester, location: '/listen');
      await tester.pump(const Duration(seconds: 11));
      await settle(tester);
      expect(h.recorder.stops, 1);
      expect(h.api.uploads, hasLength(1));
    });

    testWidgets('shows progress while the server works, and can be cancelled', (
      tester,
    ) async {
      final h = await pumpApp(
        tester,
        location: '/listen',
        setup: (h) => h.api.identifyGate = Completer(),
      );
      await tester.pump(const Duration(seconds: 5));
      await tester.tap(find.text(t.listenStop));
      await settle(tester, 2);
      expect(find.text(t.listenIdentifying), findsOneWidget);
      expect(find.text(t.commonCancel), findsOneWidget);
      h.api.identifyGate!.complete();
      await settle(tester);
      expect(find.text(t.resultTitle), findsOneWidget);
    });

    testWidgets('a refusal explains and offers to ask again', (tester) async {
      final h = await pumpApp(
        tester,
        location: '/listen',
        mic: MicStatus.askable,
        afterRequest: MicStatus.askable,
      );
      await tester.tap(find.text(t.permissionAllow));
      await settle(tester);
      expect(find.text(t.statesDeniedTitle), findsOneWidget);
      expect(find.text(t.commonRetry), findsOneWidget);
      expect(h.recorder.starts, 0);
    });

    testWidgets('a permanent refusal links to the app settings', (
      tester,
    ) async {
      final h = await pumpApp(
        tester,
        location: '/listen',
        mic: MicStatus.blocked,
      );
      expect(find.text(t.statesDeniedTitle), findsOneWidget);
      await tester.tap(find.text(t.statesOpenSettings));
      await settle(tester, 2);
      expect(h.mic.settingsOpened, 1);
      expect(h.mic.requests, 0);
    });

    testWidgets('reports a microphone that cannot be opened', (tester) async {
      await pumpApp(
        tester,
        location: '/listen',
        setup: (h) => h.recorder.failToStart = true,
      );
      expect(find.text(t.statesUnavailableTitle), findsOneWidget);
    });

    testWidgets('leaving the screen drops the recording', (tester) async {
      final h = await pumpApp(tester);
      await tester.tap(find.bySemanticsLabel(t.homeTapToListen).first);
      await settle(tester);
      expect(h.recorder.starts, 1);
      await tester.binding.handlePopRoute();
      await settle(tester);
      expect(h.recorder.cancels, greaterThan(0));
      expect(h.api.uploads, isEmpty);
    });

    for (final (reason, title) in [
      ('no_speech', t.statesNoSpeechTitle),
      ('too_short', t.statesTooShortTitle),
      ('low_confidence', t.statesLowConfidenceTitle),
    ]) {
      testWidgets('no match ($reason) explains and offers a retry', (
        tester,
      ) async {
        final h = await listenAndStop(
          tester,
          (h) => h.api.identifyResult = noMatchResponse(reason),
        );
        expect(find.text(title), findsOneWidget);
        expect(await h.store.list(), isEmpty);
        await tester.tap(find.text(t.commonRetry));
        await settle(tester);
        expect(find.text(t.listenListening), findsOneWidget);
        expect(h.recorder.starts, 2);
      });
    }

    for (final (failure, title) in [
      (ApiFailure.offline, t.statesOfflineTitle),
      (ApiFailure.busy, t.statesBusyTitle),
      (ApiFailure.badAudio, t.statesBadAudioTitle),
      (ApiFailure.server, t.statesServerTitle),
    ]) {
      testWidgets('server problem (${failure.name}) is explained', (
        tester,
      ) async {
        await listenAndStop(
          tester,
          (h) => h.api.identifyResult = ApiException(failure),
        );
        expect(find.text(title), findsOneWidget);
      });
    }

    testWidgets('rate limiting says how long to wait', (tester) async {
      await listenAndStop(
        tester,
        (h) => h.api.identifyResult = const ApiException(
          ApiFailure.rateLimited,
          status: 429,
          retryAfter: 42,
        ),
      );
      expect(find.text(t.statesRateTitle), findsOneWidget);
      expect(find.textContaining(t.statesRateWait('٤٢')), findsOneWidget);
    });

    testWidgets('listening longer sends the earlier result id', (tester) async {
      final h = await listenAndStop(
        tester,
        (_) {},
        location: '/listen?prev=id-ambiguous',
      );
      expect(h.api.previousIds, ['id-ambiguous']);
    });
  });

  group('result', () {
    testWidgets('shows surah, ayah, match and reciter', (tester) async {
      await pumpApp(
        tester,
        location: '/result/id-match',
        history: [entryFixture()],
      );
      expect(find.text(t.resultSurah('الملك')), findsOneWidget);
      expect(find.text(t.resultAyahBadge('١')), findsOneWidget);
      expect(find.textContaining(placeholderText), findsOneWidget);
      expect(find.text('٩٦٪'), findsOneWidget);
      expect(find.text('٨٢٪'), findsOneWidget);
      expect(find.text(t.resultTextCredit), findsOneWidget);
    });

    testWidgets('an unknown reciter shows guesses and can be named', (
      tester,
    ) async {
      final h = await pumpApp(
        tester,
        location: '/result/id-match',
        history: [entryFixture(reciter: unknownReciter)],
      );
      expect(find.text(t.resultUnknownReciter), findsOneWidget);
      expect(find.textContaining('أبو بكر الشاطري'), findsOneWidget);
      expect(find.text(t.resultClosestVoiceMatch), findsOneWidget);

      await tester.tap(find.text(t.resultAddName));
      await settle(tester);
      expect(find.text(t.feedbackReciterTitle), findsOneWidget);
      await tester.tap(find.byType(DropdownButtonFormField<ReciterSummary>));
      await settle(tester);
      await tester.tap(find.text('محمود خليل الحصري').last);
      await settle(tester);
      await tester.tap(find.text(t.feedbackSend));
      await settle(tester, 15);

      expect(h.api.feedback.single.kind, 'wrong_reciter');
      expect(h.api.feedback.single.correctReciterId, 'husary');
      expect(find.text('محمود خليل الحصري'), findsOneWidget);
      expect(find.text(t.resultUnknownReciter), findsNothing);
    });

    testWidgets('says so when the server cannot recognise reciters', (
      tester,
    ) async {
      await pumpApp(
        tester,
        location: '/result/id-match',
        history: [entryFixture(reciter: null)],
        setup: (h) => h.api.noReciters = true,
      );
      expect(find.text(t.resultReciterUnavailable), findsOneWidget);
      expect(find.text(t.resultUnknownHint), findsNothing);

      await tester.tap(find.text(t.resultAddName));
      await settle(tester);
      expect(find.text(t.feedbackNoReciters), findsOneWidget);
    });

    testWidgets('saving marks the entry', (tester) async {
      final h = await pumpApp(
        tester,
        location: '/result/id-match',
        history: [entryFixture()],
      );
      await tester.tap(find.text(t.resultSave));
      await settle(tester);
      expect(find.text(t.resultSaved), findsOneWidget);
      expect((await h.store.get('id-match'))!.saved, isTrue);
    });

    testWidgets('reports a wrong ayah', (tester) async {
      final h = await pumpApp(
        tester,
        location: '/result/id-match',
        history: [entryFixture()],
      );
      await tester.tap(find.text(t.resultWrong));
      await settle(tester);
      final fields = find.byType(TextField);
      await tester.enterText(fields.at(0), '2');
      await tester.enterText(fields.at(1), '255');
      await tester.tap(find.text(t.feedbackSend));
      await settle(tester, 2);
      expect(find.text(t.feedbackThanks), findsOneWidget);
      await settle(tester, 12);
      final sent = h.api.feedback.single;
      expect(
        (sent.kind, sent.correctSurah, sent.correctAyah),
        ('wrong_ayah', 2, 255),
      );
    });

    testWidgets('shares the reference and the ayah text', (tester) async {
      final h = await pumpApp(
        tester,
        location: '/result/id-match',
        history: [entryFixture()],
      );
      await tester.tap(find.bySemanticsLabel(t.resultShare));
      await settle(tester, 2);
      expect(h.shared.single, contains(placeholderText));
      expect(h.shared.single, contains('الملك'));
    });

    testWidgets('continues listening from the identified ayah', (tester) async {
      final h = await pumpApp(
        tester,
        location: '/result/id-match',
        history: [entryFixture()],
      );
      await tester.tap(find.text(t.resultContinueListening));
      await settle(tester);
      expect(h.sink.urls, ['https://audio.test/murattal/067001.mp3']);
      expect(find.text(t.playerNowPlaying('١', 'الملك')), findsOneWidget);

      // The next ayah follows by itself.
      h.sink.finishTrack();
      await settle(tester);
      expect(h.sink.urls.last, 'https://audio.test/murattal/067002.mp3');
    });

    testWidgets('says so when playback cannot start', (tester) async {
      await pumpApp(
        tester,
        location: '/result/id-match',
        history: [entryFixture()],
        setup: (h) => h.sink.fail = true,
      );
      await tester.tap(find.text(t.resultContinueListening));
      await settle(tester);
      expect(find.text(t.playerFailed), findsOneWidget);
    });

    testWidgets('says so when the reciter has no per-ayah audio', (
      tester,
    ) async {
      final h = await pumpApp(
        tester,
        location: '/result/id-match',
        history: [entryFixture()],
        setup: (h) => h.api.noAyahAudio = true,
      );
      await tester.tap(find.text(t.resultContinueListening));
      await settle(tester);
      expect(find.text(t.playerNoAyahAudio), findsOneWidget);
      expect(h.sink.urls, isEmpty);
    });

    testWidgets('an unknown id explains and links to the history', (
      tester,
    ) async {
      await pumpApp(tester, location: '/result/nope');
      expect(find.text(t.statesNotFoundTitle), findsOneWidget);
      expect(find.text(t.statesOpenHistory), findsOneWidget);
    });

    testWidgets('a repeated ayah lets the user choose its place', (
      tester,
    ) async {
      final h = await listenAndStop(
        tester,
        (h) => h.api.identifyResult = ambiguousResponse(),
      );
      expect(find.text(t.ambiguousTitle), findsOneWidget);
      expect(find.text(repeatedTimes(31)), findsOneWidget);
      expect(find.text(t.ambiguousMore(otherPlaces(29))), findsOneWidget);
      expect(find.text(t.ambiguousListenMore), findsOneWidget);

      await tester.tap(find.text(t.ambiguousAyah('١٦')));
      await settle(tester, 2);
      await tester.tap(find.text(t.ambiguousConfirm));
      await settle(tester);

      expect(find.text(t.resultAyahBadge('١٦')), findsOneWidget);
      final stored = (await h.store.get('id-ambiguous'))!;
      expect((stored.ambiguous, stored.ayah.ayah), (false, 16));
    });
  });

  group('history', () {
    testWidgets('empty history invites the user to listen', (tester) async {
      await pumpApp(tester, location: '/history');
      expect(find.text(t.historyEmptyTitle), findsOneWidget);
      expect(find.text(t.historyStartListening), findsOneWidget);
    });

    testWidgets('lists entries by day, filters and searches', (tester) async {
      await pumpApp(
        tester,
        location: '/history',
        history: [
          entryFixture(id: 'a'),
          entryFixture(
            id: 'b',
            at: fixedNow.subtract(const Duration(days: 1)),
            saved: true,
            reciter: unknownReciter,
          ),
        ],
      );
      expect(find.text('اليوم'), findsWidgets);
      expect(find.text('أمس'), findsOneWidget);
      expect(find.text(t.homeSurahAyah('١', 'الملك')), findsNWidgets(2));
      expect(find.text(t.historyUnknown), findsOneWidget);

      // The chip row scrolls sideways; bring the last chip into view first.
      await tester.ensureVisible(find.text(t.historySaved));
      await settle(tester, 2);
      await tester.tap(find.text(t.historySaved));
      await settle(tester);
      expect(find.text(t.historySavedTitle), findsNWidgets(2)); // title + tab
      expect(find.text(t.homeSurahAyah('١', 'الملك')), findsOneWidget);

      await tester.enterText(find.byType(TextField), 'البقرة');
      await settle(tester, 2);
      expect(find.text(t.historyNoResultsTitle), findsOneWidget);
    });

    testWidgets('nothing saved yet has its own message', (tester) async {
      await pumpApp(tester, location: '/history?filter=saved');
      expect(find.text(t.historyEmptySavedTitle), findsOneWidget);
    });
  });

  group('reciter', () {
    testWidgets('lists surahs, marks today, and plays one', (tester) async {
      final h = await pumpApp(
        tester,
        location: '/reciter/alafasy?surah=67',
        history: [entryFixture()],
      );
      expect(find.text('مشاري العفاسي'), findsOneWidget);
      expect(find.textContaining(t.reciterHeardToday), findsOneWidget);
      // The surah the user came from is listed first.
      expect(
        tester.getTopLeft(find.text('الملك')).dy,
        lessThan(tester.getTopLeft(find.text('الفاتحة')).dy),
      );

      await tester.tap(find.text(styleTab['mujawwad']!));
      await settle(tester, 2);
      await tester.tap(find.bySemanticsLabel(t.reciterPlaySurah('الفاتحة')));
      await settle(tester);
      expect(h.sink.urls, ['https://audio.test/mujawwad/001001.mp3']);
    });

    testWidgets('explains when there is nothing to play', (tester) async {
      final h = await pumpApp(
        tester,
        location: '/reciter/luhaidan',
        setup: (h) => h.api.noAyahAudio = true,
      );
      expect(find.text(t.playerNoAyahAudio), findsOneWidget);
      await tester.tap(
        find.bySemanticsLabel(t.reciterPlaySurah('الفاتحة')),
        warnIfMissed: false,
      );
      await settle(tester, 2);
      expect(h.sink.urls, isEmpty);
    });

    testWidgets('remembers a favourite reciter', (tester) async {
      final h = await pumpApp(tester, location: '/reciter/alafasy');
      await tester.tap(find.bySemanticsLabel(t.reciterFavourite));
      await settle(tester, 2);
      expect(find.bySemanticsLabel(t.reciterUnfavourite), findsOneWidget);
      expect(h.prefs.getStringList('ansit.favourites'), ['alafasy']);
    });

    testWidgets('explains when the reciter cannot be loaded', (tester) async {
      await pumpApp(
        tester,
        location: '/reciter/alafasy',
        setup: (h) =>
            h.api.reciterError = const ApiException(ApiFailure.offline),
      );
      expect(find.text(t.reciterLoadFailedTitle), findsOneWidget);
    });

    testWidgets('explains when the reciter does not exist', (tester) async {
      await pumpApp(
        tester,
        location: '/reciter/nobody',
        setup: (h) => h.api.reciterError = const ApiException(
          ApiFailure.server,
          status: 404,
        ),
      );
      expect(find.text(t.reciterNotFoundTitle), findsOneWidget);
    });
  });

  group('settings', () {
    testWidgets('switches theme and remembers it', (tester) async {
      final h = await pumpApp(tester, location: '/settings');
      await tester.tap(find.text(t.settingsLight));
      await settle(tester);
      final context = tester.element(find.text(t.settingsTitle));
      expect(Theme.of(context).brightness, Brightness.light);
      expect(h.prefs.getString('ansit.theme'), 'light');
      expect(
        ProviderScope.containerOf(context).read(themeModeProvider),
        ThemeMode.light,
      );
    });

    testWidgets('clears the history only after a second tap', (tester) async {
      final h = await pumpApp(
        tester,
        location: '/settings',
        history: [entryFixture()],
      );
      await tester.tap(find.text(t.settingsClearHistory));
      await settle(tester, 2);
      expect(find.text(t.settingsClearConfirm), findsOneWidget);
      expect(await h.store.list(), hasLength(1));
      await tester.tap(find.text(t.settingsClearHistory));
      await settle(tester, 2);
      expect(find.text(t.settingsCleared), findsOneWidget);
      expect(await h.store.list(), isEmpty);
    });

    testWidgets('states the privacy promise and the sources', (tester) async {
      await pumpApp(tester, location: '/settings');
      expect(find.text(t.settingsPrivacyClip), findsOneWidget);
      await tester.scrollUntilVisible(
        find.textContaining('tanzil.net'),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      expect(find.textContaining('tanzil.net'), findsOneWidget);
      expect(find.text(t.settingsCreditWespeaker), findsOneWidget);
    });

    testWidgets('saves a server address for testing', (tester) async {
      final h = await pumpApp(tester, location: '/settings');
      await tester.scrollUntilVisible(
        find.text(t.settingsServerSave),
        300,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.enterText(
        find.byType(TextField),
        'http://192.168.1.5:8765/',
      );
      await tester.tap(find.text(t.settingsServerSave));
      await settle(tester, 2);
      expect(h.prefs.getString('ansit.api_url'), 'http://192.168.1.5:8765');
    });
  });

  testWidgets('the mushaf tab says it is coming soon', (tester) async {
    await pumpApp(tester, location: '/mushaf');
    expect(find.textContaining(t.commonSoon), findsOneWidget);
  });
}
