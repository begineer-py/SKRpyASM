from django.db import models
from django.core.exceptions import ValidationError
import json
import re

class SkillTemplate(models.Model):
    """
    通用技能打點範本 (Skill System)
    基於 RAG (Retrieval-Augmented Generation) 理念，允許 AI 將常用的程式腳本與操作指引寫入資料庫，
    實作自我進化與跨 Target (任務) 之間的重用。
    
    支援兩種技能本質：
    - script：可執行腳本（Python/Bash），透過 execute_skill_script 在 sandbox 執行
    - documentation：AI 閱讀的技術指引文件，透過 follow_skill_guidance 由 agent 自主遵循
    - hybrid：文件 + 腳本（兩者皆有）
    """
    SKILL_TYPE_CHOICES = [
        ("script", "Script — 可執行腳本"),
        ("documentation", "Documentation — AI 閱讀指引文件"),
        ("hybrid", "Hybrid — 文件 + 腳本"),
    ]

    # === 技能類型（決定如何被 agent 使用）===
    skill_type = models.CharField(
        max_length=20,
        choices=SKILL_TYPE_CHOICES,
        default="script",
        db_index=True,
        help_text="技能本質：script（可執行）/ documentation（指引文件）/ hybrid（兩者皆有）",
    )

    name = models.CharField(max_length=100, db_index=True, help_text="技能名稱，例如 django-csrf-bypass")
    description = models.TextField(help_text="技能摘要描述。用於 RAG 檢索，讓 AI 判斷是否需要呼叫此技能。")

    # === 文件型技能專用（skill_type=documentation 或 hybrid）===
    short_description = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="一行簡短說明（documentation 型技能建議填寫，供快速判斷用途）",
    )
    detailed_overview = models.TextField(
        blank=True,
        default="",
        help_text="大篇幅技術指引（documentation 型技能專用）。包含執行原理、檢測步驟、背景知識。",
    )

    instructions = models.TextField(help_text="等同於 SKILL.md，包含該如何正確使用與傳參的指南。")
    script_content = models.TextField(blank=True, null=True, help_text="實際執行的工具源碼 (例如 Python 或 Bash 腳本)。")
    script_body = models.TextField(
        blank=True,
        null=True,
        help_text=(
            "腳本核心邏輯（僅含 main() 函式實作）。"
            "禁止在此欄位寫 I/O 處理代碼（sys.argv/argparse/print）。"
            "I/O Contract 由系統根據 input_schema/output_schema 自動注入。"
            "格式規範：def main(inputs: SkillInput) -> None:"
        ),
    )
    language = models.CharField(max_length=20, default="python", help_text="腳本語言", choices=[("python", "Python"), ("bash", "Bash")])
    tags = models.JSONField(default=list, help_text="標籤(如 'django', 'csrf', 'python') 用於分類與過濾")
    usage_count = models.IntegerField(default=0, help_text="被使用的次數，幫助排序高信賴度的且被重複驗證過的技能")
    
    # === 新增：類型驗證系統 ===
    # 輸入參數的 JSON Schema（例如：{"type": "object", "properties": {"url": {"type": "string", "pattern": "https?://.*"}}, "required": ["url"]}）
    input_schema = models.JSONField(
        default=dict, 
        blank=True,
        null=True,
        help_text="執行前需要驗證的輸入參數 JSON Schema。例如：{'type': 'object', 'properties': {'url': {'type': 'string'}}, 'required': ['url']}"
    )
    
    # 輸出的預期結構（例如：{"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "string"}}, "required": ["success"]}）
    output_schema = models.JSONField(
        default=dict, 
        blank=True,
        null=True,
        help_text="腳本輸出的預期 JSON Schema。用於驗證腳本是否按預期格式輸出。"
    )
    
    # 是否為「健壯」技能（已過多次驗證、不再變動）
    is_robust = models.BooleanField(
        default=False,
        help_text="標記此技能已多次驗證、輸入輸出穩定，不再允許任意修改。避免 AI 意外破壞經過驗證的技能。"
    )
    
    # 最後驗證通過的時間（用於判斷是否需要重新驗證）
    last_verified_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="上次成功執行並通過輸出驗證的時間。如果距離現在超過 7 天，應進行重驗證。"
    )
    
    # 失敗記錄（存儲最近的失敗信息，便于診斷）
    last_failure_reason = models.TextField(
        blank=True,
        null=True,
        help_text="最近一次執行失敗的原因與錯誤訊息。用於 AI 診斷問題。"
    )
    
    # 版本控制（允許同一技能有多個版本）
    version = models.PositiveIntegerField(
        default=1,
        help_text="技能版本號。當修改已驗證的技能時自動遞增。"
    )
    
    # === 新增：I/O Contract 與合併追蹤 ===
    has_io_contract = models.BooleanField(
        default=False,
        help_text="是否已自動注入 Pydantic I/O 驗證代碼。"
    )
    test_input_example = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="一組具體的測試輸入範例（JSON），用於自動化驗證。可由 AI 或手動填入。"
    )
    merged_from = models.JSONField(
        default=list,
        blank=True,
        null=True,
        help_text="如果此技能是合併產物，記錄來源技能 ID 列表。例如: [1, 5, 12]"
    )
    is_deprecated = models.BooleanField(
        default=False,
        help_text="若此技能已被合併到其他技能，標記為棄用以避免使用。"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "core_skill_template"
        verbose_name = "Skill 技能"
        verbose_name_plural = "Skill 技能庫"
        ordering = ["-is_robust", "-usage_count", "-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=['name', 'version'], name='unique_skill_version')
        ]

    def clean(self):
        """模型級驗證：檢查 JSON Schema 的有效性"""
        # 檢查字數限制
        if self.description and len(self.description) > 500:
            raise ValidationError("description 不能超過 500 字")
        if self.instructions and len(self.instructions) > 2000:
            raise ValidationError("instructions 不能超過 2000 字")

        # 驗證 input_schema 是有效的 JSON Schema
        if self.input_schema:
            try:
                if not isinstance(self.input_schema, dict):
                    raise ValidationError("input_schema 必須是有效的 JSON 物件")
                # 簡單檢查：必須有 'type' 或 'properties'
                if "type" not in self.input_schema and "properties" not in self.input_schema:
                    raise ValidationError("input_schema 必須包含 'type' 或 'properties' 欄位")
            except Exception as e:
                raise ValidationError(f"input_schema 格式錯誤: {str(e)}")
        
        # 驗證 output_schema
        if self.output_schema:
            try:
                if not isinstance(self.output_schema, dict):
                    raise ValidationError("output_schema 必須是有效的 JSON 物件")
            except Exception as e:
                raise ValidationError(f"output_schema 格式錯誤: {str(e)}")
        
        # 檢查名稱規範（kebab-case）
        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', self.name):
            raise ValidationError("name 必須使用 kebab-case 格式（如：django-csrf-bypass），只允許小寫字母、數字和連字符。")
        
        # 檢查 tags 是列表
        if not isinstance(self.tags, list):
            raise ValidationError("tags 必須是陣列類型")

        # script_body AST 格式檢查（僅 script / hybrid 型技能需要）
        if self.script_body and self.language == "python" and self.skill_type in ("script", "hybrid"):
            import ast
            try:
                tree = ast.parse(self.script_body)
                if not any(isinstance(n, ast.FunctionDef) and n.name == "main"
                           for n in ast.walk(tree)):
                    raise ValidationError("script_body 必須包含 def main(inputs: SkillInput) -> None: 函式")
            except SyntaxError as e:
                raise ValidationError(f"script_body 語法錯誤: {e}")

        # documentation 型技能必須填寫 detailed_overview
        if self.skill_type in ("documentation", "hybrid") and not self.detailed_overview:
            raise ValidationError("documentation / hybrid 型技能必須填寫 detailed_overview")

        # Pydantic schema 可解析性驗證（僅 script / hybrid 型技能需要）
        if (self.input_schema or self.output_schema) and self.language == "python" and self.skill_type in ("script", "hybrid"):
            from apps.core.validators.io_contract import IOContractGenerator
            try:
                code = IOContractGenerator.extract_pydantic_models(
                    self.input_schema, self.output_schema
                )
                compile(code, "<schema_check>", "exec")
            except SyntaxError as e:
                raise ValidationError(f"schema 無法生成合法 Pydantic 代碼: {e}")

    def save(self, *args, **kwargs):
        """保存前執行驗證"""
        update_fields = kwargs.get('update_fields')

        # 若有 script_body，自動組裝成完整的 script_content
        # 但如果 update_fields 指定了且不包含 script_content/script_body/input_schema/output_schema，
        # 則跳過重新組裝（避免冪等性問題觸發不必要的版本遞增）
        _skip_assembly = (
            update_fields is not None
            and not (set(update_fields) & {'script_content', 'script_body', 'input_schema', 'output_schema'})
        )

        if not _skip_assembly and self.script_body and self.language == "python":
            from apps.core.validators.io_contract import assemble_full_script
            self.script_content = assemble_full_script(
                script_body=self.script_body,
                input_schema=self.input_schema,
                output_schema=self.output_schema,
            )
            # 當組裝出 I/O Contract（有 input_schema 或 output_schema）時，標記 has_io_contract
            if self.input_schema or self.output_schema:
                self.has_io_contract = True

        if not _skip_assembly:
            self.full_clean()

        if self.is_robust and self.pk:
            original = SkillTemplate.objects.get(pk=self.pk)
            if original.script_content != self.script_content or original.input_schema != self.input_schema:
                self.pk = None
                self._state.adding = True
                self.version += 1
                self.is_robust = False
                self.last_verified_at = None
                # 新版本是 INSERT，不能用 update_fields（否則 Django 嘗試 UPDATE 無 PK 的物件）
                kwargs.pop('update_fields', None)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} v{self.version} ({self.usage_count} uses)" + (" [ROBUST]" if self.is_robust else "")
