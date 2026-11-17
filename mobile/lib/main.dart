import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app.dart';
import 'data/database.dart';
import 'state/providers.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  runApp(
    ProviderScope(
      // A failed request is reported to the user, who decides to retry.
      retry: (_, _) => null,
      overrides: [
        prefsProvider.overrideWithValue(prefs),
        historyStoreProvider.overrideWithValue(
          DriftHistoryStore(AppDatabase()),
        ),
      ],
      child: const AnsitApp(),
    ),
  );
}
