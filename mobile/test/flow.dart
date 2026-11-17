import 'package:ansit/services/platform.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support.dart';

/// Record → upload → result, with the server and the device services faked.
/// Shared by the widget test and the on-device integration test.
Future<void> recordUploadResultFlow(WidgetTester tester) async {
  final h = await pumpApp(tester, mic: MicStatus.askable);

  // Home → our own explainer, before any system dialog.
  await tester.tap(find.bySemanticsLabel(t.homeTapToListen).first);
  await settle(tester);
  expect(find.text(t.permissionTitle), findsOneWidget);
  expect(h.mic.requests, 0);
  expect(h.recorder.starts, 0);

  // Allow → system dialog (faked as granted) → recording starts.
  await tester.tap(find.text(t.permissionAllow));
  await settle(tester);
  expect(h.mic.requests, 1);
  expect(h.recorder.starts, 1);
  expect(find.text(t.listenListening), findsOneWidget);

  // Stop is offered only once the clip is long enough for the server.
  await tester.tap(find.text(t.listenStop));
  await settle(tester, 2);
  expect(h.recorder.stops, 0);

  await tester.pump(const Duration(seconds: 3));
  await tester.tap(find.text(t.listenStop));
  await settle(tester);

  // One WAV clip was uploaded from memory.
  expect(h.recorder.stops, 1);
  expect(h.api.uploads, hasLength(1));
  expect(String.fromCharCodes(h.api.uploads.single.sublist(0, 4)), 'RIFF');

  // The result is shown and kept in the local history.
  expect(find.text(t.resultSurah('الملك')), findsOneWidget);
  expect(find.textContaining(placeholderText), findsOneWidget);
  expect(find.text('مشاري العفاسي'), findsOneWidget);
  expect((await h.store.list()).single.id, 'id-match');
  expect(h.haptics.events, ['start', 'stop', 'result']);
}
