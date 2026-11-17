import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../api/api_client.dart';
import '../core/format.dart';
import '../data/history.dart';
import '../services/platform.dart';
import '../services/recorder.dart';
import '../state/providers.dart';
import '../theme/tokens.dart';
import '../widgets/ui.dart';

enum _Phase {
  checking,
  explain,
  recording,
  identifying,
  micDenied,
  micBlocked,
  micUnavailable,
  noMatch,
  error,
}

/// Explain → record → identify. Leaves to the result screen on success.
class ListenScreen extends ConsumerStatefulWidget {
  const ListenScreen({super.key, this.previousId});

  /// Set when continuing from an ambiguous result ("listen longer").
  final String? previousId;

  @override
  ConsumerState<ListenScreen> createState() => _ListenScreenState();
}

class _ListenScreenState extends ConsumerState<ListenScreen> {
  static const _bars = 8;

  _Phase _phase = _Phase.checking;
  String _reason = 'low_confidence';
  ApiException? _error;
  int _ticks = 0; // tenths of a second recorded so far
  double get _elapsed => _ticks / 10;
  final _levels = List<double>.filled(_bars, 0);

  // Captured once so they can be used after the widget is gone.
  late final ClipRecorder _recorder;
  late final Haptics _haptics;
  StreamSubscription<double>? _levelSub;
  Timer? _ticker;
  CancelToken? _upload;
  bool _finishing = false;

  @override
  void initState() {
    super.initState();
    _recorder = ref.read(recorderProvider);
    _haptics = ref.read(hapticsProvider);
    unawaited(_decide());
  }

  @override
  void dispose() {
    _ticker?.cancel();
    unawaited(_levelSub?.cancel());
    _upload?.cancel();
    // Leaving the screen always releases the microphone and drops the audio.
    unawaited(_recorder.cancel().catchError((_) {}));
    super.dispose();
  }

  Future<void> _decide() async {
    final status = await ref.read(micPermissionProvider).status();
    if (!mounted) return;
    switch (status) {
      case MicStatus.granted:
        await _begin();
      case MicStatus.blocked:
        setState(() => _phase = _Phase.micBlocked);
      case MicStatus.askable:
        // Always explain in our own words before the system dialog appears.
        setState(() => _phase = _Phase.explain);
    }
  }

  Future<void> _allow() async {
    final status = await ref.read(micPermissionProvider).request();
    if (!mounted) return;
    switch (status) {
      case MicStatus.granted:
        await _begin();
      case MicStatus.blocked:
        setState(() => _phase = _Phase.micBlocked);
      case MicStatus.askable:
        setState(() => _phase = _Phase.micDenied);
    }
  }

  Future<void> _begin() async {
    try {
      await _recorder.start();
    } catch (_) {
      if (mounted) setState(() => _phase = _Phase.micUnavailable);
      return;
    }
    if (!mounted) return;
    unawaited(_haptics.start());
    _levelSub = _recorder.levels.listen((level) {
      if (!mounted) return;
      setState(() {
        _levels
          ..removeAt(0)
          ..add(level);
      });
    });
    _ticker = Timer.periodic(const Duration(milliseconds: 100), (_) {
      // Counting ticks keeps the timer exact under test clocks; a late tick
      // on a busy phone only makes the clip a fraction longer than shown.
      if (_ticks + 1 >= maxRecordSeconds * 10) {
        unawaited(_finish());
      } else if (mounted) {
        setState(() => _ticks++);
      }
    });
    setState(() {
      _ticks = 0;
      _finishing = false;
      _phase = _Phase.recording;
    });
  }

  Future<void> _finish() async {
    if (_finishing) return;
    _finishing = true;
    _ticker?.cancel();
    unawaited(_levelSub?.cancel());
    unawaited(_haptics.stop());
    if (mounted) setState(() => _phase = _Phase.identifying);

    try {
      // The clip exists only in this variable; nothing is written to disk.
      final clip = await _recorder.stop();
      final cancel = _upload = CancelToken();
      final response = await ref
          .read(apiProvider)
          .identify(
            clip,
            previousIdentifyId: widget.previousId,
            cancel: cancel,
          );
      if (!mounted) return;
      final entry = HistoryEntry.fromResponse(
        response,
        ref.read(clockProvider)(),
      );
      if (entry == null) {
        setState(() {
          _reason = response.reason ?? 'low_confidence';
          _phase = _Phase.noMatch;
        });
        return;
      }
      await ref.read(historyProvider.notifier).put(entry);
      unawaited(_haptics.result());
      if (mounted) context.pushReplacement('/result/${entry.id}');
    } on ApiException catch (e) {
      if (mounted) {
        setState(() {
          _error = e;
          _phase = _Phase.error;
        });
      }
    } on DioException {
      // Cancelled by the user: they have already left this screen.
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = const ApiException(ApiFailure.server);
          _phase = _Phase.error;
        });
      }
    }
  }

  void _leave() => context.canPop() ? context.pop() : context.go('/');

  @override
  Widget build(BuildContext context) {
    final t = context.t;
    return Scaffold(
      body: SafeArea(
        child: switch (_phase) {
          _Phase.checking => const SizedBox.expand(),
          _Phase.explain => _Explainer(onAllow: _allow, onNotNow: _leave),
          _Phase.recording || _Phase.identifying => _recordingView(context),
          _Phase.micDenied => _Problem(
            icon: Icons.mic_off_outlined,
            title: t.statesDeniedTitle,
            body: t.statesDeniedBody,
            actionLabel: t.commonRetry,
            onAction: _allow,
            onHome: _leave,
          ),
          _Phase.micBlocked => _Problem(
            icon: Icons.mic_off_outlined,
            title: t.statesDeniedTitle,
            body: t.statesDeniedBody,
            actionLabel: t.statesOpenSettings,
            onAction: () => ref.read(micPermissionProvider).openSettings(),
            onHome: _leave,
          ),
          _Phase.micUnavailable => _Problem(
            icon: Icons.mic_off_outlined,
            title: t.statesUnavailableTitle,
            body: t.statesUnavailableBody,
            onHome: _leave,
          ),
          _Phase.noMatch => _Problem(
            icon: Icons.hearing_disabled_outlined,
            title: switch (_reason) {
              'no_speech' => t.statesNoSpeechTitle,
              'too_short' => t.statesTooShortTitle,
              _ => t.statesLowConfidenceTitle,
            },
            body: switch (_reason) {
              'no_speech' => t.statesNoSpeechBody,
              'too_short' => t.statesTooShortBody,
              _ => t.statesLowConfidenceBody,
            },
            actionLabel: t.commonRetry,
            onAction: _begin,
            onHome: _leave,
          ),
          _Phase.error => _errorView(context),
        },
      ),
    );
  }

  Widget _errorView(BuildContext context) {
    final t = context.t;
    final error = _error ?? const ApiException(ApiFailure.server);
    final (icon, title, body) = switch (error.kind) {
      ApiFailure.offline => (
        Icons.wifi_off_rounded,
        t.statesOfflineTitle,
        t.statesOfflineBody,
      ),
      ApiFailure.rateLimited => (
        Icons.hourglass_empty_rounded,
        t.statesRateTitle,
        error.retryAfter == null
            ? t.statesRateBody
            : '${t.statesRateBody}\n${t.statesRateWait(toArabicDigits(error.retryAfter!))}',
      ),
      ApiFailure.busy => (
        Icons.hourglass_empty_rounded,
        t.statesBusyTitle,
        t.statesBusyBody,
      ),
      ApiFailure.badAudio => (
        Icons.error_outline_rounded,
        t.statesBadAudioTitle,
        t.statesBadAudioBody,
      ),
      ApiFailure.server => (
        Icons.error_outline_rounded,
        t.statesServerTitle,
        t.statesServerBody,
      ),
    };
    return _Problem(
      icon: icon,
      title: title,
      body: body,
      actionLabel: t.commonRetry,
      onAction: _begin,
      onHome: _leave,
    );
  }

  Widget _recordingView(BuildContext context) {
    final c = context.colors;
    final t = context.t;
    final identifying = _phase == _Phase.identifying;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                t.appName,
                style: ts(
                  26,
                  weight: FontWeight.w700,
                  color: c.accent,
                  family: fontDisplay,
                ),
              ),
              Semantics(
                label: t.listenElapsed,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: c.surface,
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: c.border),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: c.recording,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Directionality(
                        textDirection: TextDirection.ltr,
                        child: Text(
                          formatElapsed(_elapsed),
                          style: ts(13, weight: FontWeight.w500),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Semantics(
                    label: t.listenWave,
                    child: Container(
                      width: 176,
                      height: 176,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: c.surface,
                        border: Border.all(
                          color: c.accent.withValues(alpha: 0.5),
                        ),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          for (final level in _levels)
                            AnimatedContainer(
                              duration: MediaQuery.of(context).disableAnimations
                                  ? Duration.zero
                                  : const Duration(milliseconds: 90),
                              margin: const EdgeInsets.symmetric(
                                horizontal: 2.5,
                              ),
                              width: 5,
                              height: identifying ? 8 : 8 + 72 * level,
                              decoration: BoxDecoration(
                                color: c.accent,
                                borderRadius: BorderRadius.circular(3),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 32),
                  Semantics(
                    liveRegion: true,
                    child: Text(
                      identifying ? t.listenIdentifying : t.listenListening,
                      style: ts(24, weight: FontWeight.w700),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    identifying
                        ? t.listenIdentifyingHint
                        : widget.previousId != null
                        ? t.listenContinuing
                        : t.listenHint,
                    textAlign: TextAlign.center,
                    style: ts(15, color: c.muted, height: 1.7),
                  ),
                  const SizedBox(height: 28),
                  Semantics(
                    label: t.listenSteps,
                    child: CardBox(
                      radius: 20,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 6,
                      ),
                      child: Column(
                        children: [
                          _Step(
                            label: t.listenStepCapture,
                            state: identifying ? 2 : 1,
                          ),
                          _Step(
                            label: t.listenStepMatch,
                            state: identifying ? 1 : 0,
                          ),
                          _Step(
                            label: t.listenStepReciter,
                            state: identifying ? 1 : 0,
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 0, 24, 20),
          child: identifying
              ? QuietButton(label: t.commonCancel, onPressed: _leave)
              : QuietButton(
                  label: t.listenStop,
                  icon: Icons.stop_rounded,
                  onPressed: _elapsed >= minRecordSeconds ? _finish : null,
                ),
        ),
      ],
    );
  }
}

class _Step extends StatelessWidget {
  const _Step({required this.label, required this.state});

  final String label;

  /// 0 waiting, 1 in progress, 2 done.
  final int state;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = context.t;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(
            switch (state) {
              2 => Icons.check_circle_rounded,
              1 => Icons.radio_button_checked_rounded,
              _ => Icons.radio_button_unchecked_rounded,
            },
            size: 24,
            color: state == 0 ? c.track : c.accent,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: ts(
                14,
                weight: state == 0 ? FontWeight.w400 : FontWeight.w600,
                color: state == 0 ? c.muted : c.text,
              ),
            ),
          ),
          if (state == 2) Text(t.listenDone, style: ts(12, color: c.muted)),
          if (state == 1)
            Text(t.listenInProgress, style: ts(12, color: c.accent)),
        ],
      ),
    );
  }
}

/// Shown before the system permission dialog, never after it.
class _Explainer extends StatelessWidget {
  const _Explainer({required this.onAllow, required this.onNotNow});

  final VoidCallback onAllow;
  final VoidCallback onNotNow;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = context.t;
    final points = [
      (
        Icons.touch_app_outlined,
        t.permissionOnlyWhenTitle,
        t.permissionOnlyWhenBody,
      ),
      (
        Icons.delete_outline_rounded,
        t.permissionDeletedTitle,
        t.permissionDeletedBody,
      ),
      (
        Icons.radio_outlined,
        t.permissionAnySourceTitle,
        t.permissionAnySourceBody,
      ),
    ];
    return Column(
      children: [
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 24, 24, 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: c.accentSoft,
                  ),
                  child: Icon(
                    Icons.mic_none_rounded,
                    size: 34,
                    color: c.accent,
                  ),
                ),
                const SizedBox(height: 24),
                Semantics(
                  header: true,
                  child: Text(
                    t.permissionTitle,
                    style: ts(26, weight: FontWeight.w700, height: 1.4),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  t.permissionSubtitle,
                  style: ts(15, color: c.muted, height: 1.8),
                ),
                const SizedBox(height: 24),
                for (final (icon, title, body) in points)
                  Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: CardBox(
                      radius: 18,
                      padding: const EdgeInsets.all(14),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(icon, size: 22, color: c.accent),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  title,
                                  style: ts(15, weight: FontWeight.w600),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  body,
                                  style: ts(13, color: c.muted, height: 1.6),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
          child: Column(
            children: [
              PrimaryButton(label: t.permissionAllow, onPressed: onAllow),
              const SizedBox(height: 4),
              QuietButton(label: t.permissionNotNow, onPressed: onNotNow),
            ],
          ),
        ),
      ],
    );
  }
}

class _Problem extends StatelessWidget {
  const _Problem({
    required this.icon,
    required this.title,
    required this.body,
    required this.onHome,
    this.actionLabel,
    this.onAction,
  });

  final IconData icon;
  final String title;
  final String body;
  final VoidCallback onHome;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Expanded(
          child: Center(
            child: SingleChildScrollView(
              child: StateMessage(
                icon: icon,
                title: title,
                body: body,
                warning: true,
              ),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
          child: Column(
            children: [
              if (actionLabel != null)
                PrimaryButton(label: actionLabel!, onPressed: onAction),
              const SizedBox(height: 4),
              QuietButton(label: context.t.commonHome, onPressed: onHome),
            ],
          ),
        ),
      ],
    );
  }
}
