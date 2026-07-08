"""
Attack Planning REST API
────────────────────────
CRUD endpoints for AttackPlan, Action, AttackVector, AssetVectorLink.
Follows the pattern established in vulnerability_api.py.
"""

import logging
from datetime import datetime
from typing import List, Optional

from django.db.models import Prefetch
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from apps.core.models.analyze.attack_planning import (
    Action,
    ActionVector,
    AssetVectorLink,
    AttackPlan,
)
from apps.core.models.analyze.AttackVector import AttackVector

logger = logging.getLogger(__name__)
router = Router(tags=["Core - Attack Planning"])


# ────────────────────────────── Schemas ──────────────────────────────


class AttackVectorOut(BaseModel):
    id: int
    overview_id: int | None = None
    name: str
    description: str | None = None
    vector_type: str
    status: str
    risk_score: int = 0
    evidence: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AssetVectorLinkOut(BaseModel):
    id: int
    attack_vector_id: int
    asset_type: str
    ip_asset_id: int | None = None
    subdomain_asset_id: int | None = None
    url_asset_id: int | None = None
    endpoint_asset_id: int | None = None
    port_asset_id: int | None = None
    status: str
    agent_thread_id: int | None = None
    agent_role: str | None = None
    last_result: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ActionVectorOut(BaseModel):
    id: int
    action_id: int
    attack_vector_id: int
    execution_detail: dict | None = None


class ActionOut(BaseModel):
    id: int
    target_id: int
    plan_id: int | None = None
    purpose: dict = {}
    purpose_text: str | None = None
    status: str
    agent_thread_id: int | None = None
    agent_role: str | None = None
    execution_graph_id: int | None = None
    result_summary: str | None = None
    order: int = 0
    created_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    asset_links: list[AssetVectorLinkOut] = []
    attack_vectors: list[AttackVectorOut] = []
    action_vectors: list[ActionVectorOut] = []


class AttackPlanOut(BaseModel):
    id: int
    target_id: int
    thread_id: int | None = None
    objective: str
    scope: dict = {}
    status: str
    parent_plan_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None
    actions: list[ActionOut] = []


class AttackPlanCreate(BaseModel):
    target_id: int
    objective: str
    scope: Optional[dict] = None
    status: str = "DRAFT"
    parent_plan_id: Optional[int] = None


class AttackPlanUpdate(BaseModel):
    objective: Optional[str] = None
    scope: Optional[dict] = None
    status: Optional[str] = None


class ActionUpdate(BaseModel):
    status: Optional[str] = None
    result_summary: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    purpose: Optional[dict] = None
    purpose_text: Optional[str] = None


class AttackVectorUpdate(BaseModel):
    status: Optional[str] = None
    risk_score: Optional[int] = None
    evidence: Optional[str] = None
    description: Optional[str] = None


# ────────────────────────────── Helpers ──────────────────────────────


def _dt(val) -> str | None:
    """Format datetime to ISO string."""
    if val is None:
        return None
    return val.isoformat()


def _asset_vector_link_out(obj: AssetVectorLink) -> AssetVectorLinkOut:
    return AssetVectorLinkOut(
        id=obj.id,
        attack_vector_id=obj.attack_vector_id,
        asset_type=obj.asset_type,
        ip_asset_id=obj.ip_asset_id,
        subdomain_asset_id=obj.subdomain_asset_id,
        url_asset_id=obj.url_asset_id,
        endpoint_asset_id=obj.endpoint_asset_id,
        port_asset_id=obj.port_asset_id,
        status=obj.status,
        agent_thread_id=obj.agent_thread_id,
        agent_role=obj.agent_role,
        last_result=obj.last_result,
        created_at=_dt(obj.created_at),
        updated_at=_dt(obj.updated_at),
    )


def _attack_vector_out(obj: AttackVector) -> AttackVectorOut:
    return AttackVectorOut(
        id=obj.id,
        overview_id=obj.overview_id,
        name=obj.name,
        description=obj.description,
        vector_type=obj.vector_type,
        status=obj.status,
        risk_score=obj.risk_score,
        evidence=obj.evidence,
        created_at=_dt(obj.created_at),
        updated_at=_dt(obj.updated_at),
    )


def _action_vector_out(obj: ActionVector) -> ActionVectorOut:
    return ActionVectorOut(
        id=obj.id,
        action_id=obj.action_id,
        attack_vector_id=obj.attack_vector_id,
        execution_detail=obj.execution_detail,
    )


def _action_out(obj: Action) -> ActionOut:
    asset_links = [_asset_vector_link_out(link) for link in obj.asset_links.all()]
    attack_vectors = [_attack_vector_out(av) for av in obj.attack_vectors.all()]
    action_vectors = [_action_vector_out(av) for av in obj.action_vectors.all()]
    return ActionOut(
        id=obj.id,
        target_id=obj.target_id,
        plan_id=obj.plan_id,
        purpose=obj.purpose or {},
        purpose_text=obj.purpose_text,
        status=obj.status,
        agent_thread_id=obj.agent_thread_id,
        agent_role=obj.agent_role,
        execution_graph_id=obj.execution_graph_id,
        result_summary=obj.result_summary,
        order=obj.order,
        created_at=_dt(obj.created_at),
        started_at=_dt(obj.started_at),
        completed_at=_dt(obj.completed_at),
        asset_links=asset_links,
        attack_vectors=attack_vectors,
        action_vectors=action_vectors,
    )


def _action_out_flat(obj: Action) -> ActionOut:
    """Action output without nested relations (for list views)."""
    return ActionOut(
        id=obj.id,
        target_id=obj.target_id,
        plan_id=obj.plan_id,
        purpose=obj.purpose or {},
        purpose_text=obj.purpose_text,
        status=obj.status,
        agent_thread_id=obj.agent_thread_id,
        agent_role=obj.agent_role,
        execution_graph_id=obj.execution_graph_id,
        result_summary=obj.result_summary,
        order=obj.order,
        created_at=_dt(obj.created_at),
        started_at=_dt(obj.started_at),
        completed_at=_dt(obj.completed_at),
        asset_links=[],
        attack_vectors=[],
        action_vectors=[],
    )


def _plan_out(obj: AttackPlan, include_actions: bool = True) -> AttackPlanOut:
    actions: list[ActionOut] = []
    if include_actions:
        qs = obj.actions.all().prefetch_related(
            "asset_links",
            "attack_vectors",
            "action_vectors",
        )
        actions = [_action_out(a) for a in qs]
    return AttackPlanOut(
        id=obj.id,
        target_id=obj.target_id,
        thread_id=obj.thread_id,
        objective=obj.objective,
        scope=obj.scope or {},
        status=obj.status,
        parent_plan_id=obj.parent_plan_id,
        created_at=_dt(obj.created_at),
        updated_at=_dt(obj.updated_at),
        actions=actions,
    )


def _plan_qs():
    return AttackPlan.objects.all()


def _action_qs():
    return Action.objects.prefetch_related(
        "asset_links",
        "attack_vectors",
        "action_vectors",
    )


def _attack_vector_qs():
    return AttackVector.objects.all()


# ────────────────────── AttackPlan endpoints ─────────────────────────


@router.get("/attack-plans", response={200: dict})
def list_attack_plans(
    request,
    target_id: int | None = None,
    status: str | None = None,
    thread_id: int | None = None,
):
    qs = _plan_qs()
    if target_id is not None:
        qs = qs.filter(target_id=target_id)
    if status is not None:
        qs = qs.filter(status=status)
    if thread_id is not None:
        qs = qs.filter(thread_id=thread_id)
    total = qs.count()
    items = [_plan_out(p, include_actions=False) for p in qs.order_by("-created_at")]
    return {"items": items, "total": total}


@router.get("/attack-plans/{plan_id}", response={200: AttackPlanOut})
def get_attack_plan(request, plan_id: int):
    obj = _plan_qs().filter(id=plan_id).first()
    if not obj:
        raise HttpError(404, f"AttackPlan {plan_id} not found")
    return _plan_out(obj, include_actions=True)


@router.post("/attack-plans", response={201: AttackPlanOut})
def create_attack_plan(request, payload: AttackPlanCreate):
    data = payload.model_dump(exclude_unset=True)
    obj = AttackPlan(**data)
    obj.save()
    obj.refresh_from_db()
    return _plan_out(obj, include_actions=False)


@router.patch("/attack-plans/{plan_id}", response={200: AttackPlanOut})
def update_attack_plan(request, plan_id: int, payload: AttackPlanUpdate):
    obj = _plan_qs().filter(id=plan_id).first()
    if not obj:
        raise HttpError(404, f"AttackPlan {plan_id} not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(obj, key, value)
    obj.save()
    return _plan_out(obj, include_actions=False)


# ────────────────────── Action endpoints ─────────────────────────────


@router.get("/attack-plans/{plan_id}/actions", response={200: dict})
def list_plan_actions(request, plan_id: int):
    plan = _plan_qs().filter(id=plan_id).first()
    if not plan:
        raise HttpError(404, f"AttackPlan {plan_id} not found")
    qs = _action_qs().filter(plan_id=plan_id)
    total = qs.count()
    items = [_action_out(a) for a in qs]
    return {"items": items, "total": total}


@router.get("/actions/{action_id}", response={200: ActionOut})
def get_action(request, action_id: int):
    obj = _action_qs().filter(id=action_id).first()
    if not obj:
        raise HttpError(404, f"Action {action_id} not found")
    return _action_out(obj)


@router.patch("/actions/{action_id}", response={200: ActionOut})
def update_action(request, action_id: int, payload: ActionUpdate):
    obj = Action.objects.filter(id=action_id).first()
    if not obj:
        raise HttpError(404, f"Action {action_id} not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(obj, key, value)
    obj.save()
    return _action_out(_action_qs().get(id=obj.id))


# ────────────────────── AttackVector endpoints ───────────────────────


@router.get("/attack-vectors", response={200: dict})
def list_attack_vectors(
    request,
    overview_id: int | None = None,
    status: str | None = None,
    vector_type: str | None = None,
):
    qs = _attack_vector_qs()
    if overview_id is not None:
        qs = qs.filter(overview_id=overview_id)
    if status is not None:
        qs = qs.filter(status=status)
    if vector_type is not None:
        qs = qs.filter(vector_type=vector_type)
    total = qs.count()
    items = [_attack_vector_out(v) for v in qs.order_by("-created_at")]
    return {"items": items, "total": total}


@router.get("/attack-vectors/{vector_id}", response={200: dict})
def get_attack_vector(request, vector_id: int):
    obj = _attack_vector_qs().filter(id=vector_id).first()
    if not obj:
        raise HttpError(404, f"AttackVector {vector_id} not found")
    asset_links = [
        _asset_vector_link_out(link) for link in obj.asset_links.all()
    ]
    action_items = [
        {"id": av.action.id, "status": av.action.status, "purpose_text": av.action.purpose_text}
        for av in obj.action_vectors.select_related("action").all()
    ]
    return {
        **_attack_vector_out(obj).model_dump(),
        "asset_links": asset_links,
        "actions": action_items,
    }


@router.patch("/attack-vectors/{vector_id}", response={200: AttackVectorOut})
def update_attack_vector(request, vector_id: int, payload: AttackVectorUpdate):
    obj = _attack_vector_qs().filter(id=vector_id).first()
    if not obj:
        raise HttpError(404, f"AttackVector {vector_id} not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(obj, key, value)
    obj.save()
    return _attack_vector_out(obj)
