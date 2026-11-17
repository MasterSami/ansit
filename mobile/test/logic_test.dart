import 'dart:typed_data';

import 'package:ansit/api/api_client.dart';
import 'package:ansit/api/models.dart';
import 'package:ansit/core/format.dart';
import 'package:ansit/data/database.dart';
import 'package:ansit/data/history.dart';
import 'package:ansit/services/recorder.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support.dart';

void main() {
  group('format', () {
    test('Eastern Arabic digits, percent and elapsed time', () {
      expect(toArabicDigits(562), '٥٦٢');
      expect(formatPercent(0.96), '٩٦٪');
      expect(formatPercent(1.4), '١٠٠٪');
      expect(formatElapsed(6.4), '٠:٠٦');
      expect(formatElapsed(75), '١:١٥');
    });

    test('counted nouns take the right Arabic form', () {
      expect(ayahCount(1), 'آية واحدة');
      expect(ayahCount(2), 'آيتان');
      expect(ayahCount(7), '٧ آيات');
      expect(ayahCount(30), '٣٠ آية');
      expect(otherPlaces(28), '٢٨ موضعًا آخر');
      expect(repeatedTimes(2), 'تتكرر مرتين');
      expect(repeatedTimes(31), 'تتكرر ٣١ مرة');
    });

    test('times and days', () {
      final now = DateTime(2026, 11, 17, 15);
      expect(
        relativeTime(now.subtract(const Duration(seconds: 10)), now),
        'الآن',
      );
      expect(
        relativeTime(now.subtract(const Duration(hours: 2)), now),
        'منذ ساعتين',
      );
      expect(clockTime(DateTime(2026, 11, 17, 14, 40)), '٢:٤٠ م');
      expect(clockTime(DateTime(2026, 11, 17, 0, 5)), '١٢:٠٥ ص');
      expect(daysAgo(DateTime(2026, 11, 16, 23, 59), now), 1);
      expect(dayLabel(DateTime(2026, 11, 14, 9), now), '١٤ نوفمبر');
    });

    test('initials skip honorifics and the definite article', () {
      expect(initials('محمد صديق المنشاوي'), 'م ص');
      expect(initials('الشيخ عبد الباسط'), 'ع ب');
    });

    test('audio templates are zero-padded', () {
      expect(
        ayahAudioUrl('https://x/{sss}{aaa}.mp3', 2, 255),
        'https://x/002255.mp3',
      );
    });
  });

  group('recorder', () {
    test('wraps PCM in a valid mono 16 kHz WAV header', () {
      final pcm = Uint8List(32000);
      final wav = wavFromPcm(pcm);
      final header = ByteData.sublistView(wav, 0, 44);
      expect(wav.length, 44 + pcm.length);
      expect(String.fromCharCodes(wav.sublist(0, 4)), 'RIFF');
      expect(String.fromCharCodes(wav.sublist(8, 16)), 'WAVEfmt ');
      expect(header.getUint32(4, Endian.little), 36 + pcm.length);
      expect(header.getUint16(22, Endian.little), 1); // channels
      expect(header.getUint32(24, Endian.little), 16000);
      expect(header.getUint16(34, Endian.little), 16); // bits
      expect(header.getUint32(40, Endian.little), pcm.length);
    });

    test('level is 0 for silence and 1 for full scale', () {
      expect(levelFromPcm(Uint8List(640)), 0);
      final loud = ByteData(640);
      for (var i = 0; i < 320; i++) {
        loud.setInt16(i * 2, i.isEven ? 30000 : -30000, Endian.little);
      }
      expect(levelFromPcm(loud.buffer.asUint8List()), 1);
      expect(levelFromPcm(Uint8List(0)), 0);
    });
  });

  group('api', () {
    test('maps HTTP statuses to what the UI shows', () {
      expect(failureForStatus(429), ApiFailure.rateLimited);
      expect(failureForStatus(413), ApiFailure.badAudio);
      expect(failureForStatus(422), ApiFailure.badAudio);
      expect(failureForStatus(503), ApiFailure.busy);
      expect(failureForStatus(500), ApiFailure.server);
    });

    test('parses an identify response', () {
      final r = IdentifyResponse.fromJson({
        'id': 'x',
        'status': 'match',
        'reason': null,
        'ayah': ayahFixture().toJson(),
        'text_confidence': 1,
        'candidates': <Object>[],
        'repeated_count': null,
        'reciter': {
          'status': 'unknown',
          'id': null,
          'name_ar': null,
          'style': null,
          'similarity': null,
          'alternatives': [
            {'id': 'a', 'name_ar': 'ب', 'style': 'murattal', 'similarity': 0.6},
          ],
        },
        'timings_ms': {'total': 900},
      });
      expect(r.ayah!.surah, 67);
      expect(r.textConfidence, 1.0);
      expect(r.reciter!.identified, isFalse);
      expect(r.reciter!.alternatives.single.similarity, 0.6);
    });

    test('feedback leaves out what the user did not give', () {
      expect(const FeedbackReport(identifyId: 'x', kind: 'other').toJson(), {
        'identify_id': 'x',
        'kind': 'other',
      });
    });
  });

  group('history', () {
    test('no_match responses are not kept', () {
      expect(
        HistoryEntry.fromResponse(noMatchResponse('no_speech'), fixedNow),
        isNull,
      );
    });

    test('an entry holds the result only: no audio, no transcript', () {
      expect(entryFixture().toJson().keys.toSet(), {
        'id',
        'created_at',
        'ambiguous',
        'ayah',
        'text_confidence',
        'candidates',
        'repeated_count',
        'reciter',
        'saved',
        'user_reciter_id',
        'user_reciter_name',
      });
    });

    test('filters by day, saved state and search text', () {
      final today = entryFixture(id: 'today');
      final week = entryFixture(
        id: 'week',
        at: fixedNow.subtract(const Duration(days: 3)),
        saved: true,
      );
      final old = entryFixture(
        id: 'old',
        at: fixedNow.subtract(const Duration(days: 20)),
      );
      final all = [today, week, old];
      List<String> ids(HistoryFilter f, [String q = '']) =>
          filterEntries(all, f, q, fixedNow).map((e) => e.id).toList();

      expect(ids(HistoryFilter.all), ['today', 'week', 'old']);
      expect(ids(HistoryFilter.today), ['today']);
      expect(ids(HistoryFilter.week), ['today', 'week']);
      expect(ids(HistoryFilter.saved), ['week']);
      expect(ids(HistoryFilter.all, 'MULK'), hasLength(3));
      expect(ids(HistoryFilter.all, 'العفاسي'), hasLength(3));
      expect(ids(HistoryFilter.all, 'البقرة'), isEmpty);
      expect(groupByDay(all).map((g) => g.$2.length), [1, 1, 1]);
    });

    test('the SQLite store round-trips, orders and clears', () async {
      final db = AppDatabase(NativeDatabase.memory());
      addTearDown(db.close);
      final store = DriftHistoryStore(db);

      await store.put(
        entryFixture(id: 'a', at: fixedNow.subtract(const Duration(hours: 2))),
      );
      await store.put(entryFixture(id: 'b', reciter: unknownReciter));
      expect((await store.list()).map((e) => e.id), ['b', 'a']);

      await store.put((await store.get('a'))!.copyWith(saved: true));
      final a = (await store.get('a'))!;
      expect(a.saved, isTrue);
      expect(a.ayah.textUthmani, placeholderText);
      expect(a.reciterName, 'مشاري العفاسي');
      expect((await store.get('b'))!.reciter!.alternatives, hasLength(1));
      expect(await store.get('missing'), isNull);

      await store.clear();
      expect(await store.list(), isEmpty);
    });
  });
}
