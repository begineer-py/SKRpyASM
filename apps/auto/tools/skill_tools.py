import logging
from django_ai_assistant import method_tool

logger = logging.getLogger(__name__)


class SkillMixin:
    """
    Skill System Tools Mixin
    Provides tools for searching, loading, creating, updating, deleting, and executing reusable skills.
    """

    @method_tool
    def search_skills(self, query: str) -> str:
        """
        [Skill System] 透過關鍵字搜尋全域通用的技能清單 (Skill Templates)。
        這能幫助你發現在過去任務中寫好的自動化繞過腳本 (如 CSRF token 獲取工具等)。
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        from django.db.models import Q
        
        skills = SkillTemplate.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        ).order_by('-usage_count')[:10]
        
        if not skills.exists():
            return f"找不到符合 '{query}' 的 Skill。"
            
        res = [f"Found {skills.count()} skills:"]
        for s in skills:
            res.append(f"- Name: {s.name}\n  Tags: {s.tags}\n  Usage Count: {s.usage_count}\n  Description: {s.description}")
        return "\n".join(res)

    @method_tool
    def load_skill(self, name: str) -> str:
        """
        [Skill System] 載入指定名稱的 Skill 詳細內容，包括如何使用的 Instructions 以及底層的 script_content。
        你在執行此技能前，必須先 Load 閱讀其 Instructions 了解具體傳參格式與執行方式。
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        try:
            skill = SkillTemplate.objects.get(name=name)
            return f"Skill Name: {skill.name}\nTags: {skill.tags}\nUsage Count: {skill.usage_count}\n\n=== INSTRUCTIONS ===\n{skill.instructions}\n\n=== SCRIPT CONTENT ({skill.language}) ===\n{skill.script_content or 'No script contents.'}"
        except SkillTemplate.DoesNotExist:
            return f"Skill '{name}' 不存在。"

    @method_tool
    def create_or_update_skill(self, name: str, description: str, instructions: str, script_content: str, language: str = "python", tags: list[str] = None) -> str:
        """
        [Skill System] 讓AI自我進化：當你手刻了繞過腳本或高度可重用的工具（例如自動登入、獲取 CSRF）時，呼叫此系統永久儲存進資料庫。
        這能讓你在未來遇到其他目標時，透過 search_skills 重新找回並重用這段智慧，避免重複造輪子。
        
        Args:
            name: 唯一標識符，如 'django-csrf-bypass'
            description: 供搜尋用的摘要（請寫清楚這能解決什麼痛點）
            instructions: 指南。該如何執行腳本？有什麼必要的 args (例如目標 URL)
            script_content: 程式碼本體字串
            language: 'python' 或 'bash'
            tags: 相關標籤陣列，例如 ["django", "csrf", "bypass"]
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        if tags is None:
            tags = []
            
        skill, created = SkillTemplate.objects.update_or_create(
            name=name,
            defaults={
                "description": description,
                "instructions": instructions,
                "script_content": script_content,
                "language": language,
                "tags": tags
            }
        )
        action = "Created new" if created else "Updated existing"
        return f"[SUCCESS] {action} Skill '{name}'. ID: {skill.id}. 它現在已常駐於資料庫中，供未來調用。"

    @method_tool
    def delete_skill(self, name: str) -> str:
        """
        [Skill System] 刪除資料庫中指定的 Skill。
        如果發現某個 Skill 已經無效、有語法錯誤、或是防禦價值過低（例如只是發送簡單的 GET 請求），必須呼叫此工具將其永久刪除，以保持技能庫的整潔。
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        try:
            skill = SkillTemplate.objects.get(name=name)
            skill.delete()
            return f"[SUCCESS] 已經成功從資料庫刪除 Skill '{name}'。"
        except SkillTemplate.DoesNotExist:
            return f"Skill '{name}' 不存在，無須刪除。"

    @method_tool
    def execute_skill_script(self, name: str, args_string: str = "") -> str:
        """
        [Skill System] 安全地執行資料庫中已存檔的 Skill 腳本。
        系統會將程式碼 dump 到暫存檔，並搭配你提供的 args_string (如 '--url https://target.com') 執行，執行後自動清理暫存。
        
        Args:
            name: 技能名稱 (需已存在於庫中)
            args_string: 命令列參數字串
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        import subprocess
        import tempfile
        import os
        import docker
        
        try:
            skill = SkillTemplate.objects.get(name=name)
        except SkillTemplate.DoesNotExist:
            return f"Skill '{name}' does not exist. Use load_skill or search_skills to verify."
            
        # 增加使用次數 (自我演化排序權重)
        skill.usage_count += 1
        skill.save(update_fields=["usage_count"])
        
        ext = ".py" if skill.language.lower() == "python" else ".sh"
        runner = "python3" if skill.language.lower() == "python" else "bash"
        host_sandbox_dir = "/tmp/c2_sandbox_scripts"
        os.makedirs(host_sandbox_dir, exist_ok=True)
        
        try:
            client = docker.from_env()
            container = client.containers.get('c2_kali_sandbox')
            
            # 將檔案寫入本機與 Docker 共享的 Volume 內
            with tempfile.NamedTemporaryFile(dir=host_sandbox_dir, suffix=ext, delete=False, mode='w', encoding='utf-8') as f:
                f.write(skill.script_content or "")
                tmp_filename = os.path.basename(f.name)
                host_path = f.name
                
            # 使用 docker sdk 將執行環境徹底轉換至 Kali 容器中
            sandbox_path = f"/scripthub/{tmp_filename}"
            # 若 args_string 含有引號，在 shell cmd 時處理比較安全
            exit_code, output_bytes = container.exec_run(
                cmd=f"{runner} {sandbox_path} {args_string}",
                detach=False,
                stream=False
            )
            
            # 執行後清理腳本
            if os.path.exists(host_path):
                os.remove(host_path)
            
            output = f"Executed Skill: {name} (Usage Count now {skill.usage_count})\n"
            output += f"Execution Environment: Kali Docker Sandbox (c2_kali_sandbox)\n"
            output += f"Return Code: {exit_code}\n\n"
            output += f"--- OUTPUT ---\n{output_bytes.decode('utf-8', errors='replace')}\n"
                
            return output
            
        except docker.errors.NotFound:
            if 'host_path' in locals() and os.path.exists(host_path):
                os.remove(host_path)
            return "錯誤：找不到 Sandbox 容器 (c2_kali_sandbox)。請手動啟動 sandbox。"
        except Exception as e:
            if 'host_path' in locals() and os.path.exists(host_path):
                os.remove(host_path)
            return f"[ERROR] Kali Sandbox 執行發生系統異常: {e}"

    @method_tool
    def install_sandbox_dependency(self, package_manager: str, package_name: str) -> str:
        """
        [Skill System] 當你的腳本缺少相依套件 (例如執行時跳出 ImportError，或 bash 跳出 command not found) 時，你可以呼叫此工具自行為 Kali Docker Sandbox 安裝套件。
        
        Args:
            package_manager: 只能是 'apt' 或 'pip'
            package_name: 要安裝的套件名稱 (例如 'paramiko' 或 'mariadb-client')
        """
        import docker
        if package_manager not in ['apt', 'pip']:
            return "package_manager 必須是 'apt' 或 'pip'"
            
        if package_manager == "apt":
            cmd = f"apt-get update && apt-get install -y --no-install-recommends {package_name}"
        else:
            # Kali is PEP-668 managed, we must append --break-system-packages
            cmd = f"pip3 install {package_name} --break-system-packages"
            
        try:
            client = docker.from_env()
            container = client.containers.get('c2_kali_sandbox')
            exit_code, output_bytes = container.exec_run(
                cmd=["/bin/bash", "-c", cmd],
                detach=False,
                stream=False
            )
            res = f"Installed {package_name} via {package_manager}.\nExit Code: {exit_code}\nOutput:\n{output_bytes.decode('utf-8', errors='replace')}"
            return res
        except docker.errors.NotFound:
            return "錯誤：找不到 Sandbox 容器 (c2_kali_sandbox)。"
        except Exception as e:
            return f"[ERROR] 安裝套件時發生錯誤: {e}"
