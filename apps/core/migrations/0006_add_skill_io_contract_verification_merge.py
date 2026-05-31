"""
Migration 0006: Add I/O Contract fields, SkillVerification, SkillMergeEvaluation models.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_remove_overview_parent_thread_id_and_more"),
    ]

    operations = [
        # ── SkillTemplate: 新增欄位 ──
        migrations.AddField(
            model_name="skilltemplate",
            name="has_io_contract",
            field=models.BooleanField(
                default=False,
                help_text="是否已自動注入 Pydantic I/O 驗證代碼。",
            ),
        ),
        migrations.AddField(
            model_name="skilltemplate",
            name="test_input_example",
            field=models.JSONField(
                blank=True,
                default=dict,
                null=True,
                help_text="一組具體的測試輸入範例（JSON），用於自動化驗證。可由 AI 或手動填入。",
            ),
        ),
        migrations.AddField(
            model_name="skilltemplate",
            name="merged_from",
            field=models.JSONField(
                blank=True,
                default=list,
                null=True,
                help_text="如果此技能是合併產物，記錄來源技能 ID 列表。例如: [1, 5, 12]",
            ),
        ),
        migrations.AddField(
            model_name="skilltemplate",
            name="is_deprecated",
            field=models.BooleanField(
                default=False,
                help_text="若此技能已被合併到其他技能，標記為棄用以避免使用。",
            ),
        ),
        # ── 新模型: SkillVerification ──
        migrations.CreateModel(
            name="SkillVerification",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "verdict",
                    models.CharField(
                        choices=[
                            ("PENDING", "待驗證"),
                            ("PASSED", "通過 — 輸出符合預期"),
                            ("FAILED", "失敗 — 輸出不符合預期"),
                            ("INCONCLUSIVE", "無法確定 — Agent 無法明確判斷"),
                            ("ERROR", "系統錯誤 — 執行過程發生異常"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                (
                    "confidence_score",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        help_text="Agent 對驗證結果的信心程度 (0-100)",
                    ),
                ),
                (
                    "test_input_used",
                    models.JSONField(
                        blank=True,
                        null=True,
                        help_text="Agent 構造並使用的測試輸入（JSON）",
                    ),
                ),
                (
                    "raw_output",
                    models.TextField(
                        blank=True,
                        null=True,
                        help_text="執行腳本後的原始輸出",
                    ),
                ),
                (
                    "agent_notes",
                    models.TextField(
                        blank=True,
                        null=True,
                        help_text="Agent 的評估推理過程（詳細說明為什麼通過/失敗）",
                    ),
                ),
                (
                    "execution_duration_ms",
                    models.IntegerField(
                        blank=True,
                        null=True,
                        help_text="腳本執行耗時（毫秒）",
                    ),
                ),
                (
                    "executed_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "skill",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="verifications",
                        to="core.skilltemplate",
                    ),
                ),
            ],
            options={
                "db_table": "core_skill_verification",
                "ordering": ["-executed_at"],
                "verbose_name": "Skill 驗證記錄",
                "verbose_name_plural": "Skill 驗證歷史",
            },
        ),
        migrations.AddIndex(
            model_name="skillverification",
            index=models.Index(
                fields=["skill", "-executed_at"],
                name="core_skill__skill_i_08974d",
            ),
        ),
        migrations.AddIndex(
            model_name="skillverification",
            index=models.Index(
                fields=["verdict"],
                name="core_skill__verdict_41e300",
            ),
        ),
        # ── 新模型: SkillMergeEvaluation ──
        migrations.CreateModel(
            name="SkillMergeEvaluation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "merge_strategy",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("NOT_RECOMMENDED", "不建議合併"),
                            ("CONCAT", "串聯 — 合併 instructions 與 tags，保留各自 script"),
                            ("UNION", "Union — 合併 schema 與全部內容"),
                            ("LATEST_ONLY", "取最新 — 保留版本較新的技能"),
                            ("SMART_MERGE", "智能合併 — 自動融合 script 與 instructions"),
                            ("A_MERGES_INTO_B", "A 併入 B — A 的功能是 B 的子集"),
                            ("B_MERGES_INTO_A", "B 併入 A — B 的功能是 A 的子集"),
                        ],
                        max_length=30,
                        null=True,
                    ),
                ),
                (
                    "is_mergeable",
                    models.BooleanField(
                        help_text="null=待評估, True=可合併, False=不建議合併",
                        null=True,
                    ),
                ),
                (
                    "reasoning",
                    models.TextField(
                        blank=True,
                        null=True,
                        help_text="Agent 評估推理過程",
                    ),
                ),
                (
                    "evaluated_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "merged_into",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="merged_from_evaluations",
                        to="core.skilltemplate",
                        help_text="如果已執行合併，指向合併後產生的新技能",
                    ),
                ),
                (
                    "skill_a",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="merge_evals_as_a",
                        to="core.skilltemplate",
                    ),
                ),
                (
                    "skill_b",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="merge_evals_as_b",
                        to="core.skilltemplate",
                    ),
                ),
            ],
            options={
                "db_table": "core_skill_merge_evaluation",
                "ordering": ["-evaluated_at"],
                "verbose_name": "Skill 合併評估",
                "verbose_name_plural": "Skill 合併評估記錄",
                "unique_together": {("skill_a", "skill_b")},
            },
        ),
        migrations.AddIndex(
            model_name="skillmergeevaluation",
            index=models.Index(
                fields=["skill_a", "skill_b"],
                name="core_skill__skill_a_57509f",
            ),
        ),
        migrations.AddIndex(
            model_name="skillmergeevaluation",
            index=models.Index(
                fields=["is_mergeable"],
                name="core_skill__is_merg_da4bcc",
            ),
        ),
    ]
