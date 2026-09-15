import uuid

from django.db import migrations


TABLES = [
    "accounts_user",
    "accounts_areawatch",
    "projects_institution",
    "projects_project",
    "projects_budgetallocation",
    "projects_timelineevent",
    "projects_projectview",
    "projects_projectfollow",
    "sources_sourcedocument",
    "sources_evidence",
    "policies_policy",
    "investigations_investigation",
    "investigations_investigationattachment",
    "reports_issuereport",
]

FKS = [
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


def _is_legacy_int(value):
    return str(value).isdigit()


def convert_legacy_integer_ids(apps, schema_editor):
    connection = schema_editor.connection
    table_names = set(connection.introspection.table_names())
    maps = {}
    with connection.cursor() as cursor:
        for table in TABLES:
            if table not in table_names:
                maps[table] = {}
                continue
            cursor.execute(f"SELECT id FROM {table}")
            maps[table] = {}
            for (old,) in cursor.fetchall():
                if _is_legacy_int(old):
                    maps[table][old] = uuid.uuid4().hex
                else:
                    try:
                        maps[table][old] = uuid.UUID(str(old)).hex
                    except Exception:
                        maps[table][old] = str(old)
        for table, column, parent in FKS:
            if table not in table_names:
                continue
            columns = {item.name for item in connection.introspection.get_table_description(cursor, table)}
            if column not in columns:
                continue
            for old, new in maps[parent].items():
                if str(old) == new:
                    continue
                cursor.execute(
                    f"UPDATE {table} SET {column}=%s WHERE {column}=%s",
                    [new, old],
                )
        for table in TABLES:
            if table not in table_names:
                continue
            for old, new in maps[table].items():
                if str(old) == new:
                    continue
                cursor.execute(f"UPDATE {table} SET id=%s WHERE id=%s", [new, old])


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_alter_areawatch_id_alter_user_id"),
        ("investigations", "0004_alter_investigation_id_and_more"),
        ("policies", "0004_alter_policy_id"),
        ("projects", "0006_alter_timelineevent_options_and_more"),
        ("reports", "0002_alter_issuereport_id"),
        ("sources", "0004_alter_evidence_options_alter_evidence_id_and_more"),
    ]

    operations = [
        migrations.RunPython(convert_legacy_integer_ids, noop),
    ]
