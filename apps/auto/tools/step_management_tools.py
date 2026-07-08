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
    def update_overview_status(self, overview_id: int = None, new_status: str = None, new_summary: str = None, new_knowledge: dict = None, new_risk_score: int = None) -> str:
        """
        更新目標 Overview（專案概覽）的多個欄位。可同時更新以下任意組合：
        - status: 狀態轉換 ('PLANNING' → 'EXECUTING' → 'COMPLETED' → 'STALLED')。
        - summary: 當前目標的文字筆記/總結 (自由文字)。
        - knowledge: 威脅情報與知識 (JSON dict)。
        - risk_score: 風險評分 (0-100)。

        ⚠️ 攻擊計劃 (Plan) 已改用 AttackPlan + Action DB 模型管理，不再透過此工具寫入。
        請使用 create_attack_plan / add_action / update_action 等專用工具管理計劃。

        Args:
            overview_id: (Optional) The ID of the Overview. Automatically injected if session is bound.
            new_status: 新的狀態值 ('PLANNING', 'EXECUTING', 'COMPLETED', 'STALLED')。
            new_summary: 更新的文字筆記或總結。
            new_knowledge: A JSON dictionary representing discovered intelligence.
            new_risk_score: 偵測到的風險評分 (0-100)。
        """
        try:
            from apps.core.models import Overview
            if not Overview.objects.filter(id=overview_id).exists():
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist. DO NOT RETRY. Use only IDs given in your starting context."
            overview = Overview.objects.get(id=overview_id)

            # ════════════════════════════════════════════════════════════
            # Thread Ownership Gate: 只有 Overview 的擁有者 thread 才能改狀態。
            # Sub-agent（非擁有者）呼叫時拒絕，防止殭屍 sub-agent 反覆把
            # COMPLETED 的 Overview 改回 EXECUTING 導致無限 spawn 循環。
            # ════════════════════════════════════════════════════════════
            current_thread_id = getattr(self, "_current_invoke_thread_id", None)
            if current_thread_id and overview.thread_id and current_thread_id != overview.thread_id:
                # 這是一個 sub-agent（非擁有者）試圖改不屬於它的 Overview
                return (
                    f"⚠️ Permission denied: Thread#{current_thread_id} is not the owner "
                    f"of Overview#{overview_id} (owner=Thread#{overview.thread_id}). "
                    f"Sub-agents cannot modify Overview status. "
                    f"If you have findings, use notify_caller_agent to report back."
                )

            update_fields = []

            valid_statuses = ['PLANNING', 'EXECUTING', 'COMPLETED', 'STALLED', 'NEEDS_GUIDANCE']
            if new_status is not None:
                if new_status not in valid_statuses:
                    return f"CRITICAL_FAILURE: Invalid status '{new_status}'. Must be one of {valid_statuses}."

                # ════════════════════════════════════════════════════════════
                # VerificationAgent Gate（PoC 審查）
                # 攔截 new_status == "COMPLETED" → 先過 LLM-as-judge 審查
                # ════════════════════════════════════════════════════════════
                if new_status == "COMPLETED":
                    from apps.auto.verification_service import VerificationService

                    verifier = VerificationService()
                    review = verifier.review_mission_completion(
                        overview_id=overview_id,
                        triggered_by="update_overview_status",
                        triggered_by_agent=getattr(self, "id", "unknown"),
                    )

                    if review.verdict == "REJECTED":
                        # 退回 EXECUTING + 注入駁回理由到 thread + wake agent
                        overview.status = "EXECUTING"
                        overview.save(update_fields=["status", "updated_at"])
                        self._inject_review_feedback(overview, review, verdict_label="REJECTED")
                        return (
                            f"⛔ VerificationAgent 駁回 COMPLETED（confidence={review.confidence_score}/100）。\n"
                            f"MissionReview#{review.id}\n"
                            f"分析：{review.reasoning}\n"
                            f"具體問題：{review.rejection_reasons}\n"
                            f"建議動作：{review.suggested_actions}\n"
                            f"Overview 已退回 EXECUTING。請依建議補強後再嘗試 COMPLETED。"
                        )
                    elif review.verdict == "INCONCLUSIVE":
                        # 放行 COMPLETED 但標記 needs_human_review（已設於 review）
                        overview.status = "COMPLETED"
                        overview.save(update_fields=["status", "updated_at"])
                        self._complete_active_graphs(overview)
                        self._inject_review_feedback(overview, review, verdict_label="INCONCLUSIVE")
                        return (
                            f"⚠️ VerificationAgent 無法確認（confidence={review.confidence_score}/100），已放行但標記需人工複查。\n"
                            f"MissionReview#{review.id}（needs_human_review=True）\n"
                            f"分析：{review.reasoning}\n"
                            f"建議動作：{review.suggested_actions}\n"
                            f"Overview 已標記 COMPLETED。"
                        )
                    # APPROVED → 正常流程（設 COMPLETED + complete graphs）
                    overview.status = "COMPLETED"
                    overview.save(update_fields=["status", "updated_at"])
                    self._complete_active_graphs(overview)
                    self._inject_review_feedback(overview, review, verdict_label="APPROVED")
                    return (
                        f"✅ VerificationAgent 審查通過（confidence={review.confidence_score}/100）。\n"
                        f"MissionReview#{review.id}\n"
                        f"分析：{review.reasoning}\n"
                        f"成功更新 Overview#{overview_id} 的 status！"
                    )

                # 非 COMPLETED 的 status 變更（PLANNING/EXECUTING/STALLED/NEEDS_GUIDANCE）直接通過
                overview.status = new_status
                update_fields.append('status')
            if new_summary is not None:
                overview.summary = new_summary
                update_fields.append('summary')
            if new_knowledge is not None:
                overview.knowledge = new_knowledge
                update_fields.append('knowledge')
            if new_risk_score is not None:
                overview.risk_score = new_risk_score
                update_fields.append('risk_score')
            
            if update_fields:
                overview.save(update_fields=update_fields)
            return f"成功更新 Overview#{overview_id} 的 {', '.join(update_fields)}！"
        except Exception as e:
            logger.error(f"Failed to update Overview#{overview_id}: {e}")
            return f"更新 Overview 時發生錯誤: {e}"

    def _complete_active_graphs(self, overview) -> None:
        """Overview 切到 COMPLETED 時，連動完成 thread 對應的 active graph。

        語意：Overview.status=COMPLETED 是 mission 真完成的訊號 → graph 才能 SUCCEEDED。
        """
        try:
            from apps.core.models import ExecutionGraph
            from apps.core.services import ExecutionService

            active_graphs = ExecutionGraph.objects.filter(
                thread_id=overview.thread_id,
                status__in=[
                    ExecutionGraph.Status.RUNNING,
                    ExecutionGraph.Status.WAITING,
                ],
            )
            for g in active_graphs:
                ExecutionService.complete_graph(
                    g, content=f"Overview {overview.id} marked COMPLETED"
                )
        except Exception as graph_err:
            logger.warning(
                f"_complete_active_graphs: failed for Overview#{overview.id}: {graph_err}"
            )

    def _inject_review_feedback(self, overview, review, verdict_label: str) -> None:
        """把審查結果注入 thread（讓 agent 被喚醒後看到具體回饋）。

        - REJECTED: 寫入駁回理由 + 觸發 wake（複用 L2 wake 機制）
        - INCONCLUSIVE/APPROVED: 寫入摘要（不 wake，因為已經放行）
        """
        try:
            from apps.core.models.ai_models import Thread as AIThread
            from apps.core.models import Message as DjangoMessage
            from langchain_core.messages import HumanMessage, message_to_dict

            thread = AIThread.objects.filter(id=overview.thread_id).first()
            if not thread:
                return

            if verdict_label == "REJECTED":
                lines = [
                    f"[SYSTEM: VerificationAgent REJECTED COMPLETED]",
                    f"Confidence: {review.confidence_score}/100",
                    f"Analysis: {review.reasoning}",
                    "Issues found:",
                ]
                for r in (review.rejection_reasons or []):
                    lines.append(f"- {r}")
                lines.append("Suggested actions:")
                for a in (review.suggested_actions or []):
                    lines.append(f"- {a}")
                content = "\n".join(lines)
            elif verdict_label == "INCONCLUSIVE":
                content = (
                    f"[SYSTEM: VerificationAgent INCONCLUSIVE (confidence={review.confidence_score})]\n"
                    f"Mission 放行但已標記 needs_human_review。\n"
                    f"Analysis: {review.reasoning}\n"
                    f"Suggested follow-up: {review.suggested_actions}"
                )
            else:  # APPROVED
                content = (
                    f"[SYSTEM: VerificationAgent APPROVED (confidence={review.confidence_score})]\n"
                    f"{review.reasoning}"
                )

            DjangoMessage.objects.create(
                thread=thread,
                role="human",
                message=message_to_dict(HumanMessage(content=content)),
            )

            # REJECTED 時觸發 wake agent（讓 agent 立刻看到駁回理由並繼續）
            if verdict_label == "REJECTED":
                try:
                    from apps.auto.tasks import wake_agent_on_scan_completion
                    wake_agent_on_scan_completion.delay(thread_id=thread.id)
                except Exception as wake_err:
                    logger.warning(
                        f"_inject_review_feedback: wake failed for thread={thread.id}: {wake_err}"
                    )
        except Exception as e:
            logger.error(f"_inject_review_feedback failed for Overview#{overview.id}: {e}")

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
        overview_id: int = None,
        limit: int = 50,
        offset: int = 0
    ) -> str:
        """
        取得此 Overview 中所有狀態為 EXHAUSTED (失敗) 或 MITIGATED (已緩解) 的攻擊向量（支持分页）。
        同時顯示每個向量曾被哪些 Action 操作過，幫助你理解「試了什麼、怎麼試的、為何失敗」。

        AI 在規劃新行動前應先呼叫此工具，避免重複使用已經失敗的攻擊向量！

        Args:
            overview_id: (Optional) Overview ID。自動注入。
            limit: 返回数量上限（默认 50，最大 100）
            offset: 分页偏移（默认 0）
        """
        try:
            if not overview_id:
                return "Error: overview_id 未提供且 session 未綁定。請先呼叫 get_target_context 或 bind_to_target。"
            from apps.core.models import AttackVector

            query = AttackVector.objects.filter(
                overview_id=overview_id,
                status__in=["EXHAUSTED", "MITIGATED"]
            )

            limit = min(limit, 100)
            total = query.count()

            if total == 0:
                return "目前沒有已失敗或無效的攻擊向量。可自由進行測試。"

            vectors = query.order_by('-created_at')[offset:offset+limit]

            summary = f"Exhausted Attack Vectors (showing {len(vectors)}/{total}):\n\n"

            for v in vectors:
                summary += f"[{v.id}] {v.name} - {v.status}\n"
                cmds = list(v.command_templates.values_list('command', flat=True))
                if cmds:
                    summary += f"  Commands tried: {cmds}\n"
                actions = v.actions.all().order_by('order')
                if actions:
                    action_lines = []
                    for act in actions:
                        action_lines.append(
                            f"    Action#{act.id} [{act.status}]: {(act.purpose_text or '')[:80]}"
                        )
                    summary += f"  Actions ({actions.count()}):\n" + "\n".join(action_lines) + "\n"
                else:
                    summary += f"  Actions: (無關聯 Action — 舊版 create_step 建立的向量)\n"

            if total > offset + limit:
                summary += f"\n💡 Tip: Use offset={offset+limit} to see next {limit} vectors\n"

            return summary
        except Exception as e:
            return f"獲取失敗的攻擊向量時發生錯誤: {e}"

    # notify_caller_agent 已統一由 ReconnaissanceMixin 提供（SubAgentDispatch 路由），
    # 舊版直接 create_message 到 hacker_assistant_agent 的邏輯已刪除。

    @method_tool
    def record_vulnerability(
        self,
        overview_id: int = None,
        name: str = "",
        severity: str = "info",
        matched_at: str = "",
        description: str = "",
        vector_id: int = None,
        action_id: int = None,
        extracted_results: dict = None,
        request_raw: str = "",
        response_raw: str = "",
        tool_source: str = "automation-agent",
        verification_id: int = None
    ) -> str:
        """
        [Final Achievement] 當 AI 成功驗證並確認一個漏洞時，呼叫此工具將其記錄到資料庫。
        這會將漏洞與當前的 Overview、發現它的 AttackVector 以及執行的 Action 關聯起來。

        標準工作流：
        1. add_action(...) → 建立 Action + AttackVector
        2. update_action(action_id, status="IN_PROGRESS") → 開始執行
        3. create_verification(vector_id, observation_prompt) → 建立 Verification
        4. 若驗證通過 → record_vulnerability(action_id=..., vector_id=...)
        5. generate_poc_for_vulnerability(vuln_id) → 生成 PoC

        Args:
            overview_id: (Optional) 當前任務的 Overview ID。自動注入。
            name: 漏洞名稱（例如: "SQL Injection in Search Field"）。
            severity: 嚴重程度 ('critical', 'high', 'medium', 'low', 'info')。
            matched_at: 發現漏洞的具體位置（例如 URL 或 IP:PORT）。
            description: 漏洞的詳細描述與影響。
            vector_id: (選填) 關聯的攻擊向量 ID。
            action_id: (選填) 發現此漏洞的 Action ID，用於追蹤「哪次行動發現的」。
            extracted_results: (選填) 漏洞 Payload 或版本號等結構化數據。
            request_raw: (選填) 觸發漏洞的原始請求內容。
            response_raw: (選填) 包含漏洞證據的原始響應內容。
            tool_source: 來源工具，預設為 "automation-agent"。
            verification_id: (選填) 已通過的 Verification ID，用於反向關聯驗證記錄。
        """
        try:
            from apps.core.models import Vulnerability, Overview, AttackVector, Action
            
            overview = Overview.objects.filter(id=overview_id).first()
            if not overview:
                return f"ERROR: Overview#{overview_id} not found."

            vector = None
            if vector_id:
                vector = AttackVector.objects.filter(id=vector_id).first()

            action = None
            if action_id:
                action = Action.objects.filter(id=action_id).first()

            # 建立漏洞記錄
            vuln = Vulnerability.objects.create(
                overview=overview,
                source_attack_vector=vector,
                action=action,
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

            # 若提供 verification_id，反向關聯到建立的漏洞
            verification_msg = ""
            if verification_id:
                from apps.core.models.analyze.Verification import Verification
                updated = Verification.objects.filter(
                    id=verification_id, created_vulnerability__isnull=True
                ).update(created_vulnerability=vuln)
                if updated:
                    verification_msg = f" 已關聯 Verification#{verification_id}。"
                else:
                    verification_msg = f" (Warning: Verification#{verification_id} 不存在或已關聯其他漏洞。)"

            logger.info(f"[Automation] Recorded confirmed vulnerability: {name} (ID: {vuln.id})")
            return (
                f"✅ 已成功將漏洞 '{name}' 記錄至資料庫 (ID: {vuln.id})，狀態標記為 'confirmed'。{verification_msg}\n"
                f"建議下一步：generate_poc_for_vulnerability(vulnerability_id={vuln.id}) 生成 PoC。"
            )
        except Exception as e:
            logger.error(f"record_vulnerability failed: {e}")
            return f"記錄漏洞時發生錯誤: {e}"
