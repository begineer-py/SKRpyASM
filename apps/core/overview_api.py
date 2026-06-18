import logging
from datetime import datetime
from typing import Any, Optional

from ninja import Router, Schema
from ninja.errors import HttpError

from apps.core.models.analyze.overview import Overview

logger = logging.getLogger(__name__)
router = Router(tags=["Core - Overviews"])


class OverviewOut(Schema):
    id: int
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    status: str
    risk_score: int
    summary: Optional[str] = None
    business_impact: Optional[str] = None
    plan: Optional[Any] = None
    knowledge: Optional[Any] = None
    techs: Optional[Any] = None
    thread_id: Optional[int] = None
    parent_thread_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class OverviewCreateIn(Schema):
    target_id: Optional[int] = None
    summary: Optional[str] = None
    status: Optional[str] = None
    risk_score: Optional[int] = None
    business_impact: Optional[str] = None
    plan: Optional[Any] = None


class OverviewUpdateIn(Schema):
    summary: Optional[str] = None
    status: Optional[str] = None
    risk_score: Optional[int] = None
    business_impact: Optional[str] = None
    plan: Optional[Any] = None
    knowledge: Optional[Any] = None


def _overview_out(obj: Overview) -> dict:
    return OverviewOut(
        id=obj.id,
        target_id=obj.target_id,
        target_name=obj.target.name if obj.target_id and obj.target else None,
        status=obj.status,
        risk_score=obj.risk_score,
        summary=obj.summary,
        business_impact=obj.business_impact,
        plan=obj.plan,
        knowledge=obj.knowledge,
        techs=obj.techs,
        thread_id=obj.thread_id,
        parent_thread_id=obj.parent_thread_id,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


@router.get("/overviews/", response={200: list[OverviewOut]})
def list_overviews(request, target_id: int | None = None):
    qs = Overview.objects.select_related("target").all()
    if target_id is not None:
        qs = qs.filter(target_id=target_id)
    return [_overview_out(o) for o in qs.order_by("-updated_at")]


@router.get("/overviews/{overview_id}", response={200: OverviewOut})
def get_overview(request, overview_id: int):
    obj = Overview.objects.select_related("target").filter(id=overview_id).first()
    if not obj:
        raise HttpError(404, f"Overview {overview_id} not found")
    return _overview_out(obj)


@router.post("/overviews/", response={201: OverviewOut})
def create_overview(request, payload: OverviewCreateIn):
    obj = Overview.objects.create(
        target_id=payload.target_id,
        summary=payload.summary or "",
        status=payload.status or "PLANNING",
        risk_score=payload.risk_score or 0,
        business_impact=payload.business_impact or "",
        plan=payload.plan,
    )
    return _overview_out(Overview.objects.select_related("target").get(id=obj.id))


@router.patch("/overviews/{overview_id}", response={200: OverviewOut})
def update_overview(request, overview_id: int, payload: OverviewUpdateIn):
    obj = Overview.objects.filter(id=overview_id).first()
    if not obj:
        raise HttpError(404, f"Overview {overview_id} not found")

    updates = {}
    update_fields = []
    if payload.summary is not None:
        obj.summary = payload.summary
        update_fields.append("summary")
    if payload.status is not None:
        obj.status = payload.status
        update_fields.append("status")
    if payload.risk_score is not None:
        obj.risk_score = payload.risk_score
        update_fields.append("risk_score")
    if payload.business_impact is not None:
        obj.business_impact = payload.business_impact
        update_fields.append("business_impact")
    if payload.plan is not None:
        obj.plan = payload.plan
        update_fields.append("plan")
    if payload.knowledge is not None:
        obj.knowledge = payload.knowledge
        update_fields.append("knowledge")

    if update_fields:
        obj.save(update_fields=update_fields)

    return _overview_out(Overview.objects.select_related("target").get(id=obj.id))


@router.delete("/overviews/{overview_id}", response={200: dict})
def delete_overview(request, overview_id: int):
    obj = Overview.objects.filter(id=overview_id).first()
    if not obj:
        raise HttpError(404, f"Overview {overview_id} not found")
    obj.delete()
    return {"success": True}
