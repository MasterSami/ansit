import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';
import 'package:share_plus/share_plus.dart';

import '../api/models.dart';
import '../core/format.dart';
import '../data/history.dart';
import '../state/providers.dart';
import '../theme/tokens.dart';
import '../widgets/feedback_sheet.dart';
import '../widgets/ui.dart';

/// Used for "continue listening" when no reciter is known or guessed.
const fallbackReciter = 'alafasy';

/// Shares text through the system sheet. Replaced in tests.
final shareProvider = Provider<Future<void> Function(String text)>(
  (ref) =>
      (text) => SharePlus.instance.share(ShareParams(text: text)),
);

class ResultScreen extends ConsumerWidget {
  const ResultScreen({super.key, required this.id});

  final String id;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final history = ref.watch(historyProvider);
    final t = context.t;
    final entry = history.value?.where((e) => e.id == id).firstOrNull;

    if (entry == null) {
      return Scaffold(
        body: SafeArea(
          child: history.isLoading
              ? const Center(child: CircularProgressIndicator())
              : Column(
                  children: [
                    Expanded(
                      child: Center(
                        child: StateMessage(
                          icon: Icons.error_outline_rounded,
                          title: t.statesNotFoundTitle,
                          body: t.statesNotFoundBody,
                          warning: true,
                        ),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(24, 0, 24, 16),
                      child: Column(
                        children: [
                          PrimaryButton(
                            label: t.statesOpenHistory,
                            onPressed: () => context.go('/history'),
                          ),
                          QuietButton(
                            label: t.commonHome,
                            onPressed: () => context.go('/'),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
        ),
      );
    }
    return entry.ambiguous ? _AmbiguousView(entry) : _MatchView(entry);
  }
}

void _back(BuildContext context) =>
    context.canPop() ? context.pop() : context.go('/');

class _Header extends StatelessWidget {
  const _Header({required this.title, this.trailing});

  final String title;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
      child: Row(
        children: [
          CircleIconButton(
            icon: Icons.arrow_forward_rounded,
            label: context.t.commonBack,
            onPressed: () => _back(context),
          ),
          Expanded(
            child: Text(
              title,
              textAlign: TextAlign.center,
              style: ts(16, weight: FontWeight.w600),
            ),
          ),
          trailing ?? const SizedBox(width: 44),
        ],
      ),
    );
  }
}

/// The ayah exactly as the server sent it, with its number.
class _AyahText extends StatelessWidget {
  const _AyahText({required this.text, this.number});

  final String text;
  final int? number;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 16),
      decoration: BoxDecoration(
        border: Border.symmetric(horizontal: BorderSide(color: c.divider)),
      ),
      child: Text.rich(
        TextSpan(
          text: text,
          children: [
            if (number != null)
              TextSpan(
                text: ' ﴿${toArabicDigits(number!)}﴾',
                style: TextStyle(color: c.accent),
              ),
          ],
        ),
        textAlign: TextAlign.center,
        style: ts(25, family: fontQuran, height: 2.1, color: c.text),
      ),
    );
  }
}

class _MatchView extends ConsumerStatefulWidget {
  const _MatchView(this.entry);

  final HistoryEntry entry;

  @override
  ConsumerState<_MatchView> createState() => _MatchViewState();
}

class _MatchViewState extends ConsumerState<_MatchView> {
  String? _notice;

  HistoryEntry get entry => widget.entry;

  Future<void> _share() async {
    final t = context.t;
    final ayah = entry.ayah;
    final text =
        '${t.resultShareText(toArabicDigits(ayah.ayah), ayah.surahNameAr)}\n'
        '${ayah.textUthmani}';
    try {
      await ref.read(shareProvider)(text);
    } catch (_) {
      // The share sheet was dismissed or is unavailable: nothing to do.
    }
  }

  Future<void> _continueListening() async {
    final failed = context.t.playerFailed;
    final reciterId =
        entry.reciterId ??
        entry.reciter?.alternatives.firstOrNull?.id ??
        fallbackReciter;
    try {
      final detail = await ref.read(reciterProvider(reciterId).future);
      final wanted = entry.userReciterId == null ? entry.reciter?.style : null;
      final template =
          detail.audioTemplates[wanted] ?? detail.audioTemplates.values.first;
      final ok = await ref
          .read(playerProvider.notifier)
          .play(
            NowPlaying(
              reciterId: detail.id,
              reciterName: detail.nameAr,
              template: template,
              surah: entry.ayah.surah,
              ayah: entry.ayah.ayah,
              stopAtSurahEnd: true,
            ),
          );
      if (!ok && mounted) setState(() => _notice = failed);
    } catch (_) {
      if (mounted) setState(() => _notice = failed);
    }
  }

  Future<void> _feedback(String kind) async {
    final picked = await showFeedbackSheet(
      context,
      identifyId: entry.id,
      initialKind: kind,
    );
    if (picked != null) {
      await ref
          .read(historyProvider.notifier)
          .put(
            entry.copyWith(
              userReciterId: picked.id,
              userReciterName: picked.nameAr,
            ),
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = context.t;
    final ayah = entry.ayah;
    final reciter = entry.reciter;
    final name = entry.reciterName;
    final corrected = entry.userReciterId != null;
    final alternatives = corrected
        ? const <ReciterAlternative>[]
        : (reciter?.alternatives ?? const <ReciterAlternative>[]);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _Header(
              title: t.resultTitle,
              trailing: CircleIconButton(
                icon: Icons.ios_share_rounded,
                label: t.resultShare,
                onPressed: _share,
              ),
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 12),
                children: [
                  Semantics(
                    container: true,
                    label: t.resultAyahSection,
                    child: CardBox(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Semantics(
                                      header: true,
                                      child: Text(
                                        t.resultSurah(ayah.surahNameAr),
                                        style: ts(
                                          30,
                                          weight: FontWeight.w700,
                                          color: c.accent,
                                          family: fontDisplay,
                                          height: 1.2,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      t.resultMeta(
                                        ayahCount(ayah.ayahCount),
                                        toArabicDigits(ayah.juz),
                                        toArabicDigits(ayah.page),
                                        revelationLabel[ayah.revelation] ?? '',
                                      ),
                                      style: ts(13, color: c.muted),
                                    ),
                                  ],
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 6,
                                ),
                                decoration: BoxDecoration(
                                  color: c.accentSoft,
                                  borderRadius: BorderRadius.circular(999),
                                ),
                                child: Text(
                                  t.resultAyahBadge(toArabicDigits(ayah.ayah)),
                                  style: ts(
                                    14,
                                    weight: FontWeight.w700,
                                    color: c.accent,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 16),
                          _AyahText(text: ayah.textUthmani, number: ayah.ayah),
                          const SizedBox(height: 16),
                          Row(
                            children: [
                              Text(
                                t.resultTextMatch,
                                style: ts(13, color: c.muted),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: ClipRRect(
                                  borderRadius: BorderRadius.circular(999),
                                  child: LinearProgressIndicator(
                                    value: entry.textConfidence.clamp(0, 1),
                                    minHeight: 6,
                                    backgroundColor: c.divider,
                                    color: c.accent,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Text(
                                formatPercent(entry.textConfidence),
                                style: ts(13, weight: FontWeight.w700),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text(
                            t.resultTextCredit,
                            textAlign: TextAlign.center,
                            style: ts(12, color: c.muted),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Semantics(
                    container: true,
                    label: t.resultReciterSection,
                    child: CardBox(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 16,
                      ),
                      child: Column(
                        children: [
                          if (name != null)
                            Row(
                              children: [
                                Avatar(name: name),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        t.resultReciter,
                                        style: ts(12, color: c.muted),
                                      ),
                                      Text(
                                        name,
                                        style: ts(17, weight: FontWeight.w700),
                                      ),
                                      InkWell(
                                        onTap: () => context.push(
                                          '/reciter/${entry.reciterId}'
                                          '?surah=${ayah.surah}',
                                        ),
                                        child: Padding(
                                          padding: const EdgeInsets.symmetric(
                                            vertical: 4,
                                          ),
                                          child: Text(
                                            [
                                              if (!corrected &&
                                                  reciter?.style != null)
                                                styleRecitation[reciter!.style],
                                              '${t.resultReciterPage} ←',
                                            ].join(' · '),
                                            style: ts(
                                              13,
                                              weight: FontWeight.w600,
                                              color: c.accent,
                                            ),
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                if (!corrected && reciter?.similarity != null)
                                  Column(
                                    children: [
                                      Text(
                                        formatPercent(reciter!.similarity!),
                                        style: ts(
                                          18,
                                          weight: FontWeight.w700,
                                          color: c.accent,
                                        ),
                                      ),
                                      Text(
                                        t.resultVoiceSimilarity,
                                        style: ts(11, color: c.muted),
                                      ),
                                    ],
                                  ),
                              ],
                            )
                          else
                            Row(
                              children: [
                                Container(
                                  width: 52,
                                  height: 52,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: c.warningBg,
                                  ),
                                  child: Icon(
                                    Icons.question_mark_rounded,
                                    size: 22,
                                    color: c.warning,
                                  ),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        t.resultReciter,
                                        style: ts(12, color: c.muted),
                                      ),
                                      Text(
                                        t.resultUnknownReciter,
                                        style: ts(17, weight: FontWeight.w700),
                                      ),
                                      Text(
                                        t.resultUnknownHint,
                                        style: ts(13, color: c.muted),
                                      ),
                                    ],
                                  ),
                                ),
                                TextButton(
                                  onPressed: () => _feedback('wrong_reciter'),
                                  style: TextButton.styleFrom(
                                    foregroundColor: c.warning,
                                    minimumSize: const Size(44, 44),
                                  ),
                                  child: Text(
                                    t.resultAddName,
                                    style: ts(13, weight: FontWeight.w600),
                                  ),
                                ),
                              ],
                            ),
                          if (alternatives.isNotEmpty) ...[
                            Divider(height: 24, color: c.divider),
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  t.resultMayAlsoBe,
                                  style: ts(13, color: c.muted),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      for (final alt in alternatives.take(
                                        name != null ? 1 : 2,
                                      ))
                                        InkWell(
                                          onTap: () => context.push(
                                            '/reciter/${alt.id}'
                                            '?surah=${ayah.surah}',
                                          ),
                                          child: Padding(
                                            padding: const EdgeInsets.symmetric(
                                              vertical: 4,
                                            ),
                                            child: Text(
                                              '${alt.nameAr}  ${formatPercent(alt.similarity)}',
                                              style: ts(13),
                                            ),
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                  if (_notice != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: Semantics(
                        liveRegion: true,
                        child: Text(
                          _notice!,
                          textAlign: TextAlign.center,
                          style: ts(13, color: c.muted),
                        ),
                      ),
                    ),
                ],
              ),
            ),
            const PlayerBar(),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
              child: Column(
                children: [
                  PrimaryButton(
                    label: t.resultContinueListening,
                    icon: Icons.play_arrow_rounded,
                    onPressed: _continueListening,
                  ),
                  const SizedBox(height: 10),
                  Row(
                    children: [
                      Expanded(
                        child: _ActionTile(
                          icon: Icons.menu_book_outlined,
                          label: '${t.resultTafsir} (${t.commonSoon})',
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: _ActionTile(
                          icon: entry.saved
                              ? Icons.bookmark_rounded
                              : Icons.bookmark_border_rounded,
                          label: entry.saved ? t.resultSaved : t.resultSave,
                          active: entry.saved,
                          onTap: () => ref
                              .read(historyProvider.notifier)
                              .put(entry.copyWith(saved: !entry.saved)),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: _ActionTile(
                          icon: Icons.help_outline_rounded,
                          label: t.resultWrong,
                          onTap: () => _feedback('wrong_ayah'),
                        ),
                      ),
                    ],
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

class _ActionTile extends StatelessWidget {
  const _ActionTile({
    required this.icon,
    required this.label,
    this.onTap,
    this.active = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback? onTap;
  final bool active;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final color = onTap == null
        ? c.muted
        : active
        ? c.accent
        : c.text;
    return Semantics(
      button: true,
      enabled: onTap != null,
      selected: active,
      child: Material(
        color: c.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: BorderSide(color: c.border),
        ),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: SizedBox(
            height: 64,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, size: 22, color: color),
                const SizedBox(height: 4),
                Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: ts(12, weight: FontWeight.w500, color: color),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _AmbiguousView extends ConsumerStatefulWidget {
  const _AmbiguousView(this.entry);

  final HistoryEntry entry;

  @override
  ConsumerState<_AmbiguousView> createState() => _AmbiguousViewState();
}

class _AmbiguousViewState extends ConsumerState<_AmbiguousView> {
  int _picked = 0;
  bool _confirming = false;
  bool _failed = false;

  HistoryEntry get entry => widget.entry;

  Future<void> _confirm() async {
    final choice = entry.candidates.elementAtOrNull(_picked);
    if (choice == null) return;
    setState(() {
      _confirming = true;
      _failed = false;
    });
    try {
      final ayah = await ref.read(apiProvider).ayah(choice.surah, choice.ayah);
      await ref
          .read(historyProvider.notifier)
          .put(
            entry.copyWith(
              ambiguous: false,
              ayah: ayah,
              textConfidence: choice.score,
            ),
          );
    } catch (_) {
      if (mounted) {
        setState(() {
          _confirming = false;
          _failed = true;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = context.t;
    final candidates = entry.candidates;
    final total = entry.repeatedCount ?? candidates.length;
    final sameSurah = candidates.every(
      (x) => x.surah == candidates.first.surah,
    );
    final reciterName = entry.reciterName;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            _Header(title: t.ambiguousTitle),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 12),
                children: [
                  Semantics(
                    container: true,
                    label: t.ambiguousHeardSection,
                    child: CardBox(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  sameSurah
                                      ? t.resultSurah(entry.ayah.surahNameAr)
                                      : t.appName,
                                  style: ts(
                                    28,
                                    weight: FontWeight.w700,
                                    color: c.accent,
                                    family: fontDisplay,
                                  ),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 6,
                                ),
                                decoration: BoxDecoration(
                                  color: c.warningBg,
                                  borderRadius: BorderRadius.circular(999),
                                ),
                                child: Text(
                                  repeatedTimes(total),
                                  style: ts(
                                    13,
                                    weight: FontWeight.w600,
                                    color: c.warning,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 14),
                          _AyahText(text: entry.ayah.textUthmani),
                          const SizedBox(height: 14),
                          Text(
                            t.ambiguousExplain,
                            style: ts(14, color: c.muted, height: 1.8),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Semantics(
                    container: true,
                    label: t.ambiguousPlaces,
                    child: Column(
                      children: [
                        for (final (i, candidate) in candidates.indexed)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: Semantics(
                              inMutuallyExclusiveGroup: true,
                              checked: i == _picked,
                              child: Material(
                                color: i == _picked ? c.accentSoft : c.surface,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(16),
                                  side: BorderSide(
                                    color: i == _picked ? c.accent : c.border,
                                  ),
                                ),
                                clipBehavior: Clip.antiAlias,
                                child: InkWell(
                                  onTap: () => setState(() => _picked = i),
                                  child: Padding(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 16,
                                      vertical: 10,
                                    ),
                                    child: Row(
                                      children: [
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                sameSurah
                                                    ? t.ambiguousAyah(
                                                        toArabicDigits(
                                                          candidate.ayah,
                                                        ),
                                                      )
                                                    : t.ambiguousSurahAyah(
                                                        toArabicDigits(
                                                          candidate.ayah,
                                                        ),
                                                        candidate.surahNameAr,
                                                      ),
                                                style: ts(
                                                  15,
                                                  weight: FontWeight.w600,
                                                ),
                                              ),
                                              Text(
                                                candidate.contextBefore != null
                                                    ? t.ambiguousAfter(
                                                        candidate
                                                            .contextBefore!,
                                                      )
                                                    : t.ambiguousFirstOfSurah,
                                                maxLines: 1,
                                                overflow: TextOverflow.ellipsis,
                                                style: ts(12, color: c.muted),
                                              ),
                                            ],
                                          ),
                                        ),
                                        Icon(
                                          i == _picked
                                              ? Icons
                                                    .radio_button_checked_rounded
                                              : Icons
                                                    .radio_button_unchecked_rounded,
                                          color: i == _picked
                                              ? c.accent
                                              : c.track,
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        if (total > candidates.length)
                          Text(
                            t.ambiguousMore(
                              otherPlaces(total - candidates.length),
                            ),
                            style: ts(13, color: c.muted),
                          ),
                      ],
                    ),
                  ),
                  if (reciterName != null) ...[
                    const SizedBox(height: 14),
                    CardBox(
                      radius: 18,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 12,
                      ),
                      child: Row(
                        children: [
                          Avatar(name: reciterName, size: 36),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              reciterName,
                              style: ts(14, weight: FontWeight.w600),
                            ),
                          ),
                          if (entry.reciter?.similarity != null)
                            Text(
                              formatPercent(entry.reciter!.similarity!),
                              style: ts(
                                14,
                                weight: FontWeight.w700,
                                color: c.accent,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
              child: Column(
                children: [
                  if (_failed)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Semantics(
                        liveRegion: true,
                        child: Text(
                          t.ambiguousConfirmFailed,
                          textAlign: TextAlign.center,
                          style: ts(13, color: c.warning),
                        ),
                      ),
                    ),
                  PrimaryButton(
                    label: t.ambiguousListenMore,
                    icon: Icons.refresh_rounded,
                    onPressed: () =>
                        context.pushReplacement('/listen?prev=${entry.id}'),
                  ),
                  QuietButton(
                    label: t.ambiguousConfirm,
                    accent: true,
                    onPressed: _confirming ? null : _confirm,
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
