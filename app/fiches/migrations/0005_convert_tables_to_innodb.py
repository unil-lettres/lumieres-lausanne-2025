# Convert legacy MyISAM tables to InnoDB.
#
# The database was imported from an old Django site where every table used the
# MyISAM engine. InnoDB brings transactions, row-level locking and real foreign
# key constraints, which the rest of the stack (and Django) assumes. This data
# migration converts every remaining MyISAM *base table* in the current schema.

from django.db import migrations


def convert_to_innodb(apps, schema_editor):
    connection = schema_editor.connection
    if connection.vendor != "mysql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND engine = 'MyISAM'
              AND table_type = 'BASE TABLE'
            """
        )
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            # Table names come from information_schema, not user input.
            cursor.execute(f"ALTER TABLE `{table}` ENGINE=InnoDB")


class Migration(migrations.Migration):
    # ALTER TABLE ... ENGINE triggers an implicit commit per statement in MySQL,
    # so wrapping it in a transaction is pointless.
    atomic = False

    dependencies = [
        ("fiches", "0004_transcription_modified_by_transcription_published_by_and_more"),
    ]

    operations = [
        # Irreversible on purpose: we never want to go back to MyISAM.
        migrations.RunPython(convert_to_innodb, migrations.RunPython.noop),
    ]
