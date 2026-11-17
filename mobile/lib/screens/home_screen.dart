import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../core/format.dart';
import '../state/providers.dart';
import '../theme/tokens.dart';
import '../widgets/ui.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final c = context.colors;
    final t = context.t;
    final latest = ref.watch(historyProvider).value?.firstOrNull;
    final now = ref.watch(clockProvider)();

    return Scaffold(
      bottomNavigationBar: const BottomNav(current: NavTab.listen),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 16, 24, 0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          t.appName,
                          style: ts(
                            32,
                            weight: FontWeight.w700,
                            color: c.accent,
                            family: fontDisplay,
                            height: 1.2,
                          ),
                        ),
                        Text(t.appVerse, style: ts(13, color: c.muted)),
                      ],
                    ),
                  ),
                  CircleIconButton(
                    icon: Icons.settings_outlined,
                    label: t.homeSettings,
                    onPressed: () => context.push('/settings'),
                  ),
                ],
              ),
            ),
            Expanded(
              child: Center(
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      _ListenButton(
                        label: t.homeTapToListen,
                        onTap: () => context.push('/listen'),
                      ),
                      const SizedBox(height: 28),
                      Text(
                        t.homeTapToListen,
                        style: ts(24, weight: FontWeight.w700),
                      ),
                      const SizedBox(height: 6),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 48),
                        child: Text(
                          t.homeSubtitle,
                          textAlign: TextAlign.center,
                          style: ts(15, color: c.muted, height: 1.6),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        t.homeLastHeard,
                        style: ts(14, weight: FontWeight.w600, color: c.muted),
                      ),
                      TextButton(
                        onPressed: () => context.go('/history'),
                        style: TextButton.styleFrom(
                          foregroundColor: c.accent,
                          minimumSize: const Size(44, 44),
                        ),
                        child: Text(
                          t.homeShowHistory,
                          style: ts(13, weight: FontWeight.w500),
                        ),
                      ),
                    ],
                  ),
                  if (latest == null)
                    CardBox(
                      radius: 20,
                      padding: const EdgeInsets.all(16),
                      child: Text(
                        t.homeNothingYet,
                        style: ts(14, color: c.muted, height: 1.6),
                      ),
                    )
                  else
                    Material(
                      color: c.surface,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(20),
                        side: BorderSide(color: c.border),
                      ),
                      clipBehavior: Clip.antiAlias,
                      child: InkWell(
                        onTap: () => context.push('/result/${latest.id}'),
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Row(
                            children: [
                              Avatar(name: latest.reciterName ?? '؟', size: 44),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      t.homeSurahAyah(
                                        toArabicDigits(latest.ayah.ayah),
                                        latest.ayah.surahNameAr,
                                      ),
                                      style: ts(15, weight: FontWeight.w600),
                                    ),
                                    Text(
                                      '${latest.reciterName ?? t.resultUnknownReciter} · '
                                      '${relativeTime(latest.createdAt, now)}',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: ts(13, color: c.muted),
                                    ),
                                  ],
                                ),
                              ),
                              Icon(
                                Icons.chevron_left_rounded,
                                color: c.muted,
                                semanticLabel: t.homeOpen,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
            const PlayerBar(),
          ],
        ),
      ),
    );
  }
}

/// The big gold button with slow rings (still when reduce-motion is on).
class _ListenButton extends StatefulWidget {
  const _ListenButton({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  State<_ListenButton> createState() => _ListenButtonState();
}

class _ListenButtonState extends State<_ListenButton>
    with SingleTickerProviderStateMixin {
  late final _controller = AnimationController(
    vsync: this,
    duration: const Duration(seconds: 3),
  );

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (MediaQuery.of(context).disableAnimations) {
      _controller.stop();
    } else if (!_controller.isAnimating) {
      _controller.repeat();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Semantics(
      button: true,
      label: widget.label,
      excludeSemantics: true,
      child: SizedBox(
        width: 260,
        height: 260,
        child: Stack(
          alignment: Alignment.center,
          children: [
            AnimatedBuilder(
              animation: _controller,
              builder: (context, _) => CustomPaint(
                size: const Size.square(260),
                painter: _RingsPainter(_controller.value, c.accent),
              ),
            ),
            Material(
              color: c.accent,
              shape: const CircleBorder(),
              clipBehavior: Clip.antiAlias,
              child: InkWell(
                onTap: widget.onTap,
                child: SizedBox(
                  width: 168,
                  height: 168,
                  child: Icon(
                    Icons.mic_none_rounded,
                    size: 64,
                    color: c.onAccent,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RingsPainter extends CustomPainter {
  _RingsPainter(this.progress, this.color);

  final double progress;
  final Color color;

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    for (var i = 0; i < 2; i++) {
      final phase = (progress + i / 2) % 1;
      paint.color = color.withValues(alpha: 0.35 * (1 - phase));
      canvas.drawCircle(center, 92 + 38 * phase, paint);
    }
  }

  @override
  bool shouldRepaint(_RingsPainter old) =>
      old.progress != progress || old.color != color;
}
