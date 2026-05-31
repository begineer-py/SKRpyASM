"""
State-only migration: move Thread, Message, compression models from ai_assistant,
and APIKey from api_keys into core's model state.
No database operations — existing tables are preserved via db_table Meta.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_rename_core_skill__skill_a_57509f_core_skill__skill_a_60375d_idx_and_more'),
        ('ai_assistant', '0011_message_role_thread_bound_overview_id_and_more'),
        ('api_keys', '0002_alter_apikey_service_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ── 1. Create all 7 models in core's state ────────────────────────
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Thread
                migrations.CreateModel(
                    name='Thread',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('name', models.CharField(blank=True, max_length=255)),
                        ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ai_assistant_threads', to=settings.AUTH_USER_MODEL)),
                        ('assistant_id', models.CharField(blank=True, max_length=255)),
                        ('bound_target_id', models.IntegerField(blank=True, help_text='The Target ID this thread is currently focused on. Set by the AI agent via bind_to_target tool.', null=True)),
                        ('bound_overview_id', models.IntegerField(blank=True, help_text='The Overview ID this thread is currently focused on. Automatically set when binding to a target.', null=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('is_hidden', models.BooleanField(default=False, help_text='If True, this thread is internal/ephemeral and hidden from the main chat list.')),
                    ],
                    options={
                        'verbose_name': 'Thread',
                        'verbose_name_plural': 'Threads',
                        'ordering': ('-created_at',),
                        'db_table': 'ai_assistant_thread',
                        'indexes': [
                            models.Index(models.OrderBy(models.F('created_at'), descending=True), name='thread_created_at_desc'),
                        ],
                    },
                ),
                # Message
                migrations.CreateModel(
                    name='Message',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('message', models.JSONField()),
                        ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='core.thread')),
                        ('compressed_content', models.JSONField(blank=True, help_text='Compressed version of message for context optimization', null=True)),
                        ('compression_applied', models.BooleanField(default=False, help_text='Whether compression has been applied to this message')),
                        ('is_tool_output', models.BooleanField(default=False, help_text='Whether this message is a tool call output')),
                        ('role', models.CharField(choices=[('human', 'Human'), ('ai', 'AI'), ('tool_call', 'Tool Call'), ('tool_result', 'Tool Result'), ('system', 'System')], default='ai', help_text='The role/type of the message (human, ai, tool_call, tool_result, system)', max_length=20)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                    ],
                    options={
                        'verbose_name': 'Message',
                        'verbose_name_plural': 'Messages',
                        'ordering': ('created_at',),
                        'db_table': 'ai_assistant_message',
                        'indexes': [
                            models.Index(models.F('created_at'), name='message_created_at'),
                            models.Index(models.F('thread'), name='message_thread'),
                            models.Index(models.F('compression_applied'), name='message_compression_applied'),
                            models.Index(models.F('role'), name='message_role'),
                        ],
                    },
                ),
                # ThreadCompressionState
                migrations.CreateModel(
                    name='ThreadCompressionState',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('total_message_count', models.IntegerField(default=0)),
                        ('last_compressed_at', models.DateTimeField(blank=True, null=True)),
                        ('last_compressed_message_id', models.BigIntegerField(blank=True, null=True)),
                        ('compression_summary', models.JSONField(default=dict, help_text='Metadata about compression operations: {compression_count, chunks_count, last_overview_update}')),
                        ('context_window_used_tokens', models.IntegerField(default=0, help_text='Estimated tokens currently in context window')),
                        ('requires_compression', models.BooleanField(default=False, help_text='Flag set when context exceeds 128K tokens')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('thread', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='compression_state', to='core.thread')),
                    ],
                    options={
                        'verbose_name': 'Thread Compression State',
                        'verbose_name_plural': 'Thread Compression States',
                        'db_table': 'ai_assistant_threadcompressionstate',
                    },
                ),
                # GlobalContextOverview
                migrations.CreateModel(
                    name='GlobalContextOverview',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('mission', models.TextField(help_text='High-level mission objective')),
                        ('confirmed_vulnerabilities', models.JSONField(default=list, help_text='List of confirmed vulnerabilities: [{title, cve, severity, location}]')),
                        ('excluded_paths', models.JSONField(default=list, help_text='Attack vectors ruled out: [{path, reason, timestamp}]')),
                        ('critical_artifacts', models.JSONField(default=list, help_text='Important artifacts to retain: [{type, value_hash, location, importance}]')),
                        ('attempted_exploits', models.JSONField(default=list, help_text='Past exploits attempted: [{tool, target, result, timestamp}]')),
                        ('current_phase', models.CharField(choices=[('RECONNAISSANCE', 'Reconnaissance'), ('SCANNING', 'Scanning'), ('ENUMERATION', 'Enumeration'), ('EXPLOITATION', 'Exploitation'), ('POST_EXPLOITATION', 'Post-Exploitation'), ('CLEANUP', 'Cleanup'), ('COMPLETED', 'Completed')], default='RECONNAISSANCE', max_length=50)),
                        ('metrics', models.JSONField(default=dict, help_text='Metrics: {hosts_discovered, ports_found, services_identified, exploits_successful}')),
                        ('generated_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('thread', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='global_overview', to='core.thread')),
                    ],
                    options={
                        'verbose_name': 'Global Context Overview',
                        'verbose_name_plural': 'Global Context Overviews',
                        'db_table': 'ai_assistant_globalcontextoverview',
                    },
                ),
                # MessageCompressionChunk
                migrations.CreateModel(
                    name='MessageCompressionChunk',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('chunk_index', models.IntegerField(help_text='Sequential index of this chunk')),
                        ('start_message_id', models.BigIntegerField()),
                        ('end_message_id', models.BigIntegerField()),
                        ('original_content', models.JSONField(help_text='Original uncompressed messages in chunk')),
                        ('compressed_content', models.JSONField(blank=True, help_text='Compressed version of messages', null=True)),
                        ('compression_ratio', models.FloatField(default=0.0, help_text='Compression ratio: (1 - compressed_size/original_size) * 100')),
                        ('tool_calls', models.JSONField(default=list, help_text='List of tools called in this chunk')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compression_chunks', to='core.thread')),
                    ],
                    options={
                        'verbose_name': 'Message Compression Chunk',
                        'verbose_name_plural': 'Message Compression Chunks',
                        'ordering': ('thread', 'chunk_index'),
                        'unique_together': {('thread', 'chunk_index')},
                        'db_table': 'ai_assistant_messagecompressionchunk',
                    },
                ),
                # ToolOutputLifecycle
                migrations.CreateModel(
                    name='ToolOutputLifecycle',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('tool_name', models.CharField(max_length=255)),
                        ('strategy', models.CharField(choices=[('DISCARD', 'Discard Entirely'), ('TEXTUALIZE', 'Textualize'), ('RETAIN', 'Retain Full Content')], default='TEXTUALIZE', max_length=20)),
                        ('original_output_size', models.IntegerField(help_text='Original output size in characters')),
                        ('compressed_size', models.IntegerField(default=0, help_text='Compressed output size')),
                        ('compressed_output', models.TextField(blank=True, help_text='Textual summary if strategy=TEXTUALIZE', null=True)),
                        ('reason', models.TextField(help_text='Why this strategy was selected')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('message', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tool_lifecycle', to='core.message')),
                    ],
                    options={
                        'verbose_name': 'Tool Output Lifecycle',
                        'verbose_name_plural': 'Tool Output Lifecycles',
                        'db_table': 'ai_assistant_tooloutputlifecycle',
                    },
                ),
                # APIKey
                migrations.CreateModel(
                    name='APIKey',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('service_name', models.CharField(help_text="服務名稱 (例如: 'shodan', 'OPENAI', 'HUNTER' - 可重複以支援多個金鑰輪轉)", max_length=100)),
                        ('key_value', models.CharField(help_text='API 金鑰的實際值', max_length=512)),
                        ('is_active', models.BooleanField(default=True, help_text='是否啟用此金鑰')),
                        ('description', models.TextField(blank=True, help_text='服務描述或備註', null=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        'verbose_name': 'API 金鑰',
                        'verbose_name_plural': 'API 金鑰',
                        'db_table': 'api_keys_apikey',
                    },
                ),
            ],
            database_operations=[],
        ),
        # ── 2. Update Overview FKs from ai_assistant.thread → core.Thread ─
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='overview',
                    name='thread',
                    field=models.ForeignKey(
                        blank=True,
                        db_column='thread_id',
                        help_text='筆記本 Overview 的 AI 對話 Thread (for push-callback)',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='overviews',
                        to='core.thread',
                    ),
                ),
                migrations.AlterField(
                    model_name='overview',
                    name='parent_thread',
                    field=models.ForeignKey(
                        blank=True,
                        db_column='parent_thread_id',
                        help_text='建立此任務的上層節點/Caller Thread (for async completion callback)',
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='child_overviews',
                        to='core.thread',
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
