from django.db import models

class SkillTemplate(models.Model):
    """
    通用技能打點範本 (Skill System)
    基於 RAG (Retrieval-Augmented Generation) 理念，允許 AI 將常用的程式腳本與操作指引寫入資料庫，
    實作自我進化與跨 Target (任務) 之間的重用。
    """
    name = models.CharField(max_length=100, unique=True, help_text="技能名稱，例如 django-csrf-bypass")
    description = models.TextField(help_text="技能摘要描述。用於 RAG 檢索，讓 AI 判斷是否需要呼叫此技能。")
    instructions = models.TextField(help_text="等同於 SKILL.md，包含該如何正確使用與傳參的指南。")
    script_content = models.TextField(blank=True, null=True, help_text="實際執行的工具源碼 (例如 Python 或 Bash 腳本)。")
    language = models.CharField(max_length=20, default="python", help_text="腳本語言")
    tags = models.JSONField(default=list, help_text="標籤(如 'django', 'csrf', 'python') 用於分類與過濾")
    usage_count = models.IntegerField(default=0, help_text="被使用的次數，幫助排序高信賴度的且被重複驗證過的技能")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "core_skill_template"
        verbose_name = "Skill 技能"
        verbose_name_plural = "Skill 技能庫"
        ordering = ["-usage_count", "-updated_at"]

    def __str__(self):
        return f"{self.name} ({self.usage_count} uses)"
