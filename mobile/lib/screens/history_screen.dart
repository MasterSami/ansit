import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

import '../core/format.dart';
import '../data/history.dart';
import '../state/providers.dart';
import '../theme/tokens.dart';
import '../widgets/ui.dart';

class HistoryScreen extends ConsumerStatefulWidget {
  const HistoryScreen({super.key, this.filter = HistoryFilter.all});

  final HistoryFilter filter;

  @override
  ConsumerState<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends ConsumerState<HistoryScreen> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = context.t;
    final history = ref.watch(historyProvider);
    final now = ref.watch(clockProvider)();
    final filter = widget.filter;
    final saved = filter == HistoryFilter.saved;
    final all = history.value ?? const <HistoryEntry>[];
    final groups = groupByDay(filterEntries(all, filter, _query, now));
    final labels = {
      HistoryFilter.all: t.historyAll,
      HistoryFilter.today: t.historyToday,
      HistoryFilter.week: t.historyWeek,
      HistoryFilter.saved: t.historySaved,
    };

    return Scaffold(
      bottomNavigationBar: BottomNav(
        current: saved ? NavTab.saved : NavTab.history,
      ),
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
              child: Semantics(
                header: true,
                child: Text(
                  saved ? t.historySavedTitle : t.historyTitle,
                  style: ts(28, weight: FontWeight.w700),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: TextField(
                onChanged: (value) => setState(() => _query = value),
                textInputAction: TextInputAction.search,
                style: ts(15),
                decoration: InputDecoration(
                  hintText: t.historySearchPlaceholder,
                  hintStyle: ts(15, color: c.muted),
                  prefixIcon: Icon(
                    Icons.search_rounded,
                    color: c.muted,
                    semanticLabel: t.historySearchLabel,
                  ),
                  filled: true,
                  fillColor: c.surface,
                  contentPadding: const EdgeInsets.symmetric(vertical: 12),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(999),
                    borderSide: BorderSide(color: c.border),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(999),
                    borderSide: BorderSide(color: c.accent, width: 2),
                  ),
                ),
              ),
            ),
            SizedBox(
              height: 76,
              child: Semantics(
                container: true,
                label: t.historyFilters,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
                  children: [
                    for (final value in HistoryFilter.values)
                      Padding(
                        padding: const EdgeInsetsDirectional.only(end: 8),
                        child: ChoiceChipButton(
                          label: labels[value]!,
                          selected: value == filter,
                          onTap: () => context.go(
                            value == HistoryFilter.all
                                ? '/history'
                                : '/history?filter=${value.name}',
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            Expanded(
              child: history.isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : groups.isEmpty
                  ? Center(
                      child: SingleChildScrollView(
                        child: _Empty(
                          hasAny: all.isNotEmpty,
                          saved: saved,
                          searching: _query.trim().isNotEmpty,
                        ),
                      ),
                    )
                  : ListView(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
                      children: [
                        for (final (day, entries) in groups) ...[
                          Padding(
                            padding: const EdgeInsets.only(top: 4, bottom: 8),
                            child: Semantics(
                              header: true,
                              child: Text(
                                dayLabel(day, now),
                                style: ts(
                                  13,
                                  weight: FontWeight.w600,
                                  color: c.muted,
                                ),
                              ),
                            ),
                          ),
                          for (final entry in entries) _Row(entry),
                        ],
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

class _Row extends StatelessWidget {
  const _Row(this.entry);

  final HistoryEntry entry;

  @override
  Widget build(BuildContext context) {
    final c = context.colors;
    final t = context.t;
    final name = entry.reciterName;
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: c.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: BorderSide(color: c.border),
        ),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: () => context.push('/result/${entry.id}'),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            child: Row(
              children: [
                ExcludeSemantics(
                  child: Container(
                    width: 46,
                    height: 46,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: c.accentSoft,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: Text(
                      toArabicDigits(entry.ayah.surah),
                      style: ts(
                        18,
                        weight: FontWeight.w700,
                        color: c.accent,
                        family: fontDisplay,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        t.homeSurahAyah(
                          toArabicDigits(entry.ayah.ayah),
                          entry.ayah.surahNameAr,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: ts(15, weight: FontWeight.w600),
                      ),
                      Text(
                        name ?? t.historyUnknown,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: ts(
                          13,
                          color: name == null ? c.warning : c.muted,
                        ),
                      ),
                    ],
                  ),
                ),
                if (entry.saved)
                  Padding(
                    padding: const EdgeInsetsDirectional.only(end: 6),
                    child: Icon(
                      Icons.bookmark_rounded,
                      size: 16,
                      color: c.accent,
                    ),
                  ),
                Text(clockTime(entry.createdAt), style: ts(12, color: c.muted)),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty({
    required this.hasAny,
    required this.saved,
    required this.searching,
  });

  final bool hasAny;
  final bool saved;
  final bool searching;

  @override
  Widget build(BuildContext context) {
    final t = context.t;
    // Something exists, but the search or the date filter hides it.
    if (hasAny && (searching || !saved)) {
      return StateMessage(
        icon: Icons.search_rounded,
        title: t.historyNoResultsTitle,
        body: t.historyNoResultsBody,
      );
    }
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        StateMessage(
          icon: saved ? Icons.bookmark_border_rounded : Icons.history_rounded,
          title: saved ? t.historyEmptySavedTitle : t.historyEmptyTitle,
          body: saved ? t.historyEmptySavedBody : t.historyEmptyBody,
        ),
        if (!saved)
          SizedBox(
            width: 260,
            child: PrimaryButton(
              label: t.historyStartListening,
              onPressed: () => context.push('/listen'),
            ),
          ),
      ],
    );
  }
}
