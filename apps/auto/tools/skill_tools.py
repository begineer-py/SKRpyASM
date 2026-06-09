import logging
from apps.ai_assistant import method_tool
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class SkillMixin:
    """
    Skill System Tools Mixin
    Provides tools for searching, loading, creating, updating, deleting, and executing reusable skills.
    
    新增自動執行追蹤：所有腳本執行都會被記錄到 ExecutionArtifact，
    即使腳本未存入 SkillTemplate，也能追蹤完整的執行歷史。
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
        ).order_by('-is_robust', '-usage_count')[:10]
        
        if not skills.exists():
            return f"找不到符合 '{query}' 的 Skill。"
            
        res = [f"Found {skills.count()} skills:"]
        for s in skills:
            robust_badge = " [ROBUST]" if s.is_robust else ""
            res.append(
                f"- Name: {s.name} v{s.version}{robust_badge}\n"
                f"  Tags: {s.tags}\n"
                f"  Usage Count: {s.usage_count}\n"
                f"  Description: {s.description}"
            )
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
            
            # 組織輸出訊息
            msg = f"Skill Name: {skill.name} v{skill.version}\n"
            msg += f"Tags: {skill.tags}\n"
            msg += f"Usage Count: {skill.usage_count}\n"
            msg += f"Is Robust: {skill.is_robust}\n"
            
            if skill.input_schema:
                msg += f"\n=== INPUT SCHEMA ===\n{json.dumps(skill.input_schema, indent=2)}\n"
            
            if skill.output_schema:
                msg += f"\n=== OUTPUT SCHEMA ===\n{json.dumps(skill.output_schema, indent=2)}\n"
            
            msg += f"\n=== INSTRUCTIONS ===\n{skill.instructions}\n"
            msg += f"\n=== SCRIPT CONTENT ({skill.language}) ===\n{skill.script_content or 'No script contents.'}"
            
            return msg
        except SkillTemplate.DoesNotExist:
            return f"Skill '{name}' 不存在。"

    @method_tool
    def request_skill_creation(
        self,
        name: str,
        description: str,
        instructions: str,
        task_description: str,
        language: str = "python",
        tags: list = None,
        input_schema: dict = None,
        output_schema: dict = None,
    ) -> str:
        """
        [Skill System] 請求 SkillCreatorAgent 創建一個新的技能並存入資料庫。

        ⚠️ 這是唯一允許創建 Skill 的工具。AI 不應直接撰寫 script_content，
        而是透過此工具，由專用的 SkillCreatorAgent 協調生成符合規範的技能。

        SkillCreatorAgent 會自動：
        1. 根據 task_description + schema 生成腳本主體
        2. 驗證 AST 語法並自動注入 Pydantic I/O Contract
        3. 確保技能符合全域規範並存入資料庫
        4. **保存完整的對話歷史到資料庫**，以便追蹤技能創建過程

        Args:
            name: 唯一 kebab-case 標識符，例如 'django-csrf-bypass'
            description: ≤ 500 字的技能摘要（供 RAG 檢索）
            instructions: ≤ 2000 字的使用指南（如何傳參、注意事項）
            task_description: 自然語言描述此腳本應該做什麼
            language: 'python' 或 'bash'
            tags: 標籤陣列，例如 ["django", "csrf", "bypass"]
            input_schema: 輸入參數的 JSON Schema
            output_schema: 輸出的預期 JSON Schema
        """
        import json
        from apps.auto.assistants.skill_creator_agent import SkillCreatorAgent
        from django.contrib.auth import get_user_model

        if tags is None:
            tags = []

        # 準備給 SkillCreatorAgent 的輸入訊息
        import json
        input_data = {
            "name": name,
            "description": description,
            "instructions": instructions,
            "task_description": task_description,
            "input_schema": input_schema or {},
            "output_schema": output_schema or {},
            "language": language,
            "tags": tags
        }

        user_message = f"""Please create a new skill with the following specifications:

```json
{json.dumps(input_data, indent=2)}
```

Use the `create_skill` tool to create this skill. Make sure to carefully analyze the task description and generate appropriate code."""

        # 獲取系統使用者
        User = get_user_model()
        system_user = User.objects.filter(is_superuser=True).first()

        # 創建新的 Thread 並運行 SkillCreatorAgent
        from apps.ai_assistant.helpers.use_cases import create_thread, create_message
        thread_name = f"skill_creation_{name.replace('-', '_')}"
        thread = create_thread(
            name=thread_name,
            user=system_user,
            assistant_id=SkillCreatorAgent.id,
            is_hidden=True,
        )

        # 使用 SkillCreatorAgent 處理這個請求
        agent = SkillCreatorAgent()
        
        try:
            result = agent.run(user_message, thread_id=thread.id)
            return result
        except Exception as e:
            logger.exception(f"Failed to run SkillCreatorAgent: {e}")
            return f"[ERROR] SkillCreatorAgent failed: {str(e)}"

    @method_tool
    def deprecate_skill(self, name: str, reason: str = "") -> str:
        """
        [Skill System] 標記資料庫中指定的 Skill 為棄用 (Deprecated)。
        如果發現某個 Skill 已經無效、有語法錯誤、或是被更好的技能取代，必須呼叫此工具將其標記，以保持技能庫的整潔。
        棄用後的技能將不會被搜尋到，但會保留歷史記錄。
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        from apps.auto.skill_manager_agent import SkillManagerAgent
        
        manager = SkillManagerAgent()
        try:
            skill = SkillTemplate.objects.get(name=name)
            if manager.deprecate_skill(skill.id, reason=reason):
                return f"[SUCCESS] 已經成功將 Skill '{name}' 標記為棄用。"
            return f"[ERROR] 標記棄用時發生未知錯誤。"
        except SkillTemplate.DoesNotExist:
            return f"Skill '{name}' 不存在。"

    @method_tool
    def request_skill_merge(self, evaluation_id: int) -> str:
        """
        [Skill System] 執行特定的技能合併建議。
        當你發現系統已評估 (SkillMergeEvaluation) 出兩個技能有合併價值時，呼叫此工具執行實際合併。
        這會根據評估建議的策略 (如 CONCAT, UNION, LATEST_ONLY) 產生新技能並棄用舊技能。
        """
        from apps.auto.skill_manager_agent import SkillManagerAgent
        manager = SkillManagerAgent()
        result = manager.execute_merge(evaluation_id)
        if result["ok"]:
            res_msg = f"[SUCCESS] 合併執行成功。策略: {result['strategy']}\n"
            if "new_skill_id" in result:
                res_msg += f"產生了新技能 ID: {result['new_skill_id']}"
            elif "kept_skill_id" in result:
                res_msg += f"保留了技能 ID: {result['kept_skill_id']}"
            return res_msg
        else:
            return f"[ERROR] 合併執行失敗: {result.get('error')}"

    @method_tool
    def execute_skill_script(
        self, 
        name: str, 
        args_string: str = "", 
        attack_vector_id: int = None,
        input_json: dict = None
    ) -> str:
        """
        [Skill System] 安全地執行資料庫中已存檔的 Skill 腳本。
        系統會將程式碼 dump 到暫存檔，並搭配你提供的 args_string (如 '--url https://target.com') 執行，執行後自動清理暫存。
        
        === 新增：執行追蹤與驗證 ===
        所有執行都會被自動記錄到 ExecutionArtifact，即使腳本未存入 SkillTemplate。
        如果定義了 input/output schema，系統會自動進行類型驗證。
        
        Args:
            name: 技能名稱 (需已存在於庫中)
            args_string: 命令列參數字串
            attack_vector_id: 可選，關聯到特定攻擊向量（用於導出）
            input_json: 可選，結構化的輸入參數（JSON），將被驗證
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        from apps.core.validators.schema_validators import InputValidator, OutputValidator
        import subprocess
        import tempfile
        import os
        import docker
        
        try:
            skill = SkillTemplate.objects.get(name=name)
        except SkillTemplate.DoesNotExist:
            return f"Skill '{name}' does not exist. Use load_skill or search_skills to verify."
        
        # === 步驟 1：驗證輸入參數 ===
        input_validation_status = "NOT_VALIDATED"
        input_validation_error = None
        
        if input_json and skill.input_schema:
            is_valid, error_msg = InputValidator.validate(input_json, skill.input_schema)
            if not is_valid:
                input_validation_status = "INPUT_INVALID"
                input_validation_error = error_msg
                return f"[INPUT VALIDATION ERROR] {error_msg}"
            input_validation_status = "VALIDATED"
        
        # 增加使用次數
        skill.usage_count += 1
        skill.save(update_fields=["usage_count"])
        
        ext = ".py" if skill.language.lower() == "python" else ".sh"
        runner = "python3" if skill.language.lower() == "python" else "bash"
        host_sandbox_dir = "/tmp/c2_sandbox_scripts"
        os.makedirs(host_sandbox_dir, exist_ok=True)
        
        script_execution = None
        started_at = datetime.now(timezone.utc)
        
        try:
            # === 步驟 2：在 Docker 中執行腳本 ===
            client = docker.from_env()
            container = client.containers.get('c2_kali_sandbox')
            
            with tempfile.NamedTemporaryFile(dir=host_sandbox_dir, suffix=ext, delete=False, mode='w', encoding='utf-8') as f:
                f.write(skill.script_content or "")
                tmp_filename = os.path.basename(f.name)
                host_path = f.name
                
            sandbox_path = f"/scripthub/{tmp_filename}"
            # If skill has an I/O contract, pass input_json as first CLI arg for Pydantic validation
            io_args = ""
            if input_json:
                io_args = json.dumps(input_json)
            cmd = f"{runner} {sandbox_path} {io_args} {args_string}".strip()
            exit_code, output_bytes = container.exec_run(
                cmd=cmd,
                detach=False,
                stream=False
            )
            
            # 清理腳本
            if os.path.exists(host_path):
                os.remove(host_path)
            
            output = output_bytes.decode('utf-8', errors='replace')
            completed_at = datetime.now(timezone.utc)
            
            # === 步驟 3：驗證輸出參數 ===
            output_validation_status = "NOT_VALIDATED"
            output_validation_error = None
            output_json = None
            
            if skill.output_schema:
                is_valid, error_msg, parsed_json = OutputValidator.validate(output, skill.output_schema)
                output_json = parsed_json
                if not is_valid:
                    output_validation_status = "OUTPUT_INVALID"
                    output_validation_error = error_msg
                else:
                    output_validation_status = "VALIDATED"
            
            # === 步驟 4：記錄執行到 execution graph ===
            execution_duration = int((completed_at - started_at).total_seconds() * 1000)
            self._record_skill_execution_artifact(
                skill=skill,
                attack_vector_id=attack_vector_id,
                args_string=args_string,
                input_json=input_json,
                status="SUCCESS" if exit_code == 0 else "FAILED",
                exit_code=exit_code,
                output=output,
                output_json=output_json,
                validation_status=output_validation_status,
                validation_error=output_validation_error,
                execution_duration_ms=execution_duration,
            )
            
            # === 步驟 5：回傳結果 ===
            result = f"Executed Skill: {name} (Usage Count now {skill.usage_count})\n"
            result += f"Execution Environment: Kali Docker Sandbox (c2_kali_sandbox)\n"
            result += f"Return Code: {exit_code}\n"
            result += f"Duration: {execution_duration}ms\n"
            
            if input_validation_status != "NOT_VALIDATED":
                result += f"Input Validation: {input_validation_status}\n"
            
            if output_validation_status != "NOT_VALIDATED":
                result += f"Output Validation: {output_validation_status}\n"
                if output_validation_error:
                    result += f"Output Validation Error: {output_validation_error}\n"
            
            result += f"\n--- OUTPUT ---\n{output}\n"
            
            # 如果輸出驗證失敗，記錄失敗信息
            if output_validation_status == "OUTPUT_INVALID":
                skill.last_failure_reason = output_validation_error
                skill.save(update_fields=["last_failure_reason"])
            else:
                # 如果驗證成功，更新 last_verified_at
                skill.last_verified_at = completed_at
                skill.save(update_fields=["last_verified_at"])
                
            return result
            
        except docker.errors.NotFound:
            if 'host_path' in locals() and os.path.exists(host_path):
                os.remove(host_path)
            
            self._record_skill_execution_artifact(
                skill=skill,
                attack_vector_id=attack_vector_id,
                args_string=args_string,
                input_json=input_json,
                status="FAILED",
                error_message="Sandbox 容器未找到 (c2_kali_sandbox)",
                validation_status=input_validation_status,
                validation_error=input_validation_error,
            )
            
            return "錯誤：找不到 Sandbox 容器 (c2_kali_sandbox)。請手動啟動 sandbox。"
        
        except Exception as e:
            if 'host_path' in locals() and os.path.exists(host_path):
                os.remove(host_path)
            
            self._record_skill_execution_artifact(
                skill=skill,
                attack_vector_id=attack_vector_id,
                args_string=args_string,
                input_json=input_json,
                status="FAILED",
                error_message=str(e),
                validation_status=input_validation_status,
                validation_error=input_validation_error,
            )
            
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
    
    # === 輔助方法 ===
    
    def _record_skill_execution_artifact(
        self,
        *,
        skill,
        attack_vector_id: int | None = None,
        args_string: str = "",
        input_json: dict | None = None,
        status: str = "SUCCESS",
        exit_code: int | None = None,
        output: str = "",
        output_json: dict | None = None,
        validation_status: str = "NOT_VALIDATED",
        validation_error: str | None = None,
        execution_duration_ms: int | None = None,
        error_message: str | None = None,
    ):
        """Record skill execution in the graph-native execution log."""
        try:
            from apps.core.models import ExecutionGraph, ExecutionNode
            from apps.core.services import ExecutionService

            graph = getattr(self, "_execution_graph", None)
            node = getattr(self, "_current_execution_node", None)
            if graph is None:
                graph_id = getattr(self, "_current_execution_graph_id", None)
                graph = ExecutionGraph.objects.filter(id=graph_id).first() if graph_id else None
            if node is None:
                node_id = getattr(self, "_current_execution_node_id", None)
                node = ExecutionNode.objects.filter(id=node_id).first() if node_id else None
            if graph is None:
                return None

            payload = {
                "skill_id": skill.id,
                "skill_name": skill.name,
                "attack_vector_id": attack_vector_id,
                "args_string": args_string,
                "input_json": input_json,
                "status": status,
                "exit_code": exit_code,
                "output_json": output_json,
                "validation_status": validation_status,
                "validation_error": validation_error,
                "execution_duration_ms": execution_duration_ms,
                "error_message": error_message,
            }
            event = ExecutionService.emit_event(
                graph=graph,
                node=node,
                event_type="skill_execution_finished" if status == "SUCCESS" else "skill_execution_error",
                status="success" if status == "SUCCESS" else "failed",
                content=f"Executed skill: {skill.name} (exit={exit_code})" if not error_message else error_message,
                payload=payload,
            )
            artifact = ExecutionService.attach_artifact(
                graph=graph,
                node=node,
                artifact_type="skill_execution",
                name=f"Skill execution: {skill.name}"[:255],
                content=output or error_message or "",
                data=payload,
            )
            return event, artifact
        except Exception as exc:
            logger.warning("Failed to record skill execution artifact: %s", exc)
            return None
    
    @method_tool
    def promote_successful_script(
        self,
        script_execution_id: int,
        skill_name: str,
        tags: list = None,
        description: str = None,
        force: bool = False
    ) -> str:
        """
        [Skill System] 舊版腳本執行記錄升級入口已停用。
        
        腳本執行記錄已改存 ExecutionArtifact。請根據 skill_execution artifact
        直接建立或更新 SkillTemplate。
        
        升級規則：
        1. 必須是 SUCCESS 狀態
        2. 最好通過了輸出驗證（VALIDATED）
        3. 系統會自動生成 instructions 和 input/output schema
        
        Args:
            script_execution_id: 舊版腳本執行記錄 ID（已停用）
            skill_name: 新技能的名稱（kebab-case，如 'django-csrf-bypass'）
            tags: 技能標籤列表（如 ["django", "csrf", "bypass"]）
            description: 技能描述（如果 None，自動生成）
            force: 強制升級（即使未通過驗證）
        
        Returns:
            升級結果訊息
        """
        from apps.core.script_upgrader import promote_to_skill
        
        if tags is None:
            tags = []
        
        try:
            is_success, message = promote_to_skill(
                script_execution_id=script_execution_id,
                skill_name=skill_name,
                tags=tags,
                description=description,
                force=force
            )
            
            if is_success:
                return f"[SUCCESS] {message}"
            else:
                return f"[ERROR] {message}"
        
        except Exception as e:
            return f"[ERROR] 升級失敗: {str(e)}"
    
    @method_tool
    def mark_skill_as_robust(self, skill_name: str, verified: bool = True) -> str:
        """
        [Skill System] 將技能標記為 ROBUST（已充分驗證，無需進一步測試）。
        
        ROBUST 技能具有以下特性：
        - 已多次驗證，輸入輸出穩定
        - 不允許任意修改（修改會自動遞增版本）
        - 在搜索時優先排序
        
        Args:
            skill_name: 技能名稱
            verified: True 表示標記為 ROBUST，False 表示重新回到 TESTING 狀態
        
        Returns:
            操作結果訊息
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        from django.utils import timezone
        
        try:
            skill = SkillTemplate.objects.get(name=skill_name)
            skill.is_robust = verified
            if verified:
                skill.last_verified_at = timezone.now()
            skill.save(update_fields=["is_robust", "last_verified_at"])
            
            status = "ROBUST" if verified else "TESTING"
            return f"[SUCCESS] Skill '{skill_name}' marked as {status}"
        except SkillTemplate.DoesNotExist:
            return f"[ERROR] Skill '{skill_name}' not found"
        except Exception as e:
            return f"[ERROR] Failed to update skill: {str(e)}"
    
    @method_tool
    def list_ready_for_promotion(self) -> str:
        """
        [Skill System] 列出所有可以升級到 SkillTemplate 的成功腳本執行。
        
        條件：
        - 必須是 SUCCESS 狀態
        - 最好已通過輸出驗證
        - 未關聯到任何 SkillTemplate
        
        Returns:
            可升級腳本的列表
        """
        from apps.core.script_upgrader import get_scripts_ready_for_promotion
        
        scripts = get_scripts_ready_for_promotion()
        
        if not scripts:
            return "No scripts ready for promotion."
        
        result = [f"Found {len(scripts)} scripts ready for promotion:\n"]
        for script in scripts[:10]:  # 最多顯示 10 個
            result.append(
                f"- ID: {script.id}\n"
                f"  Language: {script.script_language}\n"
                f"  Status: {script.status}\n"
                f"  Validation: {script.validation_status}\n"
                f"  Created: {script.started_at.isoformat()}"
            )
        
        return "\n".join(result)
