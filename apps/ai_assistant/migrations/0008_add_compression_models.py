# Generated migration for context compression system

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ai_assistant', '0007_thread_bound_target_id'),
    ]

    operations = [
        # Add compression fields to Message model
        migrations.AddField(
            model_name='message',
            name='compressed_content',
            field=models.JSONField(blank=True, help_text='Compressed version of message for context optimization', null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='compression_applied',
            field=models.BooleanField(default=False, help_text='Whether compression has been applied to this message'),
        ),
        migrations.AddField(
            model_name='message',
            name='is_tool_output',
            field=models.BooleanField(default=False, help_text='Whether this message is a tool call output'),
        ),
        
        # Add index for compression queries
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['thread'], name='ai_assistant_message_thread_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['compression_applied'], name='ai_assistant_message_compression_idx'),
        ),
        
        # Create ThreadCompressionState model
        migrations.CreateModel(
            name='ThreadCompressionState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_message_count', models.IntegerField(default=0)),
                ('last_compressed_at', models.DateTimeField(blank=True, null=True)),
                ('last_compressed_message_id', models.BigIntegerField(blank=True, null=True)),
                ('compression_summary', models.JSONField(default=dict, help_text='Metadata about compression operations')),
                ('context_window_used_tokens', models.IntegerField(default=0, help_text='Estimated tokens currently in context window')),
                ('requires_compression', models.BooleanField(default=False, help_text='Flag set when context exceeds 128K tokens')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('thread', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='compression_state', to='ai_assistant.thread')),
            ],
            options={
                'verbose_name': 'Thread Compression State',
                'verbose_name_plural': 'Thread Compression States',
            },
        ),
        
        # Create GlobalContextOverview model
        migrations.CreateModel(
            name='GlobalContextOverview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mission', models.TextField(help_text='High-level mission objective')),
                ('confirmed_vulnerabilities', models.JSONField(default=list, help_text='List of confirmed vulnerabilities')),
                ('excluded_paths', models.JSONField(default=list, help_text='Attack vectors ruled out')),
                ('critical_artifacts', models.JSONField(default=list, help_text='Important artifacts to retain')),
                ('attempted_exploits', models.JSONField(default=list, help_text='Past exploits attempted')),
                ('current_phase', models.CharField(choices=[('RECONNAISSANCE', 'Reconnaissance'), ('SCANNING', 'Scanning'), ('ENUMERATION', 'Enumeration'), ('EXPLOITATION', 'Exploitation'), ('POST_EXPLOITATION', 'Post-Exploitation'), ('CLEANUP', 'Cleanup'), ('COMPLETED', 'Completed')], default='RECONNAISSANCE', max_length=50)),
                ('metrics', models.JSONField(default=dict, help_text='Metrics')),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('thread', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='global_overview', to='ai_assistant.thread')),
            ],
            options={
                'verbose_name': 'Global Context Overview',
                'verbose_name_plural': 'Global Context Overviews',
            },
        ),
        
        # Create MessageCompressionChunk model
        migrations.CreateModel(
            name='MessageCompressionChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chunk_index', models.IntegerField(help_text='Sequential index of this chunk')),
                ('start_message_id', models.BigIntegerField()),
                ('end_message_id', models.BigIntegerField()),
                ('original_content', models.JSONField(help_text='Original uncompressed messages in chunk')),
                ('compressed_content', models.JSONField(blank=True, help_text='Compressed version of messages', null=True)),
                ('compression_ratio', models.FloatField(default=0.0, help_text='Compression ratio')),
                ('tool_calls', models.JSONField(default=list, help_text='List of tools called in this chunk')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compression_chunks', to='ai_assistant.thread')),
            ],
            options={
                'verbose_name': 'Message Compression Chunk',
                'verbose_name_plural': 'Message Compression Chunks',
                'unique_together': {('thread', 'chunk_index')},
                'ordering': ('thread', 'chunk_index'),
            },
        ),
        
        # Create ToolOutputLifecycle model
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
                ('message', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='tool_lifecycle', to='ai_assistant.message')),
            ],
            options={
                'verbose_name': 'Tool Output Lifecycle',
                'verbose_name_plural': 'Tool Output Lifecycles',
            },
        ),
    ]
