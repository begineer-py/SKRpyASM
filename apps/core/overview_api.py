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


@router.get("/overviews/", response={200: list[OverviewOut]})
def list_overviews(request):
    return list(Overview.objects.all().order_by("-updated_at"))


@router.get("/overviews/{overview_id}", response={200: OverviewOut})
def get_overview(request, overview_id: int):
    obj = Overview.objects.filter(id=overview_id).first()
    if not obj:
        raise HttpError(404, f"Overview {overview_id} not found")
    return obj


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
    return obj


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

    return obj


@router.delete("/overviews/{overview_id}", response={200: dict})
def delete_overview(request, overview_id: int):
    obj = Overview.objects.filter(id=overview_id).first()
    if not obj:
        raise HttpError(404, f"Overview {overview_id} not found")
    obj.delete()
    return {"success": True}
