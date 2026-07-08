"""
攻擊計劃管理工具 (Plan Management Tools)
─────────────────────────────────────────
將舊 Overview.plan JSONField 的計劃功能遷移到獨立的 DB 模型：
AttackPlan → Action → AssetVectorLink → 具體資產 (IP/Subdomain/URL/Endpoint/Port)。

核心設計原則：資產理所當然就是滲透目標。
每個 Action 直接綁定具體資產（FK 級），不再用自由文字描述目標。
"""

import json
import logging
from typing import Any, Optional

from apps.ai_assistant.langchain.tools import method_tool

logger = logging.getLogger(__name__)

# ── 資產類型 → AssetVectorLink FK 欄位映射 ──────────────────────────
_ASSET_FK_MAP: dict[str, str] = {
    "IP": "ip_asset",
    "SUBDOMAIN": "subdomain_asset",
    "URL": "url_asset",
    "ENDPOINT": "endpoint_asset",
    "PORT": "port_asset",
}

# ── 資產類型 → Django Model 映射（用於驗證 ID 存在性）──────────────
_ASSET_MODEL_PATH: dict[str, tuple[str, str]] = {
    "IP": ("apps.core.models", "IP"),
    "SUBDOMAIN": ("apps.core.models", "Subdomain"),
    "URL": ("apps.core.models", "URLResult"),
    "ENDPOINT": ("apps.core.models", "Endpoint"),
    "PORT": ("apps.core.models", "Port"),
}

_VALID_ASSET_TYPES = list(_ASSET_FK_MAP.keys())


def _validate_asset_exists(asset_type: str, asset_id: int) -> tuple[bool, str]:
    """驗證資產 ID 在 DB 中存在。回傳 (ok, error_msg)。"""
    if asset_type not in _ASSET_MODEL_PATH:
        return False, f"無效的 asset_type '{asset_type}'，合法值: {_VALID_ASSET_TYPES}"
    module_path, model_name = _ASSET_MODEL_PATH[asset_type]
    import importlib
    mod = importlib.import_module(module_path)
    ModelCls = getattr(mod, model_name)
    if not ModelCls.objects.filter(id=asset_id).exists():
        return False, f"CRITICAL_FAILURE: {asset_type}#{asset_id} 不存在於 DB。請只用 get_target_context 回傳的 ID。"
    return True, ""


def _create_asset_vector_link(asset_type: str, asset_id: int, attack_vector, thread_id: int | None = None, agent_role: str | None = None) -> Any:
    """建立 AssetVectorLink — 綁定具體資產到 AttackVector。"""
    from apps.core.models import AssetVectorLink
    fk_field = _ASSET_FK_MAP[asset_type]
    link = AssetVectorLink.objects.create(
        attack_vector=attack_vector,
        asset_type=asset_type,
        **{fk_field: asset_id},
        agent_thread_id=thread_id,
        agent_role=agent_role,
    )
    return link


class PlanToolsMixin:
    """攻擊計劃管理工具集 — 提供 Agent 建立/更新/查詢 AttackPlan + Action 的能力。"""

    # ── 計劃層 ─────────────────────────────────────────────────────

    @method_tool
    def create_attack_plan(
        self,
        objective: str,
        scope_asset_types: str = None,
        scope_filter: str = None,
        overview_id: int = None,
    ) -> str:
        """
        建立一個新的攻擊計劃 (AttackPlan)。

        計劃建立後狀態為 DRAFT，需呼叫 activate_plan 才會進入 ACTIVE 並建立 WalkCursor。
        一個 Target 可以有多個計劃（例如不同階段的測試），但同時只有一個 ACTIVE。

        Args:
            objective: 計劃的整體目標（一句話描述，如「枚舉 example.com 攻擊面並驗證高風險漏洞」）。
            scope_asset_types: 計劃模糊範圍的資產類型，逗號分隔（如 "SUBDOMAIN,URL"）。可省略。
            scope_filter: 模糊範圍的篩選條件（如 "*.example.com"）。可省略。
            overview_id: Overview ID（自動注入，無需手動提供）。
        """
        try:
            from apps.core.models import Overview, AttackPlan

            resolved_ov_id = overview_id or getattr(self, '_agent_overview_id', None)
            if not resolved_ov_id:
                return "CRITICAL_FAILURE: 缺少 overview_id，無法解析 Target。請先呼叫 get_target_context。"

            overview = Overview.objects.filter(id=resolved_ov_id).select_related("target").first()
            if not overview:
                return f"CRITICAL_FAILURE: Overview#{resolved_ov_id} 不存在。"
            if not overview.target_id:
                return f"CRITICAL_FAILURE: Overview#{resolved_ov_id} 沒有綁定 Target。"

            # 檢查是否已有 ACTIVE 計劃
            existing_active = AttackPlan.objects.filter(
                target_id=overview.target_id, status="ACTIVE"
            ).first()
            if existing_active:
                return (
                    f"⚠️ Target 已有 ACTIVE 計劃 AttackPlan#{existing_active.id}。"
                    f"請先完成或放棄該計劃再建立新計劃。"
                    f"可用 update_action 推進既有計劃，或 get_plan_status 查看現況。"
                )

            # 組裝 scope
            scope: dict = {}
            if scope_asset_types or scope_filter:
                fuzzy: dict = {}
                if scope_asset_types:
                    types_list = [t.strip().upper() for t in scope_asset_types.split(",") if t.strip()]
                    invalid = [t for t in types_list if t not in _VALID_ASSET_TYPES]
                    if invalid:
                        return f"CRITICAL_FAILURE: 無效的 asset_type {invalid}，合法值: {_VALID_ASSET_TYPES}"
                    fuzzy["asset_types"] = types_list
                if scope_filter:
                    fuzzy["filter"] = scope_filter
                scope["fuzzy"] = fuzzy
            scope["explicit_asset_link_ids"] = []

            thread_id = getattr(self, '_current_invoke_thread_id', None)
            plan = AttackPlan.objects.create(
                target_id=overview.target_id,
                thread_id=thread_id,
                objective=objective,
                scope=scope,
                status="DRAFT",
            )
            return (
                f"✅ AttackPlan#{plan.id} 已建立（DRAFT）。\n"
                f"   目標: {objective}\n"
                f"   範圍: {json.dumps(scope, ensure_ascii=False)}\n"
                f"   下一步: 用 add_action 加入具體行動，然後 activate_plan 開始執行。"
            )
        except Exception as e:
            logger.error(f"[PlanTools] create_attack_plan failed: {e}", exc_info=True)
            return f"建立攻擊計劃失敗: {e}"

    @method_tool
    def activate_plan(
        self,
        plan_id: int,
        overview_id: int = None,
    ) -> str:
        """
        將 DRAFT 計劃激活為 ACTIVE，並建立 WalkCursor（圖遍歷游標）。

        激活後 Agent 才能開始執行 Action。WalkCursor 追蹤 Agent 在資產圖上的當前位置。

        Args:
            plan_id: 要激活的 AttackPlan ID。
            overview_id: Overview ID（自動注入）。
        """
        try:
            from apps.core.models import AttackPlan, WalkCursor
            from django.utils import timezone

            plan = AttackPlan.objects.filter(id=plan_id).first()
            if not plan:
                return f"CRITICAL_FAILURE: AttackPlan#{plan_id} 不存在。"

            if plan.status == "ACTIVE":
                return f"AttackPlan#{plan_id} 已經是 ACTIVE，無需重複激活。"

            if plan.status == "COMPLETED":
                return f"AttackPlan#{plan_id} 已完成，無法重新激活。請建立新計劃。"

            if plan.status == "ABANDONED":
                return f"AttackPlan#{plan_id} 已放棄，無法重新激活。請建立新計劃。"

            # 檢查同 Target 是否已有 ACTIVE 計劃
            existing_active = AttackPlan.objects.filter(
                target_id=plan.target_id, status="ACTIVE"
            ).exclude(id=plan_id).first()
            if existing_active:
                return (
                    f"⚠️ Target 已有另一個 ACTIVE 計劃 AttackPlan#{existing_active.id}。"
                    f"請先完成或放棄該計劃。"
                )

            plan.status = "ACTIVE"
            plan.save(update_fields=["status", "updated_at"])

            # 建立 WalkCursor（若不存在）
            WalkCursor.objects.get_or_create(plan=plan)

            return (
                f"✅ AttackPlan#{plan_id} 已激活（ACTIVE）。\n"
                f"   WalkCursor 已建立 — 追蹤你在資產圖上的位置。\n"
                f"   現在可以用 update_action 開始執行 PENDING 的 Action。"
            )
        except Exception as e:
            logger.error(f"[PlanTools] activate_plan failed: {e}", exc_info=True)
            return f"激活計劃失敗: {e}"

    # ── 行動層 ─────────────────────────────────────────────────────

    @method_tool
    def add_action(
        self,
        plan_id: int,
        asset_type: str,
        asset_id: int,
        purpose_text: str,
        attack_vector_name: str = None,
        attack_vector_type: str = "OTHER",
        existing_attack_vector_id: int = None,
        order: int = 0,
        additional_assets: str = None,
        overview_id: int = None,
    ) -> str:
        """
        向計劃中加入一個行動 (Action)，綁定到具體資產。

        核心原則：資產就是滲透目標。每個 Action 直接綁定 DB 中的具體資產（FK 級）。
        大多數 Action 只涉及一個資產，但你可以透過 additional_assets 打包多個相關資產。

        系統會自動為每個資產建立 AssetVectorLink（資產↔攻擊向量綁定）。

        AttackVector 生命週期跨越多個 Action：
        - 第一個發現向量的 Action → 系統自動新建 AttackVector
        - 後續操作同一向量的 Action → 傳入 existing_attack_vector_id 引用既有向量

        Args:
            plan_id: 所屬 AttackPlan ID。
            asset_type: 主要資產類型（IP / SUBDOMAIN / URL / ENDPOINT / PORT）。
            asset_id: 主要資產的 DB ID（必須來自 get_target_context 或 create_discovered_* 工具）。
            purpose_text: 這次行動的目的描述（如「對此子域名執行 Nuclei 漏洞掃描」）。
            attack_vector_name: 攻擊向量名稱（如 "Reflected XSS on /search"）。可省略，系統會用 purpose_text 自動命名。僅在新建向量時使用。
            attack_vector_type: 攻擊向量類型（WEB_VULN / NETWORK_EXPOSURE / AUTH_BYPASS / INFO_LEAK / CONFIG_ISSUE / OTHER）。預設 OTHER。僅在新建向量時使用。
            existing_attack_vector_id: 既有 AttackVector ID。若提供則引用此向量（不新建），用於多個 Action 操作同一向量的場景（如先掃描→再驗證→再利用）。
            order: 執行順序（同計劃內從 0 遞增）。可省略。
            additional_assets: 額外資產的 JSON 陣列字串，如 '[{"type":"IP","id":5},{"type":"PORT","id":12}]'。可省略。
            overview_id: Overview ID（自動注入）。
        """
        try:
            from apps.core.models import AttackPlan, AttackVector, Action, ActionVector, AssetLock

            resolved_ov_id = overview_id or getattr(self, '_agent_overview_id', None)
            plan = AttackPlan.objects.filter(id=plan_id).first()
            if not plan:
                return f"CRITICAL_FAILURE: AttackPlan#{plan_id} 不存在。"
            if plan.status in ("COMPLETED", "ABANDONED"):
                return f"CRITICAL_FAILURE: AttackPlan#{plan_id} 狀態為 {plan.status}，無法加入新 Action。"

            # ── 收集所有資產（主要 + 額外）──────────────────────────
            assets: list[tuple[str, int]] = [(asset_type.upper(), asset_id)]
            if additional_assets:
                try:
                    extra_list = json.loads(additional_assets)
                    if not isinstance(extra_list, list):
                        return "CRITICAL_FAILURE: additional_assets 必須是 JSON 陣列字串。"
                    for item in extra_list:
                        if not isinstance(item, dict) or "type" not in item or "id" not in item:
                            return f"CRITICAL_FAILURE: additional_assets 格式錯誤，每個元素需含 type 和 id。收到: {item}"
                        assets.append((item["type"].upper(), int(item["id"])))
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    return f"CRITICAL_FAILURE: 無法解析 additional_assets JSON: {e}"

            # ── 驗證所有資產存在 ────────────────────────────────────
            for atype, aid in assets:
                ok, err = _validate_asset_exists(atype, aid)
                if not ok:
                    return err

            # ── AttackVector：引用既有 or 新建 ──────────────────────
            if not resolved_ov_id:
                return "CRITICAL_FAILURE: 缺少 overview_id，無法建立/引用 AttackVector。"

            if existing_attack_vector_id:
                attack_vector = AttackVector.objects.filter(id=existing_attack_vector_id).first()
                if not attack_vector:
                    return f"CRITICAL_FAILURE: existing_attack_vector_id={existing_attack_vector_id} 不存在。"
                vector_name = attack_vector.name
            else:
                vector_name = attack_vector_name or purpose_text[:200]
                attack_vector = AttackVector.objects.create(
                    overview_id=resolved_ov_id,
                    name=vector_name,
                    vector_type=attack_vector_type,
                    status="IDENTIFIED",
                )

            # ── 建立 AssetVectorLink for 每個資產 ───────────────────
            thread_id = getattr(self, '_current_invoke_thread_id', None)
            agent_role = "AUTOMATION"
            asset_links = []
            lock_warnings = []
            for atype, aid in assets:
                link = _create_asset_vector_link(atype, aid, attack_vector, thread_id, agent_role)
                asset_links.append(link)

                existing_lock = AssetLock.objects.filter(
                    **{f"{_ASSET_FK_MAP[atype]}_id": aid},
                    lock_status="HELD",
                ).exclude(thread_id=thread_id).first()
                if existing_lock:
                    lock_warnings.append(f"⚠️ {atype}#{aid} 已被 Thread#{existing_lock.thread_id} 持鎖")
                else:
                    AssetLock.objects.create(
                        target_id=plan.target_id,
                        asset_type=atype,
                        **{_ASSET_FK_MAP[atype]: aid},
                        thread_id=thread_id,
                        agent_role=agent_role,
                        lock_status="HELD",
                    )

            # ── 建立 Action ─────────────────────────────────────────
            action = Action.objects.create(
                target_id=plan.target_id,
                plan=plan,
                purpose={"text": purpose_text},
                purpose_text=purpose_text,
                status="PENDING",
                agent_thread_id=thread_id,
                agent_role=agent_role,
                order=order,
            )
            # M2M 關聯
            action.asset_links.set(asset_links)
            # ActionVector through model
            ActionVector.objects.create(action=action, attack_vector=attack_vector)

            # 更新 plan.scope.explicit_asset_link_ids
            scope = plan.scope or {}
            explicit_ids = scope.get("explicit_asset_link_ids", [])
            new_link_ids = [link.id for link in asset_links]
            explicit_ids.extend(new_link_ids)
            scope["explicit_asset_link_ids"] = explicit_ids
            plan.scope = scope
            plan.save(update_fields=["scope", "updated_at"])

            asset_summary = ", ".join(f"{t}#{i}" for t, i in assets)
            lock_info = f"\n   {''.join(lock_warnings)}" if lock_warnings else ""
            vector_op = f"引用既有 AttackVector#{attack_vector.id}" if existing_attack_vector_id else f"新建 AttackVector#{attack_vector.id}"
            return (
                f"✅ Action#{action.id} 已加入 AttackPlan#{plan_id}。\n"
                f"   目的: {purpose_text}\n"
                f"   綁定資產: {asset_summary}\n"
                f"   {vector_op}: {vector_name}\n"
                f"   AssetVectorLink IDs: {new_link_ids}\n"
                f"   狀態: PENDING — 用 update_action 開始執行。{lock_info}"
            )
        except Exception as e:
            logger.error(f"[PlanTools] add_action failed: {e}", exc_info=True)
            return f"加入行動失敗: {e}"

    @method_tool
    def update_action(
        self,
        action_id: int,
        status: str,
        result_summary: str = None,
        overview_id: int = None,
    ) -> str:
        """
        更新行動 (Action) 的狀態和結果摘要。

        狀態流轉：PENDING → IN_PROGRESS → COMPLETED / FAILED / SKIPPED。

        Args:
            action_id: 要更新的 Action ID。
            status: 新狀態（PENDING / IN_PROGRESS / COMPLETED / FAILED / SKIPPED）。
            result_summary: 行動結果摘要（完成或失敗時填寫）。可省略。
            overview_id: Overview ID（自動注入）。
        """
        try:
            from apps.core.models import Action, AssetLock
            from django.utils import timezone

            valid_statuses = ["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "SKIPPED"]
            if status not in valid_statuses:
                return f"CRITICAL_FAILURE: 無效狀態 '{status}'，合法值: {valid_statuses}"

            action = Action.objects.filter(id=action_id).first()
            if not action:
                return f"CRITICAL_FAILURE: Action#{action_id} 不存在。"

            update_fields = ["status", "updated_at"]
            action.status = status

            if status == "IN_PROGRESS" and not action.started_at:
                action.started_at = timezone.now()
                update_fields.append("started_at")

            if status in ("COMPLETED", "FAILED", "SKIPPED") and not action.completed_at:
                action.completed_at = timezone.now()
                update_fields.append("completed_at")

            if result_summary is not None:
                action.result_summary = result_summary
                update_fields.append("result_summary")

            action.save(update_fields=update_fields)

            # 同步 AssetVectorLink 狀態
            for link in action.asset_links.all():
                if status == "IN_PROGRESS":
                    link.status = "IN_PROGRESS"
                elif status == "COMPLETED":
                    link.status = "COMPLETED"
                elif status == "FAILED":
                    link.status = "FAILED"
                link.save(update_fields=["status", "updated_at"])

            if status in ("COMPLETED", "FAILED", "SKIPPED"):
                thread_id = action.agent_thread_id
                for link in action.asset_links.all():
                    fk_field = _ASSET_FK_MAP.get(link.asset_type)
                    if not fk_field:
                        continue
                    asset_id = getattr(link, f"{fk_field}_id", None)
                    if not asset_id or not thread_id:
                        continue
                    AssetLock.objects.filter(
                        **{f"{fk_field}_id": asset_id},
                        thread_id=thread_id,
                        lock_status="HELD",
                    ).update(lock_status="RELEASED", released_at=timezone.now())

            return f"✅ Action#{action_id} 狀態更新為 {status}。"
        except Exception as e:
            logger.error(f"[PlanTools] update_action failed: {e}", exc_info=True)
            return f"更新行動失敗: {e}"

    # ── 查詢層 ─────────────────────────────────────────────────────

    @method_tool
    def get_plan_status(
        self,
        plan_id: int = None,
        overview_id: int = None,
    ) -> str:
        """
        查詢當前攻擊計劃的完整狀態：計劃資訊、所有 Action、WalkCursor 位置。

        重新喚醒後或需要回顧進度時呼叫此工具。
        若不提供 plan_id，自動查找 Target 的 ACTIVE 計劃。

        Args:
            plan_id: 指定查詢的 AttackPlan ID。可省略（自動找 ACTIVE 計劃）。
            overview_id: Overview ID（自動注入）。
        """
        try:
            from apps.core.models import Overview, AttackPlan, WalkCursor, AssetLock

            resolved_ov_id = overview_id or getattr(self, '_agent_overview_id', None)
            if not resolved_ov_id:
                return "CRITICAL_FAILURE: 缺少 overview_id。請先呼叫 get_target_context。"

            overview = Overview.objects.filter(id=resolved_ov_id).select_related("target").first()
            if not overview:
                return f"CRITICAL_FAILURE: Overview#{resolved_ov_id} 不存在。"

            # 查找計劃
            if plan_id:
                plan = AttackPlan.objects.filter(id=plan_id).first()
                if not plan:
                    return f"CRITICAL_FAILURE: AttackPlan#{plan_id} 不存在。"
            else:
                plan = AttackPlan.objects.filter(
                    target_id=overview.target_id, status="ACTIVE"
                ).first()
                if not plan:
                    # 查找 DRAFT
                    plan = AttackPlan.objects.filter(
                        target_id=overview.target_id, status="DRAFT"
                    ).order_by("-created_at").first()
                    if not plan:
                        return (
                            f"Target '{overview.target.name}' 目前沒有任何 AttackPlan。\n"
                            f"請用 create_attack_plan 建立新計劃。"
                        )
                    return (
                        f"Target '{overview.target.name}' 有 DRAFT 計劃但尚未激活：\n"
                        f"AttackPlan#{plan.id} — {plan.objective}\n"
                        f"請用 activate_plan(plan_id={plan.id}) 激活後再執行。"
                    )

            # 收集 Action 列表
            actions_qs = plan.actions.select_related("agent_thread").prefetch_related(
                "asset_links", "attack_vectors"
            ).order_by("order", "created_at")

            lines = [
                f"=== ATTACK PLAN STATUS ===",
                f"Plan#{plan.id} — {plan.status}",
                f"Objective: {plan.objective}",
                f"Scope: {json.dumps(plan.scope, ensure_ascii=False)}",
                f"Target: {overview.target.name} (ID:{overview.target_id})",
                f"",
            ]

            if not actions_qs.exists():
                lines.append("Actions: (無 — 請用 add_action 加入行動)")
            else:
                lines.append(f"Actions ({actions_qs.count()}):")
                for act in actions_qs:
                    # 資產摘要
                    asset_strs = []
                    for link in act.asset_links.all():
                        atype = link.asset_type
                        # 取得資產的識別字串
                        ident = _get_asset_identifier(link)
                        asset_strs.append(f"{atype}#{_get_asset_id(link)}({ident})")

                    vectors = list(act.attack_vectors.values_list("name", flat=True))
                    vec_str = ", ".join(vectors) if vectors else "(無)"

                    lines.append(
                        f"  [{'>' if act.status == 'IN_PROGRESS' else ' '}] "
                        f"Action#{act.id} [{act.status}] order={act.order}\n"
                        f"      Purpose: {act.purpose_text or '(無)'}\n"
                        f"      Assets: {', '.join(asset_strs) or '(無)'}\n"
                        f"      Vectors: {vec_str}\n"
                        f"      Result: {(act.result_summary or '(尚無)')[:200]}"
                    )

            # WalkCursor
            lines.append("")
            try:
                cursor = plan.walk_cursor
                if cursor.current_asset_link_id:
                    link = cursor.current_asset_link
                    lines.append(
                        f"WalkCursor: 目前在 {link.asset_type}#{_get_asset_id(link)}"
                        f" (_get_asset_identifier: {_get_asset_identifier(link)})"
                    )
                else:
                    lines.append("WalkCursor: 初始位置（尚未開始走訪）")
                lines.append(
                    f"  已走訪邊數: {cursor.traversed_edges.count()}, "
                    f"待走訪邊數: {cursor.pending_edges.count()}"
                )
            except WalkCursor.DoesNotExist:
                lines.append("WalkCursor: (未建立 — 計劃尚未激活)")

            # AssetLock 狀態
            active_locks = AssetLock.objects.filter(
                target_id=overview.target_id, lock_status="HELD"
            ).select_related("thread")
            if active_locks.exists():
                lines.append("")
                lines.append(f"Active AssetLocks ({active_locks.count()}):")
                for lock in active_locks:
                    lines.append(
                        f"  [{lock.asset_type}] by Thread#{lock.thread_id} ({lock.agent_role})"
                    )
            else:
                lines.append("AssetLocks: (無活躍鎖)")

            lines.append("=== END OF PLAN STATUS ===")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"[PlanTools] get_plan_status failed: {e}", exc_info=True)
            return f"查詢計劃狀態失敗: {e}"

    # ── 資產圖層 ───────────────────────────────────────────────────

    @method_tool
    def add_asset_edge(
        self,
        from_asset_type: str,
        from_asset_id: int,
        to_asset_type: str,
        to_asset_id: int,
        edge_type: str = "DISCOVERED_FROM",
        action_id: int = None,
        overview_id: int = None,
    ) -> str:
        """
        在資產圖中記錄兩個資產之間的關聯邊 (AssetEdge)。

        例如：子域名解析到 IP（RESOLVES_TO）、URL 連結到另一個 URL（LINKS_TO）、
        掃描過程中從某資產發現了另一個資源（DISCOVERED_FROM）。

        這些邊構成資產圖，Walk 機制依賴此圖決定可走訪的鄰接資產。

        Args:
            from_asset_type: 起點資產類型（IP / SUBDOMAIN / URL / ENDPOINT / PORT）。
            from_asset_id: 起點資產 ID。
            to_asset_type: 終點資產類型。
            to_asset_id: 終點資產 ID。
            edge_type: 邊類型（RESOLVES_TO / HOSTS / LINKS_TO / DISCOVERED_FROM / CUSTOM）。預設 DISCOVERED_FROM。
            action_id: 發現此邊的 Action ID（可省略，用於追溯發現來源）。
            overview_id: Overview ID（自動注入）。
        """
        try:
            from apps.core.models import Overview, AssetEdge

            resolved_ov_id = overview_id or getattr(self, '_agent_overview_id', None)
            if not resolved_ov_id:
                return "CRITICAL_FAILURE: 缺少 overview_id。"

            overview = Overview.objects.filter(id=resolved_ov_id).select_related("target").first()
            if not overview:
                return f"CRITICAL_FAILURE: Overview#{resolved_ov_id} 不存在。"

            # 驗證資產
            for atype, aid in [(from_asset_type, from_asset_id), (to_asset_type, to_asset_id)]:
                ok, err = _validate_asset_exists(atype.upper(), aid)
                if not ok:
                    return err

            valid_edge_types = ["RESOLVES_TO", "HOSTS", "LINKS_TO", "DISCOVERED_FROM", "CUSTOM"]
            edge_type_upper = edge_type.upper()
            if edge_type_upper not in valid_edge_types:
                return f"CRITICAL_FAILURE: 無效 edge_type '{edge_type}'，合法值: {valid_edge_types}"

            from_fk = _ASSET_FK_MAP[from_asset_type.upper()]
            to_fk = _ASSET_FK_MAP[to_asset_type.upper()]

            edge = AssetEdge.objects.create(
                target_id=overview.target_id,
                from_asset_type=from_asset_type.upper(),
                **{f"from_{from_fk.lower().replace('_asset', '')}": from_asset_id},
                to_asset_type=to_asset_type.upper(),
                **{f"to_{to_fk.lower().replace('_asset', '')}": to_asset_id},
                edge_type=edge_type_upper,
                discovered_by_action_id=action_id,
            )

            return (
                f"✅ AssetEdge#{edge.id} 已建立: "
                f"{from_asset_type}#{from_asset_id} --[{edge_type_upper}]--> "
                f"{to_asset_type}#{to_asset_id}"
            )
        except Exception as e:
            logger.error(f"[PlanTools] add_asset_edge failed: {e}", exc_info=True)
            return f"建立資產邊失敗: {e}"

    @method_tool
    def walk_to_asset(
        self,
        asset_link_id: int,
        overview_id: int = None,
    ) -> str:
        """
        將 WalkCursor 移動到指定的資產（AssetVectorLink）。

        Walk 機制：Agent 在資產圖上一次走一個邊。
        移動到新資產前，該資產必須已在 DB 中（透過 create_discovered_* 或 add_action 建立）。

        Args:
            asset_link_id: 目標 AssetVectorLink ID（從 add_action 回傳或 get_plan_status 取得）。
            overview_id: Overview ID（自動注入）。
        """
        try:
            from apps.core.models import AttackPlan, WalkCursor, AssetVectorLink

            resolved_ov_id = overview_id or getattr(self, '_agent_overview_id', None)
            if not resolved_ov_id:
                return "CRITICAL_FAILURE: 缺少 overview_id。"

            # 查找 ACTIVE 計劃
            from apps.core.models import Overview
            overview = Overview.objects.filter(id=resolved_ov_id).select_related("target").first()
            if not overview:
                return f"CRITICAL_FAILURE: Overview#{resolved_ov_id} 不存在。"

            plan = AttackPlan.objects.filter(
                target_id=overview.target_id, status="ACTIVE"
            ).first()
            if not plan:
                return "CRITICAL_FAILURE: 沒有 ACTIVE 計劃，無法走訪。請先 activate_plan。"

            link = AssetVectorLink.objects.filter(id=asset_link_id).first()
            if not link:
                return f"CRITICAL_FAILURE: AssetVectorLink#{asset_link_id} 不存在。"

            cursor, _ = WalkCursor.objects.get_or_create(plan=plan)
            old_position = cursor.current_asset_link_id
            cursor.current_asset_link = link
            cursor.save(update_fields=["current_asset_link", "updated_at"])

            ident = _get_asset_identifier(link)
            aid = _get_asset_id(link)

            old_str = f"AssetVectorLink#{old_position}" if old_position else "初始位置"
            return (
                f"✅ WalkCursor 已移動: {old_str} → {link.asset_type}#{aid}({ident})\n"
                f"   AssetVectorLink#{link.id} — 現在你可以對此資產執行操作。"
            )
        except Exception as e:
            logger.error(f"[PlanTools] walk_to_asset failed: {e}", exc_info=True)
            return f"走訪資產失敗: {e}"


# ── Helper functions ────────────────────────────────────────────────

def _get_asset_id(link) -> int | None:
    """從 AssetVectorLink 取得資產 ID。"""
    for fk_field in _ASSET_FK_MAP.values():
        val = getattr(link, f"{fk_field}_id", None)
        if val:
            return val
    return None


def _get_asset_identifier(link) -> str:
    """從 AssetVectorLink 取得資產的人類可讀識別字串（如 IP 位址、子域名名稱）。"""
    try:
        if link.ip_asset_id and link.ip_asset:
            return link.ip_asset.address
        if link.subdomain_asset_id and link.subdomain_asset:
            return link.subdomain_asset.name
        if link.url_asset_id and link.url_asset:
            return link.url_asset.url[:80]
        if link.endpoint_asset_id and link.endpoint_asset:
            return f"{link.endpoint_asset.method} {link.endpoint_asset.path}"
        if link.port_asset_id and link.port_asset:
            return f"{link.port_asset.port_number}/{link.port_asset.protocol}"
    except Exception:
        pass
    return "?"
