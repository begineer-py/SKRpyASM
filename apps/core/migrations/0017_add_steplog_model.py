# Generated migration for StepLog model
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_step_completed_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='StepLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('INFO', 'Info'), ('DEBUG', 'Debug'), ('WARN', 'Warning'), ('ERROR', 'Error'), ('AI_THOUGHT', 'AI Thought Process'), ('ACTION', 'Action Started'), ('RESULT', 'Action Result')], default='INFO', help_text='日誌等級', max_length=20)),
                ('tag', models.CharField(choices=[('SKILL_EXEC', 'Skill Execution'), ('COMMAND', 'Shell Command'), ('API_CALL', 'API Call'), ('SCAN', 'Scanning Tool'), ('PARSE', 'Result Parsing'), ('DECISION', 'Decision Making'), ('ERROR_HANDLING', 'Error Handling'), ('STATE_UPDATE', 'State Update'), ('CHECKPOINT', 'Checkpoint')], default='CHECKPOINT', help_text='日誌分類標籤', max_length=30)),
                ('message', models.TextField(help_text='詳細的日誌訊息（可包含命令、輸出、錯誤棧跡等）')),
                ('action_status', models.CharField(blank=True, choices=[('STARTED', 'Started'), ('IN_PROGRESS', 'In Progress'), ('SUCCESS', 'Success'), ('FAILED', 'Failed'), ('PARTIAL', 'Partial Success'), ('SKIPPED', 'Skipped')], help_text='動作的執行狀態', max_length=50, null=True)),
                ('execution_time_ms', models.IntegerField(blank=True, help_text='執行耗時（毫秒）', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='日誌建立時間')),
                ('sequence', models.PositiveIntegerField(db_index=True, default=0, help_text='此 Step 內的日誌序列號')),
                ('step', models.ForeignKey(help_text='所屬的 Step', on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='core.step', db_index=True)),
            ],
            options={
                'ordering': ['step', 'sequence', 'created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='steplog',
            index=models.Index(fields=['step', 'created_at'], name='core_steplo_step_id_created_idx'),
        ),
        migrations.AddIndex(
            model_name='steplog',
            index=models.Index(fields=['step', 'level'], name='core_steplo_step_id_level_idx'),
        ),
        migrations.AddIndex(
            model_name='steplog',
            index=models.Index(fields=['step', 'tag'], name='core_steplo_step_id_tag_idx'),
        ),
    ]
