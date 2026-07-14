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
    def search_skills(self, query: str, skill_type: str = None) -> str:
        """
        [Skill System] 透過關鍵字搜尋全域通用的技能清單 (Skill Templates)。
        這能幫助你發現在過去任務中寫好的自動化繞過腳本 (如 CSRF token 獲取工具等)，
        或是文件型技能（技術指引、方法論）。

        Args:
            query: 搜尋關鍵字（比對 name / description / tags / short_description）
            skill_type: 篩選技能類型（script / documentation / hybrid），不指定則全部
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        from django.db.models import Q
        
        qs = SkillTemplate.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(tags__icontains=query) |
            Q(short_description__icontains=query)
        )
        if skill_type:
            qs = qs.filter(skill_type=skill_type)
        skills = qs.order_by('-is_robust', '-usage_count')[:10]
        
        if not skills.exists():
            type_hint = f" (skill_type={skill_type})" if skill_type else ""
            return f"找不到符合 '{query}'{type_hint} 的 Skill。"
            
        res = [f"Found {len(list(skills))} skills:"]
        for s in skills:
            robust_badge = " [ROBUST]" if s.is_robust else ""
            type_badge = f" [{s.skill_type}]" if s.skill_type != "script" else ""
            short = f" — {s.short_description}" if s.short_description else ""
            res.append(
                f"- Name: {s.name} v{s.version}{robust_badge}{type_badge}\n"
                f"  Tags: {s.tags}\n"
                f"  Usage Count: {s.usage_count}\n"
                f"  Description: {s.description}{short}"
            )
        return "\n".join(res)

    @method_tool
    def load_skill(self, name: str) -> str:
        """
        [Skill System] 載入指定名稱的 Skill 詳細內容。
        - script 型：顯示 instructions + input/output schema + script_content
        - documentation 型：顯示 detailed_overview（大篇幅技術指引）
        - hybrid 型：兩者皆顯示

        你在執行此技能前，必須先 Load 閱讀其內容了解具體執行方式。
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        try:
            skill = SkillTemplate.objects.get(name=name)
            
            msg = f"Skill Name: {skill.name} v{skill.version} [{skill.skill_type}]\n"
            msg += f"Tags: {skill.tags}\n"
            msg += f"Usage Count: {skill.usage_count}\n"
            msg += f"Is Robust: {skill.is_robust}\n"
            if skill.short_description:
                msg += f"Short: {skill.short_description}\n"
            
            # documentation / hybrid 型：顯示 detailed_overview
            if skill.skill_type in ("documentation", "hybrid") and skill.detailed_overview:
                overview = skill.detailed_overview
                # 若過長，提示 agent 可分頁讀取（目前直接完整回傳，超長時由 compress_tool_outputs 自動處理）
                msg += f"\n=== DETAILED OVERVIEW ===\n{overview}\n"
                if skill.skill_type == "documentation":
                    msg += (
                        "\n=== 使用方式 ===\n"
                        "這是 documentation 型技能（指引文件）。\n"
                        "呼叫 follow_skill_guidance(name='" + skill.name + "') 開始遵循此指引執行。\n"
                        "你應該用既有的偵察/檢測工具組合來實踐指引中的步驟。\n"
                    )
            
            # script / hybrid 型：顯示 schema 與 script_content
            if skill.skill_type in ("script", "hybrid"):
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
    def follow_skill_guidance(
        self,
        name: str,
        overview_id: int = None,
        context_note: str = "",
    ) -> str:
        """
        [Documentation Skill] 讀取文件型技能的指引，並自主遵循執行。
        適用於 skill_type=documentation 或 hybrid 的技能。

        與 execute_skill_script 不同：
        - execute_skill_script 在 sandbox 執行腳本（自動化）
        - follow_skill_guidance 把 detailed_overview 載入你的上下文，由你（agent）
          用既有的偵察/檢測工具組合來實踐指引中的步驟（半自動）

        使用流程：
        1. search_skills(query, skill_type='documentation') 找到相關指引
        2. load_skill(name) 閱讀 detailed_overview
        3. follow_skill_guidance(name) 正式開始遵循，系統會記錄遵循過程到 ExecutionArtifact

        Args:
            name: 技能名稱（kebab-case）
            overview_id: 當前 Overview ID（自動注入）
            context_note: 為什麼要遵循此技能（輔助記錄）
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        try:
            skill = SkillTemplate.objects.get(name=name)
            
            if skill.skill_type == "script":
                return (
                    f"Skill '{name}' 是 script 型技能，應使用 execute_skill_script 執行，\n"
                    f"而非 follow_skill_guidance。"
                )
            
            if not skill.detailed_overview:
                return f"Skill '{name}' 沒有 detailed_overview，無法遵循指引。"
            
            # 記錄遵循過程到 ExecutionArtifact
            resolved_ov = overview_id or getattr(self, '_agent_overview_id', None)
            try:
                from apps.core.services.execution_service import ExecutionService
                agent_id = getattr(self, 'id', 'unknown')
                ExecutionService.attach_artifact(
                    thread_id=getattr(getattr(self, '_thread', None), 'id', None),
                    assistant_id=agent_id,
                    artifact_type="skill_guidance_followed",
                    content=(
                        f"Agent 開始遵循 documentation 技能: {skill.name}\n"
                        f"Context: {context_note or '(無)'}\n"
                        f"Overview: {resolved_ov}\n"
                        f"Guidance length: {len(skill.detailed_overview)} chars"
                    ),
                    metadata={"skill_id": skill.id, "skill_name": skill.name, "skill_type": skill.skill_type},
                )
            except Exception as e:
                logger.warning(f"[follow_skill_guidance] Failed to record artifact: {e}")
            
            # 增加使用計數
            SkillTemplate.objects.filter(id=skill.id).update(usage_count=skill.usage_count + 1)
            
            return (
                f"✅ 已載入技能 '{skill.name}' 的指引並開始遵循。\n"
                f"系統已記錄此次遵循到 ExecutionArtifact。\n\n"
                f"=== GUIDANCE TO FOLLOW ===\n"
                f"{skill.detailed_overview}\n"
                f"=== END ===\n\n"
                f"現在請根據上述指引，使用你既有的偵察/檢測工具組合來實踐每個步驟。"
            )
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
        [Skill System] 創建一個新的技能並存入資料庫。

        ⚠️ 這是唯一允許創建 Skill 的工具。AI 不應直接撰寫 script_content，
        而是透過此工具，由系統生成符合規範的技能。

        系統會自動：
        1. 使用原始 input_schema / output_schema 呼叫 LLM 生成腳本主體 (script_body)
        2. 驗證 AST 語法並自動注入 Pydantic I/O Contract
        3. 確保技能符合全域規範並存入資料庫

        重要：input_schema 和 output_schema 會被原封不動地傳遞給資料庫，
        不經過 LLM 中繼，因此複雜的巢狀 JSON Schema 不會丟失。

        Args:
            name: 唯一 kebab-case 標識符，例如 'django-csrf-bypass'
            description: ≤ 500 字的技能摘要（供 RAG 檢索）
            instructions: ≤ 2000 字的使用指南（如何傳參、注意事項）
            task_description: 自然語言描述此腳本應該做什麼
            language: 'python' 或 'bash'
            tags: 標籤陣列，例如 ["django", "csrf", "bypass"]
            input_schema: 輸入參數的 JSON Schema（原封不動存入資料庫）
            output_schema: 輸出的預期 JSON Schema（原封不動存入資料庫）
        """
        from apps.auto.tools.skill_creator_agent import create_skill_from_spec

        if tags is None:
            tags = []

        # 直接呼叫 create_skill_from_spec，不經過 LLM 中繼跳接。
        # 這樣 input_schema / output_schema 會原封不動地傳遞給資料庫，
        # 避免複雜巢狀結構在 LLM tool call 過程中丟失或被簡化。
        try:
            result = create_skill_from_spec(
                name=name,
                description=description,
                instructions=instructions,
                task_description=task_description,
                input_schema=input_schema,
                output_schema=output_schema,
                language=language,
                tags=tags,
            )

            if result.get("ok"):
                action = result.get("action", "Saved")
                skill_id = result["skill_id"]
                script_body_preview = result.get("script_body", "")[:500]
                full_len = result.get("script_content_length", 0)

                # 記錄執行軌跡到 ExecutionArtifact（若可用）
                self._record_skill_creation_artifact(
                    skill_id=skill_id,
                    skill_name=name,
                    action=action,
                    input_schema=input_schema,
                    output_schema=output_schema,
                )

                return (
                    f"✅ **Success!** {action} skill '{name}' (ID: {skill_id})\n\n"
                    f"📝 **Script Body Preview**:\n```python\n{script_body_preview}...```\n\n"
                    f"🔧 **Assembled Script**: {full_len} chars (I/O Contract auto-injected)\n"
                    f"📊 **Schema Preserved**: input_schema={'yes' if input_schema else 'no'}, "
                    f"output_schema={'yes' if output_schema else 'no'}"
                )
            else:
                return f"❌ **Error**: {result.get('error', 'Unknown error')}"
        except Exception as e:
            logger.exception(f"Failed to create skill '{name}': {e}")
            return f"❌ **Exception**: {str(e)}"

    def _record_skill_creation_artifact(
        self,
        *,
        skill_id: int,
        skill_name: str,
        action: str,
        input_schema: dict | None = None,
        output_schema: dict | None = None,
    ):
        """Record skill creation event in the execution graph (best-effort)."""
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
                "skill_id": skill_id,
                "skill_name": skill_name,
                "action": action,
                "has_input_schema": bool(input_schema),
                "has_output_schema": bool(output_schema),
            }
            ExecutionService.emit_event(
                graph=graph,
                node=node,
                event_type="skill_created",
                status="success",
                content=f"{action} skill: {skill_name} (ID={skill_id})",
                payload=payload,
            )
        except Exception as exc:
            logger.debug("Failed to record skill creation artifact: %s", exc)
            return None

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
        input_json: dict = None,
        overview_id: int = None,
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
            overview_id: (Auto-injected) 當前 Overview ID，用來解析 workspace。
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
            raw_cmd = f"{runner} {sandbox_path} {io_args} {args_string}".strip()
            # 用 bwrap 隔離到 target 的 workspace（如果有 overview_id）
            target_id = self._resolve_target_id(overview_id) if hasattr(self, "_resolve_target_id") else None
            workspace = self._ensure_workspace(target_id) if (target_id and hasattr(self, "_ensure_workspace")) else None
            wrapped_cmd = self._wrap_command(raw_cmd, workspace) if hasattr(self, "_wrap_command") else raw_cmd
            exit_code, output_bytes = container.exec_run(
                cmd=["/bin/bash", "-c", wrapped_cmd],
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
        安裝是全系統的（所有 target 共用），不會被 workspace 隔離限制。
        pip install 不需要額外參數（環境已配置 PIP_BREAK_SYSTEM_PACKAGES=1）。
        
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
            cmd = f"pip3 install {package_name}"
            
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
