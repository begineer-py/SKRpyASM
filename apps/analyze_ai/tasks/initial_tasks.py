import logging
from typing import List, Optional
from celery import shared_task
from django.db import transaction
from apps.core.models import InitialAIAnalysis, Overview, IP, Subdomain, URLResult
from c2_core.config.logging import log_function_call
from .common import _execute_ai_batch

logger = logging.getLogger(__name__)

@shared_task(bind=True)
@log_function_call()
def trigger_initial_ai_analysis(
    self, 
    ip_ids: List[int] = None, 
    subdomain_ids: List[int] = None, 
    url_ids: List[int] = None,
    overview_id: Optional[int] = None
):
    ip_ids = ip_ids or []
    subdomain_ids = subdomain_ids or []
    url_ids = url_ids or []
    
    overview = None
    if overview_id:
        overview = Overview.objects.filter(id=overview_id).first()

    analysis_ids = []
    with transaction.atomic():
        for ip_id in ip_ids:
            obj = InitialAIAnalysis.objects.create(ip_id=ip_id, status="PENDING")
            analysis_ids.append(obj.id)
        for sid in subdomain_ids:
            obj = InitialAIAnalysis.objects.create(subdomain_id=sid, status="PENDING")
            analysis_ids.append(obj.id)
        for uid in url_ids:
            obj = InitialAIAnalysis.objects.create(url_result_id=uid, status="PENDING")
            analysis_ids.append(obj.id)

    if analysis_ids:
        perform_initial_ai_analysis_batch.delay(analysis_ids)
        return f"已派發 {len(analysis_ids)} 個初步分析任務。"
    return "無資產需要分析。"

@shared_task(name="analyze_ai.tasks.periodic_initial_analysis_bootstrapper")
def periodic_initial_analysis_bootstrapper():
    logger.info("開始執行週期性初步 AI 分析引導 (Asset Discovery)")
    
    ips = IP.objects.filter(
        ports__state="open"
    ).exclude(
        highlighted_in_overview__isnull=False
    ).exclude(
        initial_ai_analyses__status__in=["PENDING", "RUNNING", "COMPLETED"]
    ).distinct()[:50]
    
    subs = Subdomain.objects.filter(
        is_resolvable=True, is_active=True
    ).exclude(
        highlighted_in_overview__isnull=False
    ).exclude(
        initial_ai_analyses__status__in=["PENDING", "RUNNING", "COMPLETED"]
    ).distinct()[:50]
    
    urls = URLResult.objects.exclude(
        highlighted_in_overview__isnull=False
    ).exclude(
        initial_ai_analyses__status__in=["PENDING", "RUNNING", "COMPLETED"]
    ).filter(
        status_code__in=[200, 301, 302, 403, 500]
    ).distinct()[:50]

    ip_ids = [ip.id for ip in ips]
    sub_ids = [s.id for s in subs]
    url_ids = [u.id for u in urls]

    if ip_ids or sub_ids or url_ids:
        logger.info(f"發現新資產: IPs({len(ip_ids)}), Subs({len(sub_ids)}), URLs({len(url_ids)})")
        trigger_initial_ai_analysis.delay(ip_ids=ip_ids, subdomain_ids=sub_ids, url_ids=url_ids)
        return f"已派發 {len(ip_ids) + len(sub_ids) + len(url_ids)} 個資產進行初步分析。"
    
    return "無新資產需要分析。"

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_initial_ai_analysis_batch(self, analysis_ids: List[int]):
    _execute_ai_batch(asset_type="initial", asset_ids=analysis_ids, task_self=self)
    process_initial_analysis_conversions.delay(analysis_ids)

@shared_task
def process_initial_analysis_conversions(analysis_ids: List[int]):
    from apps.core.models import InitialAIAnalysis, Overview
    
    analyses = InitialAIAnalysis.objects.filter(
        id__in=analysis_ids, 
        status="COMPLETED", 
        worth_deep_analysis=True,
        is_converted=False
    ).select_related('ip', 'subdomain', 'url_result')
    
    for a in analyses:
        asset = a.ip or a.subdomain or a.url_result
        if not asset:
            continue

        target = getattr(asset, 'target', None)
        if not target and a.url_result:
            related_subdomain = a.url_result.related_subdomains.filter(target__isnull=False).first()
            target = related_subdomain.target if related_subdomain else None

        ov = None
        # 1:1 關係下大幅簡化：若 target 存在，直接取得/建立其唯一 overview
        if target:
            ov, _ = Overview.objects.get_or_create(
                target=target,
                defaults={
                    "status": "PLANNING",
                    "summary": f"AI-Detected High Value Asset: {a.summary}",
                    "knowledge": {
                        "source": "ai_initial_triage",
                        "initial_analysis_id": a.id,
                        "inferred_purpose": a.inferred_purpose,
                    },
                },
            )
        else:
            # target 未知的罕見情況：用 asset.highlighted_in_overview 反查
            ov = asset.highlighted_in_overview.filter(
                status__in=["PLANNING", "EXECUTING"]
            ).first()

        # 若復用既有 overview，附加新資產資訊
        if ov and not ov.summary:
            ov.summary = f"AI-Detected High Value Asset: {a.summary}"
        elif ov and "added_asset_from_initial" not in (ov.knowledge or {}):
            ov.summary = f"{(ov.summary or '')}\n[新增高價值資產] {a.summary}"
            if not ov.knowledge:
                ov.knowledge = {}
            ov.knowledge[f"added_asset_from_initial_{a.id}"] = {
                "source": "ai_initial_triage",
                "inferred_purpose": a.inferred_purpose,
            }
            ov.save(update_fields=["summary", "knowledge"])
            logger.info(f"將高價值資產 {asset} 附加到現有 Overview#{ov.id}")
        
        if a.ip:
            ov.ips.add(a.ip)
        elif a.subdomain:
            ov.subdomains.add(a.subdomain)
        elif a.url_result:
            ov.url_results.add(a.url_result)
            related_subdomains = list(a.url_result.related_subdomains.all())
            if related_subdomains:
                ov.subdomains.add(*related_subdomains)

        if target and not ov.target_id:
            ov.target = target
            ov.save(update_fields=["target"])
            
        a.is_converted = True
        a.overview = ov
        a.save(update_fields=["is_converted", "overview"])
        logger.info(f"資產 {asset} 通過初步分析，已綁定到 Overview#{ov.id}。")

    # ═══════════════════════════════════════════════════════════════════
    # 鏈式觸發：為新建的 Overview 自動進入策略規劃
    # ═══════════════════════════════════════════════════════════════════
    newly_planning_overview_ids = set()
    for a in analyses:
        if a.overview_id and a.overview and a.overview.status == "PLANNING":
            newly_planning_overview_ids.add(a.overview_id)

    for ov_id in newly_planning_overview_ids:
        from .planning import propose_next_steps
        logger.info(f"[Chain] 自動觸發策略規劃 for Overview#{ov_id}")
        propose_next_steps.delay(ov_id)
