import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../state/providers.dart';
import '../theme/tokens.dart';
import '../widgets/ui.dart';

const appVersion = String.fromEnvironment('APP_VERSION', defaultValue: '0.1.0');

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key, this.showServer = !kReleaseMode});

  /// The server address field is for trying the app against your own server;
  /// it is hidden in release builds.
  final bool showServer;

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  late final _server = TextEditingController(text: ref.read(apiUrlProvider));
  int _clearing = 0; // 0 idle, 1 awaiting confirmation, 2 done
  bool _serverSaved = false;

  @override
  void dispose() {
    _server.dispose();
    super.dispose();
  }

  Future<void> _clear() async {
    if (_clearing != 1) {
      setState(() => _clearing = 1);
      return;
    }
    await ref.read(historyProvider.notifier).clear();
    if (mounted) setState(() => _clearing = 2);
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = context.t;
    final mode = ref.watch(themeModeProvider);
    final modes = [
      (ThemeMode.system, t.settingsSystem),
      (ThemeMode.dark, t.settingsDark),
      (ThemeMode.light, t.settingsLight),
    ];
    final credit = ts(13, color: c.muted, height: 1.8);

    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
          children: [
            Row(
              children: [
                CircleIconButton(
                  icon: Icons.arrow_forward_rounded,
                  label: t.commonBack,
                  onPressed: () =>
                      context.canPop() ? context.pop() : context.go('/'),
                ),
                const SizedBox(width: 12),
                Semantics(
                  header: true,
                  child: Text(
                    t.settingsTitle,
                    style: ts(20, weight: FontWeight.w700),
                  ),
                ),
              ],
            ),
            _Section(
              title: t.settingsAppearance,
              child: Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: c.bg,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  children: [
                    for (final (value, label) in modes)
                      Expanded(
                        child: Semantics(
                          button: true,
                          selected: value == mode,
                          child: Material(
                            color: value == mode
                                ? c.accent
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(12),
                            clipBehavior: Clip.antiAlias,
                            child: InkWell(
                              onTap: () => ref
                                  .read(themeModeProvider.notifier)
                                  .set(value),
                              child: Container(
                                height: 44,
                                alignment: Alignment.center,
                                child: Text(
                                  label,
                                  style: ts(
                                    14,
                                    weight: FontWeight.w600,
                                    color: value == mode ? c.onAccent : c.muted,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            _Section(
              title: t.settingsPrivacy,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  for (final line in [
                    t.settingsPrivacyMic,
                    t.settingsPrivacyClip,
                    t.settingsPrivacyHistory,
                  ])
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 3),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Icon(
                              Icons.check_rounded,
                              size: 16,
                              color: c.accent,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(line, style: ts(14, height: 1.8)),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
            _Section(
              title: t.settingsData,
              child: InkWell(
                onTap: _clearing == 2 ? null : _clear,
                child: ConstrainedBox(
                  constraints: const BoxConstraints(minHeight: 44),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          _clearing == 2
                              ? t.settingsCleared
                              : t.settingsClearHistory,
                          style: ts(
                            15,
                            weight: FontWeight.w600,
                            color: _clearing == 2 ? c.muted : c.warning,
                          ),
                        ),
                      ),
                      if (_clearing == 1)
                        Semantics(
                          liveRegion: true,
                          child: Text(
                            t.settingsClearConfirm,
                            style: ts(12, color: c.warning),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
            if (widget.showServer)
              _Section(
                title: t.settingsServer,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Directionality(
                      textDirection: TextDirection.ltr,
                      child: TextField(
                        controller: _server,
                        keyboardType: TextInputType.url,
                        autocorrect: false,
                        style: ts(14),
                        onChanged: (_) => setState(() => _serverSaved = false),
                        decoration: InputDecoration(
                          labelText: t.settingsServerLabel,
                          labelStyle: ts(13, color: c.muted),
                          hintText: defaultApiUrl,
                          filled: true,
                          fillColor: c.bg,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(14),
                            borderSide: BorderSide(color: c.border),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(t.settingsServerHint, style: ts(12, color: c.muted)),
                    QuietButton(
                      label: _serverSaved
                          ? t.settingsServerSaved
                          : t.settingsServerSave,
                      accent: true,
                      onPressed: () async {
                        await ref
                            .read(apiUrlProvider.notifier)
                            .set(_server.text);
                        if (mounted) setState(() => _serverSaved = true);
                      },
                    ),
                  ],
                ),
              ),
            _Section(
              title: t.settingsAbout,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${t.settingsCreditTanzil} tanzil.net', style: credit),
                  const SizedBox(height: 8),
                  Text(t.settingsCreditWespeaker, style: credit),
                  const SizedBox(height: 8),
                  Text(t.settingsCreditAsr, style: credit),
                  const SizedBox(height: 8),
                  Text('${t.settingsCreditAudio} everyayah.com', style: credit),
                  const SizedBox(height: 8),
                  Text(
                    t.settingsVersion(appVersion),
                    style: ts(12, color: c.muted),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Semantics(
            header: true,
            child: Text(
              title,
              style: ts(
                13,
                weight: FontWeight.w600,
                color: context.colors.muted,
              ),
            ),
          ),
          const SizedBox(height: 10),
          CardBox(radius: 20, padding: const EdgeInsets.all(16), child: child),
        ],
      ),
    );
  }
}
