import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

import '../api/models.dart';
import 'history.dart';

part 'database.g.dart';

/// One row per identified recitation. `payload` is the entry as JSON; the
/// other columns exist for ordering.
class HistoryRows extends Table {
  TextColumn get id => text()();
  IntColumn get createdAt => integer()();
  TextColumn get payload => text()();

  @override
  Set<Column<Object>> get primaryKey => {id};
}

@DriftDatabase(tables: [HistoryRows])
class AppDatabase extends _$AppDatabase {
  AppDatabase([QueryExecutor? executor])
    : super(executor ?? driftDatabase(name: 'ansit'));

  @override
  int get schemaVersion => 1;
}

class DriftHistoryStore implements HistoryStore {
  DriftHistoryStore(this._db);

  final AppDatabase _db;

  HistoryEntry _decode(HistoryRow row) =>
      HistoryEntry.fromJson(jsonDecode(row.payload) as Json);

  @override
  Future<void> put(HistoryEntry entry) => _db
      .into(_db.historyRows)
      .insertOnConflictUpdate(
        HistoryRowsCompanion.insert(
          id: entry.id,
          createdAt: entry.createdAt.millisecondsSinceEpoch,
          payload: jsonEncode(entry.toJson()),
        ),
      );

  @override
  Future<HistoryEntry?> get(String id) async {
    final row = await (_db.select(
      _db.historyRows,
    )..where((t) => t.id.equals(id))).getSingleOrNull();
    return row == null ? null : _decode(row);
  }

  @override
  Future<List<HistoryEntry>> list() async {
    final rows = await (_db.select(
      _db.historyRows,
    )..orderBy([(t) => OrderingTerm.desc(t.createdAt)])).get();
    return rows.map(_decode).toList();
  }

  @override
  Future<void> clear() => _db.delete(_db.historyRows).go();
}
