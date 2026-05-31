"""
State-only migration: remove Thread, Message, and compression models
from ai_assistant's state. The actual DB tables remain untouched —
they are now owned by core via core.0008.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0011_message_role_thread_bound_overview_id_and_more'),
        ('core', '0008_move_models_from_ai_assistant_and_api_keys'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='ToolOutputLifecycle'),
                migrations.DeleteModel(name='MessageCompressionChunk'),
                migrations.DeleteModel(name='GlobalContextOverview'),
                migrations.DeleteModel(name='ThreadCompressionState'),
                migrations.DeleteModel(name='Message'),
                migrations.DeleteModel(name='Thread'),
            ],
            database_operations=[],
        ),
    ]
