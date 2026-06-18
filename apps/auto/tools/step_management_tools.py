import logging
from apps.ai_assistant import method_tool

logger = logging.getLogger(__name__)


class StepManagementMixin:
    """
    Execution workflow tools mixin.
    Provides tools for creating, querying, and updating execution graph planning state.
    """

    def _get_current_execution_context(self):
        from apps.core.models import ExecutionGraph, ExecutionNode

        graph = getattr(self, "_execution_graph", None)
        node = getattr(self, "_current_execution_node", None)
        if graph is None:
            graph_id = getattr(self, "_current_execution_graph_id", None)
            graph = ExecutionGraph.objects.filter(id=graph_id).first() if graph_id else None
        if node is None:
            node_id = getattr(self, "_current_execution_node_id", None)
            node = ExecutionNode.objects.filter(id=node_id).first() if node_id else None
        return graph, node

    @method_tool
    def update_overview_status(self, overview_id: int = None, new_status: str = None, new_summary: str = None, new_knowledge: dict = None, new_plan: dict = None, new_risk_score: int = None) -> str:
        """
        更新目標 Overview（專案概覽）的多個欄位。可同時更新以下任意組合：
        - status: 狀態轉換 ('PLANNING' → 'EXECUTING' → 'COMPLETED' → 'STALLED')。
        - summary: 當前目標的文字筆記/總結 (自由文字)。
        - knowledge: 威脅情報與知識 (JSON dict)。
        - plan: 攻擊藍圖 (JSON dict)。
        - risk_score: 風險評分 (0-100)。
        
        Args:
            overview_id: (Optional) The ID of the Overview. Automatically injected if session is bound.
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

            valid_statuses = ['PLANNING', 'EXECUTING', 'COMPLETED', 'STALLED', 'NEEDS_GUIDANCE']
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
    def update_step_note(
        self,
        step_id: int,
        summary: str | None = None,
        details: str | None = None,
        ai_thoughts: str | None = None,
        append: bool = False,
    ) -> str:
        """Record a human-facing note on the current execution graph.

        Intended workflow:
        - `summary` is a short human-friendly note shown in execution previews.
        - `details` and `ai_thoughts` can contain longer execution trace / reasoning.
        - If `append=True`, the provided text will be appended.
        """
        try:
            from apps.core.models import ExecutionNode
            from apps.core.services import ExecutionService

            graph, current_node = self._get_current_execution_context()
            node = ExecutionNode.objects.filter(id=step_id).first() if step_id else current_node
            if graph is None and node is not None:
                graph = node.graph
            if graph is None:
                return "CRITICAL_FAILURE: no active ExecutionGraph found."

            note_parts = [value for value in [summary, details, ai_thoughts] if value]
            note_content = "\n\n".join(note_parts)
            event = ExecutionService.emit_event(
                graph=graph,
                node=node,
                event_type="execution_note_recorded",
                status=getattr(node, "status", None),
                content=summary or details or ai_thoughts or "Execution note recorded",
                payload={
                    "execution_node_id_param": step_id,
                    "summary": summary,
                    "details": details,
                    "ai_thoughts": ai_thoughts,
                    "append": append,
                },
            )
            artifact = ExecutionService.attach_artifact(
                graph=graph,
                node=node,
                artifact_type="execution_note",
                name=(summary or "Execution Note")[:255],
                content=note_content,
                data={"execution_node_id_param": step_id, "append": append},
            )
            return f"✅ ExecutionEvent#{event.id} / ExecutionArtifact#{artifact.id} recorded."
        except Exception as e:
            logger.error(f"update_step_note failed for execution_node_id={step_id}: {e}")
            return f"記錄 execution note 失敗: {e}"

    @method_tool
    def query_steps(self, overview_id: int = None, status_filter: str = None, limit: int = 20) -> str:
        """
        查詢指定 Overview 關聯 thread 下的 execution graph/node 詳細狀態與內容。
        可以按狀態過濾 (e.g. 只看 COMPLETED 或 FAILED)。
        回傳每個 ExecutionNode 的 ID、狀態與最新事件。

        Args:
            overview_id: (Optional) 要查詢的 Overview ID。自動注入。
            status_filter: (選填) 過濾 graph 狀態 ('RUNNING', 'WAITING', 'SUCCEEDED', 'FAILED')。
            limit: (選填) 最大回傳數量，預設 20。
        """
        try:
            from apps.core.models import ExecutionGraph, Overview

            if not Overview.objects.filter(id=overview_id).exists():
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist."
            overview = Overview.objects.get(id=overview_id)

            thread_ids = [value for value in [overview.thread_id, overview.parent_thread_id] if value]
            qs = ExecutionGraph.objects.filter(thread_id__in=thread_ids).prefetch_related("nodes", "events") if thread_ids else ExecutionGraph.objects.none()
            if status_filter:
                qs = qs.filter(status=status_filter)

            graphs = list(qs.order_by("-started_at")[:limit])
            if not graphs:
                return f"Overview#{overview_id} 下沒有找到符合條件的 ExecutionGraph。"

            lines = [f"=== Executions for Overview#{overview_id} (顯示 {len(graphs)} 筆) ==="]
            for graph in graphs:
                nodes = list(graph.nodes.order_by("sequence")[:10])
                latest_event = graph.events.order_by("-sequence").first()
                lines.append(
                    f"- ExecutionGraph[{graph.id}] Status:{graph.status} | Started:{graph.started_at.strftime('%m-%d %H:%M')} "
                    f"| Nodes:{len(nodes)} | Title:{graph.title or graph.assistant_id}"
                )
                for node in nodes:
                    lines.append(f"  - Node[{node.id}] {node.name} Status:{node.status} Kind:{node.kind}")
                if latest_event:
                    lines.append(f"  LatestEvent[{latest_event.sequence}] {latest_event.event_type}: {latest_event.content[:200]}")

            lines.append("=== END ===")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"query_steps failed for overview {overview_id}: {e}")
            return f"查詢 executions 失敗: {e}"

    @method_tool
    def create_step(
        self,
        overview_id: int = None,
        tool_name: str = None,
        command_name: str = None,
        command_template_str: str = None,
        description: str = "",
        asset_fk_field: str = None,
        asset_fk_value_id: int = None,
        parent_step_id: int = None,
        note: str = None,
        ai_thoughts: str = None,
    ) -> str:
        """
        [Workflow] 建立一個 execution planning artifact 與關聯的攻擊向量。
        這會同步建立 ExecutionArtifact、AttackVector 以及 CommandTemplate。

        Args:
            overview_id: (Optional) 關聯的 Overview ID。自動注入。
            command_name: 命令的簡稱。
            command_template_str: 要執行的 CLI 命令（例如 'nmap -sV -p 80 {{ip}}'）。
            description: 這個步驟的說明與目的。
            asset_fk_field: 關聯的資產類型 ('ip', 'subdomain', 或 'url_result')。
            asset_fk_value_id: 關聯的資產主鍵 ID。
            parent_step_id: (Optional) 父 ExecutionNode ID。
            tool_name: (Optional) 使用的工具名稱 (nmap, nuclei 等)。
            note: (Optional) AI寫給人類看的進度筆記。
            ai_thoughts: (Optional) AI內部推理過程筆記。
        """
        try:
            from apps.core.models import AttackVector, Overview
            from apps.core.models.analyze.AttackVector import CommandTemplate
            from apps.core.services import ExecutionService
            
            # Overview ID 前置驗證：AI 幻覺防火牆
            if not Overview.objects.filter(id=overview_id).exists():
                logger.error(f"Hallucinated overview_id={overview_id}, does not exist in DB.")
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist. DO NOT RETRY. Use only the overview_id given in your starting context."
            
            graph, node = self._get_current_execution_context()
            if graph is not None:
                ExecutionService.emit_event(
                    graph=graph,
                    node=node,
                    event_type="execution_plan_item_created",
                    status="planned",
                    content=description or command_name or tool_name or "Execution plan item created",
                    payload={
                        "overview_id": overview_id,
                        "tool_name": tool_name,
                        "command_name": command_name,
                        "command": command_template_str,
                        "asset_fk_field": asset_fk_field,
                        "asset_fk_value_id": asset_fk_value_id,
                        "parent_execution_node_id_param": parent_step_id,
                    },
                )
                artifact = ExecutionService.attach_artifact(
                    graph=graph,
                    node=node,
                    artifact_type="execution_plan_item",
                    name=(command_name or tool_name or "Execution Plan Item")[:255],
                    content=note or description or command_template_str or "",
                    data={
                        "overview_id": overview_id,
                        "tool_name": tool_name,
                        "command_name": command_name,
                        "command": command_template_str,
                        "ai_thoughts": ai_thoughts,
                    },
                )
            else:
                artifact = None
            
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
                        logger.warning(f"Hallucinated asset {asset_fk_field}_id={asset_fk_value_id}. Returning CRITICAL_FAILURE.")
                        return f"CRITICAL_FAILURE: asset {asset_fk_field}_id={asset_fk_value_id} does not exist in the database. Use ONLY IDs from your starting context. DO NOT RETRY with the same ID."

            vector = AttackVector.objects.create(
                overview_id=overview_id,
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
            
            return f"成功建立 ExecutionArtifact#{getattr(artifact, 'id', 'N/A')}, AttackVector#{vector.id}, 與 CommandTemplate#{cmd.id}！"
        except Exception as e:
            logger.error(f"Failed to create step: {e}")
            return f"建立 execution plan item 時發生錯誤: {e}"

    @method_tool
    def update_step_status(
        self,
        step_id: int,
        status: str,
        execution_output: str = None,
    ) -> str:
        """
        更新指定 ExecutionNode 的執行狀態。
        
        **AI 使用規則 (MANDATORY WORKFLOW)**:
        - 在呼叫任何掃描 API 工具之前，先確認目前 ExecutionNode 為 RUNNING。
        - 如果工具是非同步的，呼叫後設為 WAITING。
        - 如果工具立即返回成功結果，設為 SUCCEEDED。
        - 如果工具返回 CRITICAL_FAILURE，設為 FAILED 並附上錯誤輸出。
        
        Valid status values: PENDING, RUNNING, SUCCEEDED, FAILED, WAITING, CANCELLED, SKIPPED, BLOCKED

        Args:
            step_id: 要更新的 ExecutionNode ID（保留舊參數名以相容工具 schema）。
            status: 新狀態 (RUNNING / SUCCEEDED / FAILED / WAITING / CANCELLED / SKIPPED / BLOCKED)。
            execution_output: (Optional) 執行結果摘要或錯誤訊息。
        """
        try:
            from apps.core.models import ExecutionNode
            from apps.core.services import ExecutionService

            node = ExecutionNode.objects.filter(id=step_id).first()
            if not node:
                return f"CRITICAL_FAILURE: ExecutionNode#{step_id} not found."

            status_map = {
                "PENDING": ExecutionNode.Status.PENDING,
                "RUNNING": ExecutionNode.Status.RUNNING,
                "COMPLETED": ExecutionNode.Status.SUCCEEDED,
                "FAILED": ExecutionNode.Status.FAILED,
                "WAITING_FOR_ASYNC": ExecutionNode.Status.WAITING,
                "ENDED": ExecutionNode.Status.SUCCEEDED,
                "SUCCEEDED": ExecutionNode.Status.SUCCEEDED,
                "WAITING": ExecutionNode.Status.WAITING,
                "CANCELLED": ExecutionNode.Status.CANCELLED,
                "SKIPPED": ExecutionNode.Status.SKIPPED,
                "BLOCKED": ExecutionNode.Status.BLOCKED,
            }
            normalized = status_map.get(status)
            if normalized is None:
                return f"無效的 status 值: '{status}'。請使用: {list(status_map.keys())}"

            if normalized == ExecutionNode.Status.SUCCEEDED:
                ExecutionService.complete_node(node, output={"preview": (execution_output or "")[:4000]}, content=execution_output or status)
            elif normalized == ExecutionNode.Status.FAILED:
                ExecutionService.fail_node(node, error={"message": execution_output or ""}, content=execution_output or status)
            elif normalized == ExecutionNode.Status.WAITING:
                ExecutionService.wait_node(node, wait_reason="MANUAL_STATUS_UPDATE", content=execution_output or status)
            else:
                node.status = normalized
                node.save(update_fields=["status", "updated_at"])
                ExecutionService.emit_event(
                    graph=node.graph,
                    node=node,
                    event_type="node_status_updated",
                    status=normalized,
                    content=execution_output or status,
                    payload={"execution_node_id_param": step_id, "requested_status": status},
                )

            return f"ExecutionNode#{step_id} 狀態已更新為 {normalized}。"
        except Exception as e:
            return f"更新 ExecutionNode#{step_id} 狀態失敗: {e}"

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
            observation_prompt: 驗證標準，描述成功條件（如: 'nmap 輸出中出現漏洞 CVE'）。
            confidence_threshold: 信心門檻 (預設 75)。
            auto_create_vulnerability: 驗證通過時是否自動回報漏洞 (預設 False)。
        """
        try:
            from apps.core.models.analyze.Verification import Verification
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
    def get_exhausted_attack_vectors(
        self,
        overview_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> str:
        """
        取得此 Overview 中所有狀態為 EXHAUSTED (失敗) 或 MITIGATED (已緩解) 的攻擊向量（支持分页）。

        AI 在規劃新行動前應先呼叫此工具，避免重複使用已經失敗的攻擊向量！

        Args:
            overview_id: Overview ID
            limit: 返回数量上限（默认 50，最大 100）
            offset: 分页偏移（默认 0）

        Returns:
            格式化的失败攻击向量列表
        """
        try:
            from apps.core.models import AttackVector

            query = AttackVector.objects.filter(
                overview_id=overview_id,
                status__in=["EXHAUSTED", "MITIGATED"]
            )

            # 限制最大值
            limit = min(limit, 100)

            # 获取总数
            total = query.count()

            if total == 0:
                return "目前沒有已失敗或無效的攻擊向量。可自由進行測試。"

            # 获取分页数据
            vectors = query.order_by('-created_at')[offset:offset+limit]

            summary = f"Exhausted Attack Vectors (showing {len(vectors)}/{total}):\n\n"

            for v in vectors:
                cmds = list(v.command_templates.values_list('command', flat=True))
                summary += f"[{v.id}] {v.name} - {v.status}\n"
                summary += f"  Commands tried: {cmds}\n\n"

            if total > offset + limit:
                summary += f"\n💡 Tip: Use offset={offset+limit} to see next {limit} vectors\n"

            return summary
        except Exception as e:
            return f"獲取失敗的攻擊向量時發生錯誤: {e}"

    @method_tool
    def notify_caller_agent(self, overview_id: int, message: str) -> str:
        """
        [Layered Intelligence] 向發起任務的父層 Agent (HackerAssistant) 報告關鍵進度或最終結果。
        
        ⚠️ 強烈建議：
        1. 當你完成了一個階段 (Phase) 的任務時使用。
        2. 當你發現了高嚴重度漏洞 (SQLi, RCE, Data Leak) 時使用。
        3. 當你決定結束整個測試流程 (COMPLETED) 時使用。
        
        這會讓你的父層 Agent 能夠即時感知進度，並在需要時向使用者進行總結報告。

        Args:
            overview_id: 當前 Overview 的 ID。
            message: 你要報告的內容（包含具體發現、數據、與下一步建議）。
        """
        try:
            from apps.core.models import Overview
            from apps.ai_assistant.helpers.use_cases import create_message
            from django.contrib.auth import get_user_model

            overview = Overview.objects.filter(id=overview_id).first()
            if not overview:
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist."

            if not overview.parent_thread_id:
                return "ℹ️ 此任務沒有關聯的父層 Thread，訊息已記錄在當前日誌中，但未發送至父層。"

            User = get_user_model()
            system_user = User.objects.filter(is_superuser=True).first()

            # 發送訊息至父層 Thread
            create_message(
                assistant_id="hacker_assistant_agent",
                thread_id=overview.parent_thread_id,
                user=system_user,
                content=(
                    f"📢 **Intelligence Report from AutomationAgent (Overview #{overview_id})**\n\n"
                    f"{message}\n\n"
                    f"---\n"
                    f"*Reported from autonomous execution layer.*"
                )
            )

            return f"✅ 成功將報告發送至父層 Thread (ID: {overview.parent_thread_id})。"
        except Exception as e:
            logger.error(f"notify_caller_agent failed: {e}")
            return f"報告發送失敗: {e}"

    @method_tool
    def record_vulnerability(
        self,
        overview_id: int = None,
        name: str = "",
        severity: str = "info",
        matched_at: str = "",
        description: str = "",
        vector_id: int = None,
        extracted_results: dict = None,
        request_raw: str = "",
        response_raw: str = "",
        tool_source: str = "automation-agent"
    ) -> str:
        """
        [Final Achievement] 當 AI 成功驗證並確認一個漏洞時，呼叫此工具將其記錄到資料庫。
        這會將漏洞與當前的 Overview 以及發現它的 AttackVector 關聯起來。

        Args:
            overview_id: (Optional) 當前任務的 Overview ID。自動注入。
            name: 漏洞名稱（例如: "SQL Injection in Search Field"）。
            severity: 嚴重程度 ('critical', 'high', 'medium', 'low', 'info')。
            matched_at: 發現漏洞的具體位置（例如 URL 或 IP:PORT）。
            description: 漏洞的詳細描述與影響。
            vector_id: (選填) 關聯的攻擊向量 ID。
            extracted_results: (選填) 漏洞 Payload 或版本號等結構化數據。
            request_raw: (選填) 觸發漏洞的原始請求內容。
            response_raw: (選填) 包含漏洞證據的原始響應內容。
            tool_source: 來源工具，預設為 "automation-agent"。
        """
        try:
            from apps.core.models import Vulnerability, Overview, AttackVector
            
            overview = Overview.objects.filter(id=overview_id).first()
            if not overview:
                return f"ERROR: Overview#{overview_id} not found."

            vector = None
            if vector_id:
                vector = AttackVector.objects.filter(id=vector_id).first()

            # 建立漏洞記錄
            vuln = Vulnerability.objects.create(
                overview=overview,
                source_attack_vector=vector,
                name=name,
                severity=severity.lower(),
                matched_at=matched_at,
                description=description,
                extracted_results=extracted_results,
                request_raw=request_raw,
                response_raw=response_raw,
                tool_source=tool_source,
                template_id=name.lower().replace(" ", "-"), # 模擬 template_id
                status="confirmed"
            )

            logger.info(f"[Automation] Recorded confirmed vulnerability: {name} (ID: {vuln.id})")
            return f"✅ 已成功將漏洞 '{name}' 記錄至資料庫 (ID: {vuln.id})，狀態標記為 'confirmed'。"
        except Exception as e:
            logger.error(f"record_vulnerability failed: {e}")
            return f"記錄漏洞時發生錯誤: {e}"
