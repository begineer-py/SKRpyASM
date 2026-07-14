import logging
from datetime import datetime
from typing import List, Optional

from ninja import Router, Schema
from ninja.errors import HttpError

from apps.core.models.analyze.MissionReview import MissionReview

logger = logging.getLogger(__name__)
router = Router(tags=["Core - Mission Reviews"])


class MissionReviewOut(Schema):
    id: int
    overview_id: int
    verdict: str
    confidence_score: int
    reasoning: str
    rejection_reasons: List[str]
    suggested_actions: List[str]
    needs_human_review: bool
    # 審查輸入快照
    vuln_count: int
    confirmed_vuln_count: int
    high_severity_count: int
    has_poc_evidence: bool
    scan_coverage_pct: int
    # 觸發來源
    triggered_by: str
    triggered_by_agent: str
    # 時間
    reviewed_at: Optional[datetime] = None
    created_at: datetime


def _review_out(r: MissionReview) -> MissionReviewOut:
    return MissionReviewOut(
        id=r.id,
        overview_id=r.overview_id,
        verdict=r.verdict,
        confidence_score=r.confidence_score,
        reasoning=r.reasoning,
        rejection_reasons=r.rejection_reasons or [],
        suggested_actions=r.suggested_actions or [],
        needs_human_review=r.needs_human_review,
        vuln_count=r.vuln_count,
        confirmed_vuln_count=r.confirmed_vuln_count,
        high_severity_count=r.high_severity_count,
        has_poc_evidence=r.has_poc_evidence,
        scan_coverage_pct=r.scan_coverage_pct,
        triggered_by=r.triggered_by,
        triggered_by_agent=r.triggered_by_agent,
        reviewed_at=r.reviewed_at,
        created_at=r.created_at,
    )


@router.get(
    "/overviews/{overview_id}/mission-reviews",
    response={200: List[MissionReviewOut]},
)
def list_mission_reviews(request, overview_id: int):
    """列出指定 Overview 的所有 MissionReview（最新在前面）。"""
    qs = MissionReview.objects.filter(overview_id=overview_id).order_by("-created_at")
    return [_review_out(r) for r in qs]


@router.get(
    "/mission-reviews/{review_id}",
    response={200: MissionReviewOut},
)
def get_mission_review(request, review_id: int):
    """取得單筆 MissionReview 詳情。"""
    obj = MissionReview.objects.filter(id=review_id).first()
    if not obj:
        raise HttpError(404, f"MissionReview {review_id} not found")
    return _review_out(obj)


@router.get(
    "/mission-reviews",
    response={200: List[MissionReviewOut]},
)
def list_all_mission_reviews(
    request,
    needs_human_review: bool | None = None,
    verdict: str | None = None,
    limit: int = 50,
):
    """全局列表，可篩選 needs_human_review 或 verdict。"""
    qs = MissionReview.objects.all()
    if needs_human_review is not None:
        qs = qs.filter(needs_human_review=needs_human_review)
    if verdict:
        if verdict not in {"PENDING", "APPROVED", "REJECTED", "INCONCLUSIVE"}:
            raise HttpError(
                400,
                "verdict must be one of PENDING/APPROVED/REJECTED/INCONCLUSIVE",
            )
        qs = qs.filter(verdict=verdict)
    qs = qs.order_by("-created_at")[:limit]
    return [_review_out(r) for r in qs]
