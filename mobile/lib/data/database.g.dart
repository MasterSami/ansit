// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'database.dart';

// ignore_for_file: type=lint
class $HistoryRowsTable extends HistoryRows
    with TableInfo<$HistoryRowsTable, HistoryRow> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $HistoryRowsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<int> createdAt = GeneratedColumn<int>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _payloadMeta = const VerificationMeta(
    'payload',
  );
  @override
  late final GeneratedColumn<String> payload = GeneratedColumn<String>(
    'payload',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [id, createdAt, payload];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'history_rows';
  @override
  VerificationContext validateIntegrity(
    Insertable<HistoryRow> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('payload')) {
      context.handle(
        _payloadMeta,
        payload.isAcceptableOrUnknown(data['payload']!, _payloadMeta),
      );
    } else if (isInserting) {
      context.missing(_payloadMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  HistoryRow map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return HistoryRow(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}created_at'],
      )!,
      payload: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}payload'],
      )!,
    );
  }

  @override
  $HistoryRowsTable createAlias(String alias) {
    return $HistoryRowsTable(attachedDatabase, alias);
  }
}

class HistoryRow extends DataClass implements Insertable<HistoryRow> {
  final String id;
  final int createdAt;
  final String payload;
  const HistoryRow({
    required this.id,
    required this.createdAt,
    required this.payload,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['created_at'] = Variable<int>(createdAt);
    map['payload'] = Variable<String>(payload);
    return map;
  }

  HistoryRowsCompanion toCompanion(bool nullToAbsent) {
    return HistoryRowsCompanion(
      id: Value(id),
      createdAt: Value(createdAt),
      payload: Value(payload),
    );
  }

  factory HistoryRow.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return HistoryRow(
      id: serializer.fromJson<String>(json['id']),
      createdAt: serializer.fromJson<int>(json['createdAt']),
      payload: serializer.fromJson<String>(json['payload']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'createdAt': serializer.toJson<int>(createdAt),
      'payload': serializer.toJson<String>(payload),
    };
  }

  HistoryRow copyWith({String? id, int? createdAt, String? payload}) =>
      HistoryRow(
        id: id ?? this.id,
        createdAt: createdAt ?? this.createdAt,
        payload: payload ?? this.payload,
      );
  HistoryRow copyWithCompanion(HistoryRowsCompanion data) {
    return HistoryRow(
      id: data.id.present ? data.id.value : this.id,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      payload: data.payload.present ? data.payload.value : this.payload,
    );
  }

  @override
  String toString() {
    return (StringBuffer('HistoryRow(')
          ..write('id: $id, ')
          ..write('createdAt: $createdAt, ')
          ..write('payload: $payload')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, createdAt, payload);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is HistoryRow &&
          other.id == this.id &&
          other.createdAt == this.createdAt &&
          other.payload == this.payload);
}

class HistoryRowsCompanion extends UpdateCompanion<HistoryRow> {
  final Value<String> id;
  final Value<int> createdAt;
  final Value<String> payload;
  final Value<int> rowid;
  const HistoryRowsCompanion({
    this.id = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.payload = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  HistoryRowsCompanion.insert({
    required String id,
    required int createdAt,
    required String payload,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       createdAt = Value(createdAt),
       payload = Value(payload);
  static Insertable<HistoryRow> custom({
    Expression<String>? id,
    Expression<int>? createdAt,
    Expression<String>? payload,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (createdAt != null) 'created_at': createdAt,
      if (payload != null) 'payload': payload,
      if (rowid != null) 'rowid': rowid,
    });
  }

  HistoryRowsCompanion copyWith({
    Value<String>? id,
    Value<int>? createdAt,
    Value<String>? payload,
    Value<int>? rowid,
  }) {
    return HistoryRowsCompanion(
      id: id ?? this.id,
      createdAt: createdAt ?? this.createdAt,
      payload: payload ?? this.payload,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<int>(createdAt.value);
    }
    if (payload.present) {
      map['payload'] = Variable<String>(payload.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('HistoryRowsCompanion(')
          ..write('id: $id, ')
          ..write('createdAt: $createdAt, ')
          ..write('payload: $payload, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $HistoryRowsTable historyRows = $HistoryRowsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [historyRows];
}

typedef $$HistoryRowsTableCreateCompanionBuilder =
    HistoryRowsCompanion Function({
      required String id,
      required int createdAt,
      required String payload,
      Value<int> rowid,
    });
typedef $$HistoryRowsTableUpdateCompanionBuilder =
    HistoryRowsCompanion Function({
      Value<String> id,
      Value<int> createdAt,
      Value<String> payload,
      Value<int> rowid,
    });

class $$HistoryRowsTableFilterComposer
    extends Composer<_$AppDatabase, $HistoryRowsTable> {
  $$HistoryRowsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get payload => $composableBuilder(
    column: $table.payload,
    builder: (column) => ColumnFilters(column),
  );
}

class $$HistoryRowsTableOrderingComposer
    extends Composer<_$AppDatabase, $HistoryRowsTable> {
  $$HistoryRowsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get payload => $composableBuilder(
    column: $table.payload,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$HistoryRowsTableAnnotationComposer
    extends Composer<_$AppDatabase, $HistoryRowsTable> {
  $$HistoryRowsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<int> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get payload =>
      $composableBuilder(column: $table.payload, builder: (column) => column);
}

class $$HistoryRowsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $HistoryRowsTable,
          HistoryRow,
          $$HistoryRowsTableFilterComposer,
          $$HistoryRowsTableOrderingComposer,
          $$HistoryRowsTableAnnotationComposer,
          $$HistoryRowsTableCreateCompanionBuilder,
          $$HistoryRowsTableUpdateCompanionBuilder,
          (
            HistoryRow,
            BaseReferences<_$AppDatabase, $HistoryRowsTable, HistoryRow>,
          ),
          HistoryRow,
          PrefetchHooks Function()
        > {
  $$HistoryRowsTableTableManager(_$AppDatabase db, $HistoryRowsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$HistoryRowsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$HistoryRowsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$HistoryRowsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<int> createdAt = const Value.absent(),
                Value<String> payload = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => HistoryRowsCompanion(
                id: id,
                createdAt: createdAt,
                payload: payload,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required int createdAt,
                required String payload,
                Value<int> rowid = const Value.absent(),
              }) => HistoryRowsCompanion.insert(
                id: id,
                createdAt: createdAt,
                payload: payload,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$HistoryRowsTable, HistoryRow>(table),
                  BaseReferences<_$AppDatabase, $HistoryRowsTable, HistoryRow>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$HistoryRowsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $HistoryRowsTable,
      HistoryRow,
      $$HistoryRowsTableFilterComposer,
      $$HistoryRowsTableOrderingComposer,
      $$HistoryRowsTableAnnotationComposer,
      $$HistoryRowsTableCreateCompanionBuilder,
      $$HistoryRowsTableUpdateCompanionBuilder,
      (
        HistoryRow,
        BaseReferences<_$AppDatabase, $HistoryRowsTable, HistoryRow>,
      ),
      HistoryRow,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$HistoryRowsTableTableManager get historyRows =>
      $$HistoryRowsTableTableManager(_db, _db.historyRows);
}
