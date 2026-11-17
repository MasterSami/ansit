import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../api/api_client.dart';
import '../core/format.dart';
import '../state/providers.dart';
import '../theme/tokens.dart';
import '../widgets/ui.dart';

const _styleOrder = ['murattal', 'mujawwad', 'muallim'];

class ReciterScreen extends ConsumerStatefulWidget {
  const ReciterScreen({super.key, required this.id, this.fromSurah});

  final String id;

  /// The surah the user came from; listed first.
  final int? fromSurah;

  @override
  ConsumerState<ReciterScreen> createState() => _ReciterScreenState();
}

class _ReciterScreenState extends ConsumerState<ReciterScreen> {
  String? _style;

  void _back() => context.canPop() ? context.pop() : context.go('/');

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = context.t;
    final reciter = ref.watch(reciterProvider(widget.id));

    if (reciter.hasError) {
      final error = reciter.error;
      final missing = error is ApiException && error.status == 404;
      return Scaffold(
        body: SafeArea(
          child: Column(
            children: [
              Expanded(
                child: Center(
                  child: StateMessage(
                    icon: Icons.error_outline_rounded,
                    title: missing
                        ? t.reciterNotFoundTitle
                        : t.reciterLoadFailedTitle,
                    body: missing ? t.statesNotFoundBody : t.statesOfflineBody,
                    warning: true,
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
                child: QuietButton(label: t.commonBack, onPressed: _back),
              ),
            ],
          ),
        ),
      );
    }
    final detail = reciter.value;
    if (detail == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final styles = _styleOrder.where(detail.styles.contains).toList();
    final style = _style ?? styles.firstOrNull;
    final template = detail.audioTemplates[style];
    final favourite = ref.watch(favouritesProvider).contains(detail.id);
    final now = ref.watch(clockProvider)();
    final heardToday = {
      for (final e in ref.watch(historyProvider).value ?? const [])
        if (daysAgo(e.createdAt, now) == 0 && e.reciterId == detail.id)
          e.ayah.surah,
    };
    final surahs = [...?ref.watch(surahsProvider).value]
      ..sort((a, b) {
        final first =
            (b.number == widget.fromSurah ? 1 : 0) -
            (a.number == widget.fromSurah ? 1 : 0);
        return first != 0 ? first : a.number - b.number;
      });

    void play(int surah, {required bool stopAtSurahEnd}) {
      if (template == null) return;
      ref
          .read(playerProvider.notifier)
          .play(
            NowPlaying(
              reciterId: detail.id,
              reciterName: detail.nameAr,
              template: template,
              surah: surah,
              ayah: 1,
              stopAtSurahEnd: stopAtSurahEnd,
            ),
          );
    }

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  CircleIconButton(
                    icon: Icons.arrow_forward_rounded,
                    label: t.commonBack,
                    onPressed: _back,
                  ),
                  CircleIconButton(
                    icon: favourite
                        ? Icons.favorite_rounded
                        : Icons.favorite_border_rounded,
                    label: favourite
                        ? t.reciterUnfavourite
                        : t.reciterFavourite,
                    selected: favourite,
                    color: favourite ? c.accent : null,
                    onPressed: () =>
                        ref.read(favouritesProvider.notifier).toggle(detail.id),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
            Avatar(name: detail.nameAr, size: 96),
            const SizedBox(height: 10),
            Semantics(
              header: true,
              child: Text(
                detail.nameAr,
                textAlign: TextAlign.center,
                style: ts(
                  28,
                  weight: FontWeight.w700,
                  family: fontDisplay,
                  height: 1.3,
                ),
              ),
            ),
            if (detail.country != null)
              Text(detail.country!, style: ts(14, color: c.muted)),
            if (styles.length > 1)
              Semantics(
                container: true,
                label: t.reciterStyles,
                child: Container(
                  margin: const EdgeInsets.fromLTRB(20, 16, 20, 0),
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: c.surface,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: c.border),
                  ),
                  child: Row(
                    children: [
                      for (final s in styles)
                        Expanded(
                          child: Semantics(
                            button: true,
                            selected: s == style,
                            child: Material(
                              color: s == style ? c.accent : Colors.transparent,
                              borderRadius: BorderRadius.circular(12),
                              clipBehavior: Clip.antiAlias,
                              child: InkWell(
                                onTap: () => setState(() => _style = s),
                                child: Container(
                                  height: 44,
                                  alignment: Alignment.center,
                                  child: Text(
                                    styleTab[s] ?? s,
                                    style: ts(
                                      14,
                                      weight: FontWeight.w600,
                                      color: s == style ? c.onAccent : c.muted,
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
            if (template == null)
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
                child: Semantics(
                  liveRegion: true,
                  child: Text(
                    t.playerNoAyahAudio,
                    textAlign: TextAlign.center,
                    style: ts(13, color: c.muted),
                  ),
                ),
              ),
            Expanded(
              child: surahs.isEmpty
                  ? const Center(child: CircularProgressIndicator())
                  : ListView.builder(
                      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
                      itemCount: surahs.length,
                      itemBuilder: (context, i) {
                        final surah = surahs[i];
                        final heard = heardToday.contains(surah.number);
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: CardBox(
                            radius: 16,
                            borderColor: heard ? c.accent : null,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 8,
                            ),
                            child: Row(
                              children: [
                                Container(
                                  width: 38,
                                  height: 38,
                                  alignment: Alignment.center,
                                  decoration: BoxDecoration(
                                    color: c.surface2,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    toArabicDigits(surah.number),
                                    style: ts(
                                      14,
                                      weight: FontWeight.w600,
                                      color: c.muted,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        surah.nameAr,
                                        style: ts(15, weight: FontWeight.w600),
                                      ),
                                      Text(
                                        heard
                                            ? '${ayahCount(surah.ayahCount)} · ${t.reciterHeardToday}'
                                            : ayahCount(surah.ayahCount),
                                        style: ts(
                                          12,
                                          color: heard ? c.accent : c.muted,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                CircleIconButton(
                                  icon: Icons.play_arrow_rounded,
                                  label: t.reciterPlaySurah(surah.nameAr),
                                  color: template == null ? c.track : null,
                                  onPressed: template == null
                                      ? null
                                      : () => play(
                                          surah.number,
                                          stopAtSurahEnd: true,
                                        ),
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),
            const PlayerBar(),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 12),
              child: PrimaryButton(
                label: t.reciterPlayAll,
                icon: Icons.play_arrow_rounded,
                onPressed: template == null
                    ? null
                    : () => play(1, stopAtSurahEnd: false),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
