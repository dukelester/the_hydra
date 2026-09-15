"""Convert integer primary keys to UUID on PostgreSQL.

Django's AlterField emits `USING id::uuid`, which PostgreSQL rejects for bigint.
SQLite is duck-typed, so the generated AlterField still works there.
"""

from __future__ import annotations

import uuid

INTEGER_TYPES = {"bigint", "integer", "smallint"}

EXTRA_FKS = [
    ("accounts_areawatch", "user_id", "accounts_user"),
    ("accounts_user_groups", "user_id", "accounts_user"),
    ("accounts_user_user_permissions", "user_id", "accounts_user"),
    ("django_admin_log", "user_id", "accounts_user"),
    ("projects_project", "institution_id", "projects_institution"),
    ("projects_budgetallocation", "project_id", "projects_project"),
    ("projects_budgetallocation", "source_document_id", "sources_sourcedocument"),
    ("projects_timelineevent", "project_id", "projects_project"),
    ("projects_timelineevent", "evidence_id", "sources_evidence"),
    ("projects_projectview", "user_id", "accounts_user"),
    ("projects_projectview", "project_id", "projects_project"),
    ("projects_projectfollow", "user_id", "accounts_user"),
    ("projects_projectfollow", "project_id", "projects_project"),
    ("projects_project_source_documents", "project_id", "projects_project"),
    ("projects_project_source_documents", "sourcedocument_id", "sources_sourcedocument"),
    ("sources_evidence", "project_id", "projects_project"),
    ("sources_evidence", "source_document_id", "sources_sourcedocument"),
    ("policies_policy", "institution_id", "projects_institution"),
    ("policies_policy", "source_document_id", "sources_sourcedocument"),
    ("investigations_investigation", "project_id", "projects_project"),
    ("investigations_investigation", "user_id", "accounts_user"),
    ("investigations_investigationattachment", "investigation_id", "investigations_investigation"),
    ("reports_issuereport", "project_id", "projects_project"),
    ("reports_issuereport", "investigation_id", "investigations_investigation"),
    ("reports_issuereport", "user_id", "accounts_user"),
]


def convert_tables(*tables):
    selected = list(tables)

    def _convert(apps, schema_editor):
        convert_bigint_pks_if_postgres(apps, schema_editor, tables=selected)

    return _convert


def convert_bigint_pks_if_postgres(apps, schema_editor, tables=None):
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        return

    quote = connection.ops.quote_name
    with connection.cursor() as cursor:
        table_names = set(connection.introspection.table_names())
        pk_tables = [table for table in (tables or []) if table in table_names]
        if not pk_tables:
            return

        leftover = [
            {"table": table, "column": column, "foreign_table": parent}
            for table, column, parent in EXTRA_FKS
            if table in table_names
            and parent in pk_tables
            and _column_type(cursor, table, column) in INTEGER_TYPES
        ]
        if not any(_column_type(cursor, table, "id") in INTEGER_TYPES for table in pk_tables) and not leftover:
            return

        fks = _foreign_keys(cursor, table_names, pk_tables)
        touched = set(pk_tables) | {item["table"] for item in leftover} | {item["table"] for item in fks}
        uniques = [item for item in _unique_constraints(cursor, table_names) if item["table"] in touched]
        for item in fks:
            cursor.execute(
                f"ALTER TABLE {quote(item['table'])} DROP CONSTRAINT IF EXISTS {quote(item['name'])}"
            )

        maps: dict[str, dict[object, uuid.UUID]] = {}
        for table in pk_tables:
            data_type = _column_type(cursor, table, "id")
            if data_type == "uuid":
                cursor.execute(f"SELECT id FROM {quote(table)}")
                maps[table] = {old: uuid.UUID(str(old)) for (old,) in cursor.fetchall()}
                continue
            if data_type not in INTEGER_TYPES:
                continue
            cursor.execute(f"SELECT id FROM {quote(table)}")
            maps[table] = {old: uuid.uuid4() for (old,) in cursor.fetchall()}
            _replace_column(cursor, quote, table, "id", maps[table], primary_key=True)

        converted_fks = set()
        for item in fks + leftover:
            table = item["table"]
            column = item["column"]
            parent = item["foreign_table"]
            key = (table, column)
            if key in converted_fks:
                continue
            if parent not in pk_tables:
                continue
            if _column_type(cursor, table, column) not in INTEGER_TYPES:
                continue
            not_null = _column_not_null(cursor, table, column)
            _replace_column(cursor, quote, table, column, maps.get(parent, {}), primary_key=False)
            if not_null:
                cursor.execute(
                    f"ALTER TABLE {quote(table)} ALTER COLUMN {quote(column)} SET NOT NULL"
                )
            converted_fks.add(key)

        for item in fks:
            cursor.execute(
                f"ALTER TABLE {quote(item['table'])} ADD CONSTRAINT {quote(item['name'])} "
                f"FOREIGN KEY ({quote(item['column'])}) REFERENCES {quote(item['foreign_table'])} "
                f"({quote(item['foreign_column'])}) "
                f"ON DELETE {item['delete_rule']} ON UPDATE {item['update_rule']}"
            )

        for item in uniques:
            cursor.execute(
                f"ALTER TABLE {quote(item['table'])} DROP CONSTRAINT IF EXISTS {quote(item['name'])}"
            )
            cursor.execute(
                f"ALTER TABLE {quote(item['table'])} ADD CONSTRAINT {quote(item['name'])} {item['definition']}"
            )


def _column_type(cursor, table, column):
    cursor.execute(
        """
        SELECT data_type
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
        """,
        [table, column],
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _column_not_null(cursor, table, column):
    cursor.execute(
        """
        SELECT is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
        """,
        [table, column],
    )
    row = cursor.fetchone()
    return bool(row) and row[0] == "NO"


def _unique_constraints(cursor, table_names):
    cursor.execute(
        """
        SELECT con.conname, rel.relname, pg_get_constraintdef(con.oid)
        FROM pg_constraint con
        JOIN pg_class rel ON rel.oid = con.conrelid
        JOIN pg_namespace nsp ON nsp.oid = con.connamespace
        WHERE nsp.nspname = 'public' AND con.contype = 'u'
        """
    )
    items = []
    for name, table, definition in cursor.fetchall():
        if table in table_names:
            items.append({"name": name, "table": table, "definition": definition})
    return items


def _foreign_keys(cursor, table_names, pk_tables):
    cursor.execute(
        """
        SELECT
            con.conname,
            src.relname,
            src_att.attname,
            tgt.relname,
            tgt_att.attname,
            CASE con.confdeltype
                WHEN 'a' THEN 'NO ACTION'
                WHEN 'r' THEN 'RESTRICT'
                WHEN 'c' THEN 'CASCADE'
                WHEN 'n' THEN 'SET NULL'
                WHEN 'd' THEN 'SET DEFAULT'
            END,
            CASE con.confupdtype
                WHEN 'a' THEN 'NO ACTION'
                WHEN 'r' THEN 'RESTRICT'
                WHEN 'c' THEN 'CASCADE'
                WHEN 'n' THEN 'SET NULL'
                WHEN 'd' THEN 'SET DEFAULT'
            END
        FROM pg_constraint con
        JOIN pg_class src ON src.oid = con.conrelid
        JOIN pg_class tgt ON tgt.oid = con.confrelid
        JOIN pg_namespace nsp ON nsp.oid = src.relnamespace
        JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS src_cols(attnum, ord) ON true
        JOIN LATERAL unnest(con.confkey) WITH ORDINALITY AS tgt_cols(attnum, ord)
          ON src_cols.ord = tgt_cols.ord
        JOIN pg_attribute src_att
          ON src_att.attrelid = src.oid AND src_att.attnum = src_cols.attnum
        JOIN pg_attribute tgt_att
          ON tgt_att.attrelid = tgt.oid AND tgt_att.attnum = tgt_cols.attnum
        WHERE con.contype = 'f' AND nsp.nspname = 'public'
        """
    )
    items = []
    for name, table, column, foreign_table, foreign_column, delete_rule, update_rule in cursor.fetchall():
        if table not in table_names or foreign_table not in table_names:
            continue
        if foreign_table not in pk_tables and table not in pk_tables:
            continue
        items.append(
            {
                "name": name,
                "table": table,
                "column": column,
                "foreign_table": foreign_table,
                "foreign_column": foreign_column,
                "delete_rule": delete_rule,
                "update_rule": update_rule,
            }
        )
    return items


def _replace_column(cursor, quote, table, column, mapping, primary_key):
    new_column = f"{column}_uuid"
    quoted_table = quote(table)
    quoted_column = quote(column)
    quoted_new = quote(new_column)
    cursor.execute(f"ALTER TABLE {quoted_table} ADD COLUMN {quoted_new} uuid")
    for old, new in mapping.items():
        cursor.execute(
            f"UPDATE {quoted_table} SET {quoted_new} = %s WHERE {quoted_column} = %s",
            [new, old],
        )
    if primary_key:
        cursor.execute(f"ALTER TABLE {quoted_table} DROP CONSTRAINT IF EXISTS {quote(f'{table}_pkey')}")
        cursor.execute(f"ALTER TABLE {quoted_table} ALTER COLUMN {quoted_column} DROP IDENTITY IF EXISTS")
    cursor.execute(f"ALTER TABLE {quoted_table} DROP COLUMN {quoted_column} CASCADE")
    cursor.execute(f"ALTER TABLE {quoted_table} RENAME COLUMN {quoted_new} TO {quoted_column}")
    if primary_key:
        cursor.execute(f"ALTER TABLE {quoted_table} ALTER COLUMN {quoted_column} SET DEFAULT gen_random_uuid()")
        cursor.execute(
            f"UPDATE {quoted_table} SET {quoted_column} = gen_random_uuid() WHERE {quoted_column} IS NULL"
        )
        cursor.execute(f"ALTER TABLE {quoted_table} ALTER COLUMN {quoted_column} SET NOT NULL")
        cursor.execute(f"ALTER TABLE {quoted_table} ADD PRIMARY KEY ({quoted_column})")
