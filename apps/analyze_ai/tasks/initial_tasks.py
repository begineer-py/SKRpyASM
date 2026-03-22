"""
apps/analyze_ai/tasks/initial_tasks.py

初步 AI 分析 (Initial Triage) 任務。
核心功能：
1. 為 IP/Subdomain/URL 建立初步分析記錄。
2. 判斷資產用途並決定是否值得進行深入探查。
"""

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
    """
    【初步分析啟動】為資產建立 InitialAIAnalysis 記錄並派發任務。
    """
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
    """
    【週期性資產發現】查找尚未有 Overview 的資產並觸發初步 AI 分析。
    替代原本 scheduler 中的 regex 基礎 bootstrap。
    """
    logger.info("🚀 開始執行週期性初步 AI 分析引導 (Asset Discovery)")
    
    # 1. 查找沒有 Overview 且近期沒有 InitialAIAnalysis 的 IP
    ips = IP.objects.filter(
        ports__state="open"
    ).exclude(
        overviews__isnull=False
    ).exclude(
        initial_ai_analyses__status__in=["PENDING", "RUNNING", "COMPLETED"]
    ).distinct()[:50]
    
    # 2. 查找沒有 Overview 且近期沒有 InitialAIAnalysis 的 Subdomain
    subs = Subdomain.objects.filter(
        is_resolvable=True, is_active=True
    ).exclude(
        overviews__isnull=False
    ).exclude(
        initial_ai_analyses__status__in=["PENDING", "RUNNING", "COMPLETED"]
    ).distinct()[:50]
    
    # 3. 查找沒有 Overview 且近期沒有 InitialAIAnalysis 的 URLResult
    # 這裡可以保留一些基本的過濾邏輯，但不再是主要的過濾器
    urls = URLResult.objects.exclude(
        overviews__isnull=False
    ).exclude(
        initial_ai_analyses__status__in=["PENDING", "RUNNING", "COMPLETED"]
    ).filter(
        status_code__in=[200, 301, 302, 403, 500]
    ).distinct()[:50]

    ip_ids = [ip.id for ip in ips]
    sub_ids = [s.id for s in subs]
    url_ids = [u.id for u in urls]

    if ip_ids or sub_ids or url_ids:
        logger.info(f"   [+] 發現新資產: IPs({len(ip_ids)}), Subs({len(sub_ids)}), URLs({len(url_ids)})")
        trigger_initial_ai_analysis.delay(ip_ids=ip_ids, subdomain_ids=sub_ids, url_ids=url_ids)
        return f"已派發 {len(ip_ids) + len(sub_ids) + len(url_ids)} 個資產進行初步分析。"
    
    return "無新資產需要分析。"

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@log_function_call()
def perform_initial_ai_analysis_batch(self, analysis_ids: List[int]):
    """
    【初步分析執行】調用通用 AI 批次引擎。
    """
    # 注意：'initial' 的 asset_id_field 設為 'id'，因為它直接分析自己這條記錄中的 FK
    _execute_ai_batch(asset_type="initial", asset_ids=analysis_ids, task_self=self)
    
    # 【後處理】自動轉換為 Overview (Step 0)
    process_initial_analysis_conversions.delay(analysis_ids)

@shared_task
def process_initial_analysis_conversions(analysis_ids: List[int]):
    """
    檢查初步分析結果，如果 worth_deep_analysis 為 True，則轉換為 Overview。
    """
    from apps.core.models import InitialAIAnalysis, Overview, URLAIAnalysis, SubdomainAIAnalysis, IPAIAnalysis
    
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
            
        # 再次檢查是否已有 Overview (併發防護)
        if asset.overviews.exists():
            a.is_converted = True
            a.save()
            continue
            
        target = asset.target if hasattr(asset, 'target') else None
        
        # 建立 Overview
        ov = Overview.objects.create(
            target=target,
            status="PLANNING",
            summary=f"AI-Detected High Value Asset: {a.summary}",
            knowledge={
                "source": "ai_initial_triage",
                "initial_analysis_id": a.id,
                "inferred_purpose": a.inferred_purpose
            }
        )
        
        # 關聯資產並啟動深度分析
        if a.ip:
            ov.ips.add(a.ip)
            deep = IPAIAnalysis.objects.create(ip=a.ip, overview=ov, status="PENDING")
            from .ip import trigger_ai_analysis_for_ips
            trigger_ai_analysis_for_ips.delay([a.ip_id])
        elif a.subdomain:
            ov.subdomains.add(a.subdomain)
            deep = SubdomainAIAnalysis.objects.create(subdomain=a.subdomain, overview=ov, status="PENDING")
            from .subdomains import trigger_ai_analysis_for_subdomains
            trigger_ai_analysis_for_subdomains.delay([a.subdomain_id])
        elif a.url_result:
            ov.url_results.add(a.url_result)
            if a.url_result.subdomain:
                ov.subdomains.add(a.url_result.subdomain)
            deep = URLAIAnalysis.objects.create(url_result=a.url_result, overview=ov, status="PENDING")
            from .urls import trigger_ai_analysis_for_urls
            trigger_ai_analysis_for_urls.delay([a.url_result_id])
            
        a.is_converted = True
        a.overview = ov
        a.save()
        logger.info(f"   [🚀] 資產 {asset} 通過初步分析，已自動建立 Overview#{ov.id} 並啟動深度偵察。")
