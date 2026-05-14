import logging
from django_ai_assistant import method_tool

logger = logging.getLogger(__name__)


class StepManagementMixin:
    """
    Step Management & Workflow Tools Mixin
    Provides tools for creating, querying, and updating steps in the automated pentesting workflow.
    """

    @method_tool
    def update_overview_status(self, overview_id: int, new_status: str = None, new_summary: str = None, new_knowledge: dict = None, new_plan: dict = None, new_risk_score: int = None) -> str:
        """
        更新目標 Overview（專案概覽）的多個欄位。可同時更新以下任意組合：
        - status: 狀態轉換 ('PLANNING' → 'EXECUTING' → 'COMPLETED' → 'STALLED')。
        - summary: 當前目標的文字筆記/總結 (自由文字)。
        - knowledge: 威脅情報與知識 (JSON dict)。
        - plan: 攻擊藍圖 (JSON dict)。
        - risk_score: 風險評分 (0-100)。
        
        Args:
            overview_id: The ID of the Overview.
            new_status: 新的狀態值 ('PLANNING', 'EXECUTING', 'COMPLETED', 'STALLED')。
            new_summary: 更新的文字筆記或總結。
            new_knowledge: A JSON dictionary representing discovered intelligence.
            new_plan: A JSON dictionary outlining the strategic attack plan.
            new_risk_score: 偵測到的風險評分 (0-100)。
        """
        try:
            from apps.core.models import Overview
            if not Overview.objects.filter(id=overview_id).exists():
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist. DO NOT RETRY. Use only IDs given in your starting context."
            overview = Overview.objects.get(id=overview_id)
            update_fields = []

            valid_statuses = ['PLANNING', 'EXECUTING', 'COMPLETED', 'STALLED']
            if new_status is not None:
                if new_status not in valid_statuses:
                    return f"CRITICAL_FAILURE: Invalid status '{new_status}'. Must be one of {valid_statuses}."
                overview.status = new_status
                update_fields.append('status')
            if new_summary is not None:
                overview.summary = new_summary
                update_fields.append('summary')
            if new_knowledge is not None:
                overview.knowledge = new_knowledge
                update_fields.append('knowledge')
            if new_plan is not None:
                overview.plan = new_plan
                update_fields.append('plan')
            if new_risk_score is not None:
                overview.risk_score = new_risk_score
                update_fields.append('risk_score')
            
            if update_fields:
                overview.save(update_fields=update_fields)
            return f"成功更新 Overview#{overview_id} 的 {', '.join(update_fields)}！"
        except Exception as e:
            logger.error(f"Failed to update Overview#{overview_id}: {e}")
            return f"更新 Overview 時發生錯誤: {e}"

    @method_tool
    def query_steps(self, overview_id: int, status_filter: str = None, limit: int = 20) -> str:
        """
        查詢指定 Overview 下的所有 Step 的詳細狀態與內容。
        可以按狀態過濾 (e.g. 只看 COMPLETED 或 FAILED)。
        回傳每個 Step 的 ID、狀態、關聯攻擊向量、筆記內容。

        Args:
            overview_id: 要查詢的 Overview ID。
            status_filter: (選填) 過濾狀態 ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'WAITING_FOR_ASYNC', 'ENDED')。
            limit: (選填) 最大回傳數量，預設 20。
        """
        try:
            from apps.core.models.analyze.Step import Step, StepNote
            from apps.core.models import Overview

            if not Overview.objects.filter(id=overview_id).exists():
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist."

            qs = Step.objects.filter(overview_id=overview_id).prefetch_related(
                'discovered_vectors', 'note_detail', 'content_blobs'
            ).order_by('-created_at')

            if status_filter:
                qs = qs.filter(status=status_filter)

            steps = qs[:limit]
            if not steps:
                return f"Overview#{overview_id} 下沒有找到符合條件的 Step。"

            lines = [f"=== Steps for Overview#{overview_id} (顯示 {len(steps)} 筆) ==="]
            for s in steps:
                # Attack Vector 資訊
                vectors = s.discovered_vectors.all()
                vector_info = ", ".join([f"{v.name}({v.id})" for v in vectors]) if vectors else "None"

                # StepNote 內容
                note_content = ""
                if hasattr(s, 'note_detail') and s.note_detail:
                    note_content = s.note_detail.content[:300] if s.note_detail.content else ""

                # ContentBlob 摘要
                blobs = s.content_blobs.all()
                blob_info = ""
                if blobs:
                    blob_info = " | Blobs: " + ", ".join(
                        [f"blob_id={b.id}({b.content_size}chars)" for b in blobs]
                    )

                lines.append(
                    f"- Step[{s.id}] Status:{s.status} | Created:{s.created_at.strftime('%m-%d %H:%M')} "
                    f"| Vectors:{vector_info}{blob_info}"
                    f"\n  Note: {note_content[:200]}{'...' if len(note_content) > 200 else ''}"
                )

            lines.append("=== END ===")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"query_steps failed for overview {overview_id}: {e}")
            return f"查詢 Steps 失敗: {e}"

    @method_tool
    def create_step(
        self, 
        overview_id: int, 
        command_name: str,
        command_template_str: str, 
        description: str,
        asset_fk_field: str,
        asset_fk_value_id: int,
        parent_step_id: int = None,
        tool_name: str = None,
        note: str = None,
        ai_thoughts: str = None
    ) -> str:
        """
        為自動化滲透測試流程建立一個新的執行步驟（Step）。
        這會同步建立關聯的 StepNote、AttackVector 以及 CommandTemplate。

        Args:
            overview_id: 關聯的 Overview ID。
            command_name: 命令的簡稱。
            command_template_str: 要執行的 CLI 命令（例如 'nmap -sV -p 80 {{ip}}'）。
            description: 這個步驟的說明與目的。
            asset_fk_field: 關聯的資產類型 ('ip', 'subdomain', 或 'url_result')。
            asset_fk_value_id: 關聯的資產主鍵 ID。
            parent_step_id: (Optional) 父步驟 ID。
            tool_name: (Optional) 使用的工具名稱 (nmap, nuclei 等)。
            note: (Optional) AI寫給人類看的進度筆記。
            ai_thoughts: (Optional) AI內部推理過程筆記。
        """
        try:
            from apps.core.models import Step, AttackVector, Overview
            from apps.core.models.analyze.Step import StepNote
            from apps.core.models.analyze.AttackVector import CommandTemplate
            
            # Overview ID 前置驗證：AI 幻覺防火牆
            if not Overview.objects.filter(id=overview_id).exists():
                logger.error(f"Hallucinated overview_id={overview_id}, does not exist in DB.")
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist. DO NOT RETRY. Use only the overview_id given in your starting context."
            
            if parent_step_id and not Step.objects.filter(id=parent_step_id).exists():
                logger.warning(f"Invalid parent_step_id {parent_step_id}, setting to None")
                parent_step_id = None

            step = Step.objects.create(
                overview_id=overview_id,
                parent_step_id=parent_step_id,
                status="PENDING"
            )
            
            if asset_fk_field and asset_fk_value_id:
                # 資產 ID 前置驗證：在寫入 M2M 前先確認資產存在
                _asset_model_map = {
                    "ip": ("apps.core.models", "IP"),
                    "subdomain": ("apps.core.models", "Subdomain"),
                    "url_result": ("apps.core.models.url_assets", "URLResult"),
                }
                _model_info = _asset_model_map.get(asset_fk_field)
                if _model_info:
                    import importlib
                    _mod = importlib.import_module(_model_info[0])
                    _AssetModel = getattr(_mod, _model_info[1])
                    if not _AssetModel.objects.filter(id=asset_fk_value_id).exists():
                        logger.warning(f"Hallucinated asset {asset_fk_field}_id={asset_fk_value_id}. Rolling back step and returning CRITICAL_FAILURE.")
                        step.delete()
                        return f"CRITICAL_FAILURE: asset {asset_fk_field}_id={asset_fk_value_id} does not exist in the database. Use ONLY IDs from your starting context. DO NOT RETRY with the same ID."

                m2m_mgr = getattr(step, asset_fk_field, None)
                if m2m_mgr is not None:
                    try:
                        m2m_mgr.add(asset_fk_value_id)
                    except Exception as m2m_err:
                        logger.warning(f"Invalid asset {asset_fk_field}={asset_fk_value_id}, ignored: {m2m_err}")
            
            if note or ai_thoughts:
                StepNote.objects.create(step=step, content=note, ai_thoughts=ai_thoughts)
            
            vector = AttackVector.objects.create(
                overview_id=overview_id,
                discovery_step=step,
                name=f"Attack Vector via {tool_name or 'Tool'}",
                description=description,
                status="IDENTIFIED"
            )
            
            cmd = CommandTemplate.objects.create(
                attack_vector=vector,
                name=command_name,
                description=description,
                tool_name=tool_name,
                command=command_template_str
            )
            
            return f"成功建立新的 Step#{step.id}, AttackVector#{vector.id}, 與 CommandTemplate#{cmd.id}！"
        except Exception as e:
            logger.error(f"Failed to create step: {e}")
            return f"建立 Step 時發生錯誤: {e}"

    @method_tool
    def update_step_status(
        self,
        step_id: int,
        status: str,
        execution_output: str = None,
    ) -> str:
        """
        更新指定 Step 的執行狀態。
        
        **AI 使用規則 (MANDATORY WORKFLOW)**:
        - 在呼叫任何掃描 API 工具「之前」，先呼叫此工具將 Step 設為 RUNNING。
        - 如果工具是非同步的 (會有 callback)，呼叫後設為 WAITING_FOR_ASYNC。
        - 如果工具立即返回成功結果，設為 COMPLETED。
        - 如果工具返回 CRITICAL_FAILURE，設為 FAILED 並附上錯誤輸出。
        
        Valid status values: PENDING, RUNNING, COMPLETED, FAILED, WAITING_FOR_ASYNC, ENDED

        Args:
            step_id: 要更新的 Step ID。
            status: 新狀態 (RUNNING / COMPLETED / FAILED / WAITING_FOR_ASYNC / ENDED)。
            execution_output: (Optional) 執行結果摘要或錯誤訊息。
        """
        try:
            from apps.core.models import Step
            from apps.core.models.analyze.Step import StepNote
            from django.utils import timezone
            
            step = Step.objects.get(id=step_id)
            valid_statuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED", "WAITING_FOR_ASYNC", "ENDED"]
            if status not in valid_statuses:
                return f"無效的 status 值: '{status}'。請使用: {valid_statuses}"
            
            step.status = status
            
            # 📍 P0 FIX: 當 Step 完成或失敗時，設置 completed_at 時間戳
            if status in ["COMPLETED", "FAILED", "ENDED"]:
                step.completed_at = timezone.now()
            
            step.save(update_fields=["status", "completed_at"])
            
            # 附加執行輸出到 StepNote
            if execution_output:
                note, _ = StepNote.objects.get_or_create(step=step)
                note.content = (note.content or "") + f"\n[{status}] {execution_output}"
                note.save(update_fields=["content"])
            
            return f"Step#{step_id} 狀態已更新為 {status}。"
        except Exception as e:
            return f"更新 Step#{step_id} 狀態失敗: {e}"

    @method_tool
    def create_verification(
        self,
        attack_vector_id: int,
        observation_prompt: str,
        confidence_threshold: int = 75,
        auto_create_vulnerability: bool = False
    ) -> str:
        """
        為指定的 AttackVector 建立 AI 驗證規則（Verification）。
        設定成功標準，系統執行後將依此評估該向量是否成功並建立 Vulnerability。
        
        Args:
            attack_vector_id: 目標 AttackVector 的 ID。
            observation_prompt: 驗證標準，描述「這個步驟的成功標準」(如: 'nmap 輸出中出現漏洞 CVE')。
            confidence_threshold: 信心門檻 (預設 75)。
            auto_create_vulnerability: 驗證通過時是否自動回報漏洞 (預設 False)。
        """
        try:
            from apps.core.models.analyze.Step import Verification
            v = Verification.objects.create(
                attack_vector_id=attack_vector_id,
                observation_prompt=observation_prompt,
                confidence_threshold=confidence_threshold,
                auto_create_vulnerability=auto_create_vulnerability,
                verdict="PENDING"
            )
            return f"成功為 AttackVector#{attack_vector_id} 建立 Verification#{v.id}！"
        except Exception as e:
            return f"建立 Verification 發生錯誤: {e}"

    @method_tool
    def get_exhausted_attack_vectors(self, overview_id: int) -> str:
        """
        取得此 Overview 中所有狀態為 EXHAUSTED (失敗) 或 MITIGATED (已緩解) 的攻擊向量。
        AI 在規劃 Step 前應先呼叫此工具，避免重複使用已經失敗的攻擊向量！
        """
        try:
            from apps.core.models import AttackVector
            vectors = AttackVector.objects.filter(
                overview_id=overview_id, 
                status__in=["EXHAUSTED", "MITIGATED"]
            )
            if not vectors.exists():
                return "目前沒有已失敗或無效的攻擊向量。可自由進行測試。"
            
            res = []
            for v in vectors:
                cmds = list(v.command_templates.values_list('command', flat=True))
                res.append(f"Vector ID: {v.id} | Name: {v.name} | Commands tried: {cmds} | Status: {v.status}")
            return "\n".join(res)
        except Exception as e:
            return f"獲取失敗的攻擊向量時發生錯誤: {e}"
