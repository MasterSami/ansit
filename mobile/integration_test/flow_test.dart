import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import '../test/flow.dart';

// Runs the record → upload → result flow on a real device or emulator:
//   flutter test integration_test
// The server, microphone and haptics are faked; the app, its navigation and
// its rendering are real.
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('record, upload and see the result', recordUploadResultFlow);
}
