import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import 'data/history.dart';
import 'l10n/app_localizations.dart';
import 'screens/history_screen.dart';
import 'screens/home_screen.dart';
import 'screens/listen_screen.dart';
import 'screens/mushaf_screen.dart';
import 'screens/reciter_screen.dart';
import 'screens/result_screen.dart';
import 'screens/settings_screen.dart';
import 'state/providers.dart';
import 'theme/tokens.dart';

GoRouter buildRouter({String initialLocation = '/'}) => GoRouter(
  initialLocation: initialLocation,
  routes: [
    GoRoute(path: '/', builder: (_, _) => const HomeScreen()),
    GoRoute(
      path: '/listen',
      builder: (_, state) => ListenScreen(
        // A new key per visit, so "listen again" always starts clean.
        key: state.pageKey,
        previousId: state.uri.queryParameters['prev'],
      ),
    ),
    GoRoute(
      path: '/result/:id',
      builder: (_, state) => ResultScreen(id: state.pathParameters['id']!),
    ),
    GoRoute(
      path: '/history',
      builder: (_, state) => HistoryScreen(
        filter:
            HistoryFilter.values
                .asNameMap()[state.uri.queryParameters['filter']] ??
            HistoryFilter.all,
      ),
    ),
    GoRoute(
      path: '/reciter/:id',
      builder: (_, state) => ReciterScreen(
        id: state.pathParameters['id']!,
        fromSurah: int.tryParse(state.uri.queryParameters['surah'] ?? ''),
      ),
    ),
    GoRoute(path: '/settings', builder: (_, _) => const SettingsScreen()),
    GoRoute(path: '/mushaf', builder: (_, _) => const MushafScreen()),
  ],
);

class AnsitApp extends ConsumerStatefulWidget {
  const AnsitApp({super.key, this.initialLocation = '/'});

  final String initialLocation;

  @override
  ConsumerState<AnsitApp> createState() => _AnsitAppState();
}

class _AnsitAppState extends ConsumerState<AnsitApp> {
  late final _router = buildRouter(initialLocation: widget.initialLocation);

  @override
  void dispose() {
    _router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'أنصِت',
      debugShowCheckedModeBanner: false,
      routerConfig: _router,
      // Arabic only for now; the locale also makes the whole app right-to-left.
      locale: const Locale('ar'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: [
        AppLocalizations.delegate,
        // Material, Cupertino and widget strings for Arabic.
        ...GlobalMaterialLocalizations.delegates,
      ],
      theme: buildTheme(Brightness.light),
      darkTheme: buildTheme(Brightness.dark),
      themeMode: ref.watch(themeModeProvider),
    );
  }
}
