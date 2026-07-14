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
    recon_summary: Optional[str] = None
    business_impact: Optional[str] = None
    plan: Optional[Any] = None
    knowledge: Optional[Any] = None
    techs: Optional[Any] = None
    tech_stack: Optional[Any] = None
    subdomain_intel: Optional[Any] = None
    port_service: Optional[Any] = None
    vuln_intel: Optional[Any] = None
    seed_id: Optional[int] = None
    ips: Optional[list[int]] = None
    subdomains: Optional[list[int]] = None
    url_results: Optional[list[int]] = None
    thread_id: Optional[int] = None
    parent_thread_id: Optional[int] = None
    needs_human_review: bool = False
    latest_mission_review_id: Optional[int] = None
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
    recon_summary: Optional[str] = None
    status: Optional[str] = None
    risk_score: Optional[int] = None
    business_impact: Optional[str] = None
    plan: Optional[Any] = None
    knowledge: Optional[Any] = None
    tech_stack: Optional[Any] = None
    subdomain_intel: Optional[Any] = None
    port_service: Optional[Any] = None
    vuln_intel: Optional[Any] = None


def _overview_out(obj: Overview) -> dict:
    # prefetch M2M relationships — only once per overview object
    ips = list(obj.ips.values_list("id", flat=True)) if obj.pk else []
    subdomains = list(obj.subdomains.values_list("id", flat=True)) if obj.pk else []
    url_results = list(obj.url_results.values_list("id", flat=True)) if obj.pk else []
    # MissionReview 快照
    latest_review = (
        obj.mission_reviews.order_by("-created_at").first() if obj.pk else None
    )
    needs_human_review = (
        obj.mission_reviews.filter(needs_human_review=True).exists() if obj.pk else False
    )
    return OverviewOut(
        id=obj.id,
        target_id=obj.target_id,
        target_name=obj.target.name if obj.target_id and obj.target else None,
        status=obj.status,
        risk_score=obj.risk_score,
        summary=obj.summary,
        recon_summary=obj.recon_summary,
        business_impact=obj.business_impact,
        plan=obj.plan,
        knowledge=obj.knowledge,
        techs=obj.techs,
        tech_stack=obj.tech_stack,
        subdomain_intel=obj.subdomain_intel,
        port_service=obj.port_service,
        vuln_intel=obj.vuln_intel,
        seed_id=obj.seed_id,
        ips=ips,
        subdomains=subdomains,
        url_results=url_results,
        thread_id=obj.thread_id,
        parent_thread_id=obj.parent_thread_id,
        needs_human_review=needs_human_review,
        latest_mission_review_id=latest_review.id if latest_review else None,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


@router.get("/overviews/", response={200: list[OverviewOut]})
def list_overviews(request, target_id: int | None = None):
    qs = Overview.objects.select_related("target", "seed").prefetch_related("ips", "subdomains", "url_results").all()
    if target_id is not None:
        qs = qs.filter(target_id=target_id)
    return [_overview_out(o) for o in qs.order_by("-updated_at")]


@router.get("/overviews/{overview_id}", response={200: OverviewOut})
def get_overview(request, overview_id: int):
    obj = Overview.objects.select_related("target", "seed").prefetch_related("ips", "subdomains", "url_results").filter(id=overview_id).first()
    if not obj:
        raise HttpError(404, f"Overview {overview_id} not found")
    return _overview_out(obj)


@router.post("/overviews/", response={201: OverviewOut})
def create_overview(request, payload: OverviewCreateIn):
    # 1:1 關係：target 已有 overview 時改為 upsert（更新既有）
    if payload.target_id:
        obj, created = Overview.objects.get_or_create(
            target_id=payload.target_id,
            defaults={
                "summary": payload.summary or "",
                "status": payload.status or "PLANNING",
                "risk_score": payload.risk_score or 0,
                "business_impact": payload.business_impact or "",
            },
        )
        if not created:
            # 既有 overview 已存在 — 更新可選欄位
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
            if update_fields:
                obj.save(update_fields=update_fields)
    else:
        obj = Overview.objects.create(
            target_id=payload.target_id,
            summary=payload.summary or "",
            status=payload.status or "PLANNING",
            risk_score=payload.risk_score or 0,
            business_impact=payload.business_impact or "",
        )
    return _overview_out(Overview.objects.select_related("target").get(id=obj.id))


@router.patch("/overviews/{overview_id}", response={200: OverviewOut})
def update_overview(request, overview_id: int, payload: OverviewUpdateIn):
    obj = Overview.objects.select_related("target", "seed").prefetch_related("ips", "subdomains", "url_results").filter(id=overview_id).first()
    if not obj:
        raise HttpError(404, f"Overview {overview_id} not found")

    updates = {}
    update_fields = []
    if payload.summary is not None:
        obj.summary = payload.summary
        update_fields.append("summary")
    if payload.recon_summary is not None:
        obj.recon_summary = payload.recon_summary
        update_fields.append("recon_summary")
    if payload.status is not None:
        obj.status = payload.status
        update_fields.append("status")
    if payload.risk_score is not None:
        obj.risk_score = payload.risk_score
        update_fields.append("risk_score")
    if payload.business_impact is not None:
        obj.business_impact = payload.business_impact
        update_fields.append("business_impact")
    if payload.knowledge is not None:
        obj.knowledge = payload.knowledge
        update_fields.append("knowledge")
    if payload.tech_stack is not None:
        obj.tech_stack = payload.tech_stack
        update_fields.append("tech_stack")
    if payload.subdomain_intel is not None:
        obj.subdomain_intel = payload.subdomain_intel
        update_fields.append("subdomain_intel")
    if payload.port_service is not None:
        obj.port_service = payload.port_service
        update_fields.append("port_service")
    if payload.vuln_intel is not None:
        obj.vuln_intel = payload.vuln_intel
        update_fields.append("vuln_intel")

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
