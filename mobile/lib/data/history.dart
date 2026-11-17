import '../api/models.dart';
import '../core/format.dart';

/// One identified recitation, kept on this device only. Holds the result,
/// never audio and never a transcript.
class HistoryEntry {
  const HistoryEntry({
    required this.id,
    required this.createdAt,
    required this.ambiguous,
    required this.ayah,
    required this.textConfidence,
    this.candidates = const [],
    this.repeatedCount,
    this.reciter,
    this.saved = false,
    this.userReciterId,
    this.userReciterName,
  });

  /// Null for `no_match` responses: those are not kept.
  static HistoryEntry? fromResponse(IdentifyResponse r, DateTime now) {
    final ayah = r.ayah;
    if (r.status == 'no_match' || ayah == null) return null;
    return HistoryEntry(
      id: r.id,
      createdAt: now,
      ambiguous: r.status == 'ambiguous',
      ayah: ayah,
      textConfidence: r.textConfidence ?? 0,
      candidates: r.candidates,
      repeatedCount: r.repeatedCount,
      reciter: r.reciter,
    );
  }

  factory HistoryEntry.fromJson(Json j) => HistoryEntry(
    id: j['id'] as String,
    createdAt: DateTime.fromMillisecondsSinceEpoch(j['created_at'] as int),
    ambiguous: j['ambiguous'] as bool,
    ayah: Ayah.fromJson(j['ayah'] as Json),
    textConfidence: (j['text_confidence'] as num).toDouble(),
    candidates: [
      for (final c in j['candidates'] as List) Candidate.fromJson(c as Json),
    ],
    repeatedCount: j['repeated_count'] as int?,
    reciter: j['reciter'] == null
        ? null
        : ReciterResult.fromJson(j['reciter'] as Json),
    saved: j['saved'] as bool,
    userReciterId: j['user_reciter_id'] as String?,
    userReciterName: j['user_reciter_name'] as String?,
  );

  final String id;
  final DateTime createdAt;
  final bool ambiguous;
  final Ayah ayah;
  final double textConfidence;
  final List<Candidate> candidates;
  final int? repeatedCount;
  final ReciterResult? reciter;
  final bool saved;

  /// Set when the user corrected or supplied the reciter.
  final String? userReciterId;
  final String? userReciterName;

  /// The reciter name to show, or null when unknown.
  String? get reciterName =>
      userReciterName ?? (reciter?.identified == true ? reciter!.nameAr : null);

  /// The reciter id to link to, or null when unknown.
  String? get reciterId =>
      userReciterId ?? (reciter?.identified == true ? reciter!.id : null);

  HistoryEntry copyWith({
    bool? ambiguous,
    Ayah? ayah,
    double? textConfidence,
    bool? saved,
    String? userReciterId,
    String? userReciterName,
  }) => HistoryEntry(
    id: id,
    createdAt: createdAt,
    ambiguous: ambiguous ?? this.ambiguous,
    ayah: ayah ?? this.ayah,
    textConfidence: textConfidence ?? this.textConfidence,
    candidates: candidates,
    repeatedCount: repeatedCount,
    reciter: reciter,
    saved: saved ?? this.saved,
    userReciterId: userReciterId ?? this.userReciterId,
    userReciterName: userReciterName ?? this.userReciterName,
  );

  Json toJson() => {
    'id': id,
    'created_at': createdAt.millisecondsSinceEpoch,
    'ambiguous': ambiguous,
    'ayah': ayah.toJson(),
    'text_confidence': textConfidence,
    'candidates': [for (final c in candidates) c.toJson()],
    'repeated_count': repeatedCount,
    'reciter': reciter?.toJson(),
    'saved': saved,
    'user_reciter_id': userReciterId,
    'user_reciter_name': userReciterName,
  };
}

/// Where history lives. The app uses drift (SQLite); tests use memory.
abstract class HistoryStore {
  Future<void> put(HistoryEntry entry);
  Future<HistoryEntry?> get(String id);

  /// Newest first.
  Future<List<HistoryEntry>> list();
  Future<void> clear();
}

class MemoryHistoryStore implements HistoryStore {
  final _entries = <String, HistoryEntry>{};

  @override
  Future<void> put(HistoryEntry entry) async => _entries[entry.id] = entry;

  @override
  Future<HistoryEntry?> get(String id) async => _entries[id];

  @override
  Future<List<HistoryEntry>> list() async =>
      _entries.values.toList()
        ..sort((a, b) => b.createdAt.compareTo(a.createdAt));

  @override
  Future<void> clear() async => _entries.clear();
}

enum HistoryFilter { all, today, week, saved }

List<HistoryEntry> filterEntries(
  List<HistoryEntry> entries,
  HistoryFilter filter,
  String query,
  DateTime now,
) {
  final needle = query.trim();
  return entries.where((e) {
    if (filter == HistoryFilter.saved && !e.saved) return false;
    final ago = daysAgo(e.createdAt, now);
    if (filter == HistoryFilter.today && ago != 0) return false;
    if (filter == HistoryFilter.week && ago > 6) return false;
    if (needle.isEmpty) return true;
    final haystack = [
      e.ayah.surahNameAr,
      e.ayah.surahNameEn.toLowerCase(),
      e.reciterName ?? '',
    ].join(' ');
    return haystack.contains(needle) || haystack.contains(needle.toLowerCase());
  }).toList();
}

/// Group newest-first entries by calendar day, keeping the order.
List<(DateTime, List<HistoryEntry>)> groupByDay(List<HistoryEntry> entries) {
  final groups = <(DateTime, List<HistoryEntry>)>[];
  for (final entry in entries) {
    final day = startOfDay(entry.createdAt);
    if (groups.isNotEmpty && groups.last.$1 == day) {
      groups.last.$2.add(entry);
    } else {
      groups.add((day, [entry]));
    }
  }
  return groups;
}
