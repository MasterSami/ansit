import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../core/format.dart';
import '../l10n/app_localizations.dart';
import '../state/providers.dart';
import '../theme/tokens.dart';

extension L10n on BuildContext {
  AppLocalizations get t => AppLocalizations.of(this);
}

TextStyle ts(
  double size, {
  FontWeight weight = FontWeight.w400,
  Color? color,
  double? height,
  String? family,
}) => TextStyle(
  fontSize: size,
  fontWeight: weight,
  color: color,
  height: height,
  fontFamily: family,
);

/// Round 44 px icon button with a label for screen readers.
class CircleIconButton extends StatelessWidget {
  const CircleIconButton({
    super.key,
    required this.icon,
    required this.label,
    required this.onPressed,
    this.color,
    this.selected,
  });

  final IconData icon;
  final String label;
  final VoidCallback? onPressed;
  final Color? color;
  final bool? selected;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Semantics(
      // Its own node, so screen readers announce it apart from its row.
      container: true,
      button: true,
      label: label,
      selected: selected,
      excludeSemantics: true,
      child: Material(
        color: c.surface,
        shape: CircleBorder(side: BorderSide(color: c.border)),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onPressed,
          child: SizedBox(
            width: 44,
            height: 44,
            child: Icon(icon, size: 20, color: color ?? c.text),
          ),
        ),
      ),
    );
  }
}

class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return SizedBox(
      width: double.infinity,
      height: 54,
      child: FilledButton(
        onPressed: onPressed,
        style: FilledButton.styleFrom(
          backgroundColor: c.accent,
          foregroundColor: c.onAccent,
          disabledBackgroundColor: c.surface2,
          disabledForegroundColor: c.muted,
          shape: const StadiumBorder(),
          textStyle: ts(16, weight: FontWeight.w700, family: fontSans),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(icon, size: 20),
              const SizedBox(width: 8),
            ],
            Flexible(child: Text(label, overflow: TextOverflow.ellipsis)),
          ],
        ),
      ),
    );
  }
}

class QuietButton extends StatelessWidget {
  const QuietButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.accent = false,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final bool accent;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return SizedBox(
      width: double.infinity,
      height: 48,
      child: TextButton(
        onPressed: onPressed,
        style: TextButton.styleFrom(
          foregroundColor: accent ? c.accent : c.text,
          disabledForegroundColor: c.muted,
          shape: const StadiumBorder(),
          textStyle: ts(15, weight: FontWeight.w600, family: fontSans),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (icon != null) ...[
              Icon(icon, size: 18),
              const SizedBox(width: 8),
            ],
            Text(label),
          ],
        ),
      ),
    );
  }
}

/// Initials in a circle. Reciter photos are deliberately not used.
class Avatar extends StatelessWidget {
  const Avatar({super.key, required this.name, this.size = 52});

  final String name;
  final double size;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return ExcludeSemantics(
      child: Container(
        width: size,
        height: size,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: c.accentSoft,
          border: Border.all(color: c.accent, width: size > 60 ? 2 : 1),
        ),
        child: Text(
          initials(name),
          style: ts(
            size * 0.36,
            weight: FontWeight.w700,
            color: c.accent,
            family: fontDisplay,
          ),
        ),
      ),
    );
  }
}

class CardBox extends StatelessWidget {
  const CardBox({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.radius = 24,
    this.borderColor,
    this.color,
  });

  final Widget child;
  final EdgeInsets padding;
  final double radius;
  final Color? borderColor;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: color ?? c.surface,
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(color: borderColor ?? c.border),
      ),
      child: child,
    );
  }
}

/// Centered icon, title and explanation for empty and error states.
class StateMessage extends StatelessWidget {
  const StateMessage({
    super.key,
    required this.icon,
    required this.title,
    required this.body,
    this.warning = false,
  });

  final IconData icon;
  final String title;
  final String body;
  final bool warning;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Semantics(
      liveRegion: true,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 88,
              height: 88,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: warning ? c.warningBg : c.accentSoft,
              ),
              child: Icon(
                icon,
                size: 38,
                color: warning ? c.warning : c.accent,
              ),
            ),
            const SizedBox(height: 20),
            Semantics(
              header: true,
              child: Text(
                title,
                textAlign: TextAlign.center,
                style: ts(22, weight: FontWeight.w700),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              body,
              textAlign: TextAlign.center,
              style: ts(15, color: c.muted, height: 1.8),
            ),
          ],
        ),
      ),
    );
  }
}

enum NavTab { listen, history, saved, mushaf }

class BottomNav extends StatelessWidget {
  const BottomNav({super.key, required this.current});

  final NavTab current;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = context.t;
    final items = [
      (NavTab.listen, Icons.mic_none_rounded, t.navListen, '/'),
      (NavTab.history, Icons.history_rounded, t.navHistory, '/history'),
      (
        NavTab.saved,
        Icons.bookmark_border_rounded,
        t.navSaved,
        '/history?filter=saved',
      ),
      (NavTab.mushaf, Icons.menu_book_outlined, t.navMushaf, '/mushaf'),
    ];
    return Semantics(
      container: true,
      label: t.navLabel,
      child: Container(
        decoration: BoxDecoration(
          color: c.navBg,
          border: Border(top: BorderSide(color: c.navBorder)),
        ),
        child: SafeArea(
          top: false,
          child: Row(
            children: [
              for (final (tab, icon, label, path) in items)
                Expanded(
                  child: Semantics(
                    button: true,
                    selected: tab == current,
                    child: InkWell(
                      onTap: tab == current ? null : () => context.go(path),
                      child: Padding(
                        padding: const EdgeInsets.only(top: 10, bottom: 8),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              icon,
                              size: 24,
                              color: tab == current ? c.accent : c.muted,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              label,
                              style: ts(
                                12,
                                weight: tab == current
                                    ? FontWeight.w700
                                    : FontWeight.w500,
                                color: tab == current ? c.text : c.muted,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Mini player shown while a recitation is playing.
class PlayerBar extends ConsumerWidget {
  const PlayerBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final playing = ref.watch(playerProvider);
    if (playing == null) return const SizedBox.shrink();
    final c = context.colors;
    final t = context.t;
    final name = ref
        .watch(surahsProvider)
        .value
        ?.where((s) => s.number == playing.surah)
        .firstOrNull
        ?.nameAr;
    final player = ref.read(playerProvider.notifier);
    return Semantics(
      container: true,
      label: t.playerLabel,
      child: Container(
        margin: const EdgeInsets.fromLTRB(12, 0, 12, 8),
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: c.surface2,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: c.border),
        ),
        child: Row(
          children: [
            CircleIconButton(
              icon: playing.paused
                  ? Icons.play_arrow_rounded
                  : Icons.pause_rounded,
              label: playing.paused ? t.playerPlay : t.playerPause,
              color: c.accent,
              onPressed: player.toggle,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    t.playerNowPlaying(
                      toArabicDigits(playing.ayah),
                      name ?? toArabicDigits(playing.surah),
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: ts(14, weight: FontWeight.w600),
                  ),
                  Text(
                    playing.reciterName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: ts(12, color: c.muted),
                  ),
                ],
              ),
            ),
            IconButton(
              onPressed: player.stop,
              tooltip: t.playerStop,
              icon: Icon(Icons.close_rounded, size: 20, color: c.muted),
            ),
          ],
        ),
      ),
    );
  }
}

/// A pill-shaped chip used for filters and choices.
class ChoiceChipButton extends StatelessWidget {
  const ChoiceChipButton({
    super.key,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Semantics(
      button: true,
      selected: selected,
      child: Material(
        color: selected ? c.accent : c.surface,
        shape: StadiumBorder(
          side: BorderSide(color: selected ? c.accent : c.border),
        ),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Container(
            height: 44,
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Text(
              label,
              style: ts(
                13,
                weight: FontWeight.w600,
                color: selected ? c.onAccent : c.text,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
