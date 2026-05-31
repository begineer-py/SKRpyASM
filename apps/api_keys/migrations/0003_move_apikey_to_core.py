"""
State-only migration: remove APIKey from api_keys's state.
The actual DB table remains untouched — it is now owned by core via core.0008.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_keys', '0002_alter_apikey_service_name'),
        ('core', '0008_move_models_from_ai_assistant_and_api_keys'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name='APIKey'),
            ],
            database_operations=[],
        ),
    ]
