from django.core.management.base import BaseCommand
from apps.core.models.analyze.SkillTemplate import SkillTemplate
import ast

class Command(BaseCommand):
    help = "清理不符合新架構規範的舊技能數據"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("開始清理技能庫..."))
        
        skills = SkillTemplate.objects.all()
        total = skills.count()
        deleted_count = 0
        
        for skill in skills:
            reason = None
            
            # 1. 檢查是否為測試數據
            if skill.name.startswith("test-"):
                reason = "測試數據 (test- 開頭)"
            
            # 2. 檢查是否已棄用
            elif skill.is_deprecated:
                reason = "已棄用 (is_deprecated=True)"
                
            # 3. 檢查 Python 結構
            elif skill.language == "python":
                if not skill.script_body:
                    reason = "缺少 script_body (舊格式)"
                else:
                    try:
                        tree = ast.parse(skill.script_body)
                        has_main = any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in ast.walk(tree))
                        if not has_main:
                            reason = "script_body 缺少 main() 函式"
                    except SyntaxError:
                        reason = "script_body 語法錯誤"

            # 4. 檢查名稱規範 (kebab-case)
            import re
            if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', skill.name):
                reason = f"名稱格式錯誤: {skill.name} (應為 kebab-case)"

            if reason:
                self.stdout.write(self.style.NOTICE(f"刪除技能: {skill.name} (ID: {skill.id}) - 原因: {reason}"))
                skill.delete()
                deleted_count += 1

        self.stdout.write(self.style.SUCCESS(f"清理完成。共掃描 {total} 個技能，刪除 {deleted_count} 個不合規技能。"))
