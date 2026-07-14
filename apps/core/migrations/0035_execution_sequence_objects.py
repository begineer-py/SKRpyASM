from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0034_verification_vulnerability_fk"),
    ]
    operations = [
        migrations.RunSQL(
            sql="""
                CREATE SEQUENCE IF NOT EXISTS execution_graph_node_seq;
                CREATE SEQUENCE IF NOT EXISTS execution_node_event_seq;
                SELECT setval('execution_graph_node_seq',
                    COALESCE((SELECT MAX(sequence) FROM execution_node), 0) + 1, false);
                SELECT setval('execution_node_event_seq',
                    COALESCE((SELECT MAX(sequence) FROM execution_event), 0) + 1, false);
            """,
            reverse_sql="""
                DROP SEQUENCE IF EXISTS execution_graph_node_seq;
                DROP SEQUENCE IF EXISTS execution_node_event_seq;
            """,
        ),
    ]
