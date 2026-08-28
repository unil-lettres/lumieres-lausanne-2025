"""Drop the obsolete ``django_content_type.name`` column on the legacy DB.

Django removed this column in 1.8 (``contenttypes.0002_remove_content_type_name``),
but on the legacy import that migration was *faked*: the row is recorded as applied
in ``django_migrations`` while the column is still physically present
(``varchar(100) NOT NULL`` without a default). As soon as a **new** model is added
(e.g. ``PlaceRecord``), creating its ``ContentType`` row — which the contenttypes
framework does on ``post_migrate`` and the admin does via
``ContentType.objects.get_or_create()`` — fails with
``IntegrityError (1364, "Field 'name' doesn't have a default value")``.

The column is dropped **only if it still exists**, so this is a no-op on any
database where it is already absent (the SQLite test DB, any post-1.8 install).
The reverse re-adds it as NULLable on purpose, to never reintroduce the trap.

Ordered before the place migrations so the column is gone before any new model —
and its ContentType — is created.
"""

from django.db import migrations

CT_TABLE = "django_content_type"
CT_COLUMN = "name"


def _column_exists(connection):
    with connection.cursor() as cursor:
        columns = connection.introspection.get_table_description(cursor, CT_TABLE)
    return any(col.name == CT_COLUMN for col in columns)


def drop_legacy_name(apps, schema_editor):
    connection = schema_editor.connection
    if _column_exists(connection):
        schema_editor.execute(f"ALTER TABLE `{CT_TABLE}` DROP COLUMN `{CT_COLUMN}`")


def readd_legacy_name(apps, schema_editor):
    connection = schema_editor.connection
    if not _column_exists(connection):
        schema_editor.execute(f"ALTER TABLE `{CT_TABLE}` ADD COLUMN `{CT_COLUMN}` varchar(100) NULL")


class Migration(migrations.Migration):
    # Raw DDL (ALTER TABLE) on MySQL cannot run inside a transaction: MySQL has
    # no transactional DDL, so Django forbids it in an atomic migration. Run
    # this migration non-atomically (the single ALTER is auto-committed).
    atomic = False

    dependencies = [
        ("fiches", "0005_convert_tables_to_innodb"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(drop_legacy_name, readd_legacy_name),
    ]
