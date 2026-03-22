#!/usr/bin/env python3
"""
scripts/bootstrap_high_value_overviews.py

高價值資產引導腳本 (High-Value Recon Bootstrapper)
─────────────────────────────────────────────────
用途:
  1. 掃描資料庫中所有的 IP / Subdomain / URLResult。
  2. 根據「高價值」過濾邏輯（如動態參數、特定端口、敏感路徑）篩選資產。
  3. 為篩選出的資產建立首個 `Overview` 節點。
  4. 整合現有的 `AIAnalysis` 紀錄內容作為初始 Knowledge。
"""

import os
import sys
import django
from django.db.models import Q, Count

# 設定 Django 環境
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "c2_core.settings")
django.setup()

from apps.core.models import IP, Subdomain, URLResult, Overview, IPAIAnalysis, SubdomainAIAnalysis, URLAIAnalysis


def _collect_techs(asset_type: str, asset) -> list:
    """
    從資料庫現有的 techstack 紀錄中提取技術棧清單，用於預填 Overview.techs。
    """
    techs = []
    if asset_type == "subdomain":
        for t in asset.techstacks.all():
            entry = t.name
            if t.version:
                entry += f" {t.version}"
            if t.categories:
                entry += f" ({', '.join(t.categories) if isinstance(t.categories, list) else t.categories})"
            techs.append(entry)
    elif asset_type == "url":
        for t in asset.techstacks.all():
            entry = t.name
            if t.version:
                entry += f" {t.version}"
            techs.append(entry)
    elif asset_type == "ip":
        # IP 沒有直接的 techstack，但可從關聯子域名收集
        for sub_ip in asset.subdomain_ips.select_related('subdomain').all():
            for t in sub_ip.subdomain.techstacks.all():
                entry = t.name
                if t.version:
                    entry += f" {t.version}"
                if entry not in techs:
                    techs.append(entry)
    return techs


def bootstrap_overviews():
    print("\n" + "="*50)
    print(" 🚀 開始高價值資產引導任務 (Bootstrapping Overviews)")
    print("="*50)

    # 1. 過濾 URL ──────────────────────────────────────────────
    print("\n🔍 正在掃描高價值 URLResult...")
    
    # 過濾條件: 
    # - 包含動態參數 (?, &)
    # - 關鍵路徑 (admin, api, login, config, upload)
    # - 特定副檔名 (.php, .asp, .jsp, .cgi, .action, .do)
    # - 成功的狀態碼 (200, 301, 302, 403)
    # - 排除靜態資源
    high_value_urls = URLResult.objects.filter(
        Q(url__contains="?") | Q(url__contains="&") |
        Q(url__regex=r"/(admin|api|login|config|upload|setup|shell|cmd|exec|db)/") |
        Q(url__regex=r"\.(php|asp|aspx|jsp|cgi|jspx|action|do|json|xml|yaml|bak|phtml)$")
    ).filter(
        status_code__in=[200, 301, 302, 403, 500]
    ).exclude(
        url__regex=r"\.(css|js|png|jpg|jpeg|gif|ico|woff|woff2|ttf|svg|pdf|map)$"
    ).distinct()

    print(f"   發現 {high_value_urls.count()} 個高價值 URL")
    
    for url in high_value_urls.prefetch_related("techstacks"):
        if not Overview.objects.filter(url_results=url).exists():
            techs = _collect_techs("url", url)
            ov = Overview.objects.create(
                status="PLANNING",
                summary=f"Automated recon discovery for URL: {url.url[:50]}...",
                knowledge={"source": "bootstrap_recon", "initial_url": url.url},
                techs=techs if techs else None,
            )
            ov.url_results.add(url)
            # 關聯子域名 (如果有)
            if url.subdomain:
                ov.subdomains.add(url.subdomain)
            tech_str = f" | techs: {', '.join(techs[:3])}" if techs else ""
            
            # [ADD] 建立首個 PENDING 分析紀錄以啟動循環
            URLAIAnalysis.objects.create(
                url_result=url,
                overview=ov,
                status="PENDING"
            )
            print(f"   [+] 建立 Overview#{ov.id} & 啟動 AI 規劃 for URL: {url.url[:60]}{tech_str}")

    # 2. 過濾 IP ────────────────────────────────────────────────
    print("\n🔍 正在掃描高價值 IP (排除通用/空端口)...")
    
    # 過濾條件: 有開放端口，且不只是常見的 80/443 (可選)
    high_value_ips = IP.objects.annotate(
        open_port_count=Count('ports', filter=Q(ports__state='open'))
    ).filter(open_port_count__gt=0).distinct()

    print(f"   發現 {high_value_ips.count()} 個已掃描且有開放端口的 IP")
    
    for ip in high_value_ips.prefetch_related("subdomain_ips__subdomain__techstacks"):
        if not Overview.objects.filter(ips=ip).exists():
            # 檢查是否有舊的 AI 分析可以繼承
            old_analysis = IPAIAnalysis.objects.filter(ip=ip, status="COMPLETED").first()
            techs = _collect_techs("ip", ip)

            ov = Overview.objects.create(
                status="PLANNING",
                summary=f"Automated recon discovery for IP: {ip.ipv4 or ip.ipv6}",
                knowledge={
                    "source": "bootstrap_recon",
                    "history": old_analysis.summary if old_analysis else "New recon base",
                    "initial_ip": ip.ipv4 or ip.ipv6
                },
                techs=techs if techs else None,
                risk_score=old_analysis.risk_score if old_analysis else 0
            )
            ov.ips.add(ip)
            tech_str = f" | techs: {', '.join(techs[:3])}" if techs else ""
            
            # [ADD] 建立首個 PENDING 分析紀錄以啟動循環
            IPAIAnalysis.objects.create(
                ip=ip,
                overview=ov,
                status="PENDING"
            )
            print(f"   [+] 建立 Overview#{ov.id} & 啟動 AI 規劃 for IP: {ip.ipv4 or ip.ipv6}{tech_str}")

    # 3. 過濾子域名 ──────────────────────────────────────────────
    print("\n🔍 正在掃描高價值子域名...")
    
    high_value_subs = Subdomain.objects.filter(is_resolvable=True, is_active=True).distinct()
    
    print(f"   發現 {high_value_subs.count()} 個可解析且活躍的子域名")

    for sub in high_value_subs.prefetch_related("techstacks"):
        if not Overview.objects.filter(subdomains=sub).exists():
            old_analysis = SubdomainAIAnalysis.objects.filter(subdomain=sub, status="COMPLETED").first()
            techs = _collect_techs("subdomain", sub)
            ov = Overview.objects.create(
                status="PLANNING",
                summary=f"Automated recon discovery for Subdomain: {sub.name}",
                knowledge={
                    "source": "bootstrap_recon",
                    "history": old_analysis.summary if old_analysis else "New sub discovery",
                    "initial_domain": sub.name
                },
                techs=techs if techs else None,
                risk_score=old_analysis.risk_score if old_analysis else 0
            )
            ov.subdomains.add(sub)
            tech_str = f" | techs: {', '.join(techs[:3])}" if techs else ""
            
            # [ADD] 建立首個 PENDING 分析紀錄以啟動循環
            SubdomainAIAnalysis.objects.create(
                subdomain=sub,
                overview=ov,
                status="PENDING"
            )
            print(f"   [+] 建立 Overview#{ov.id} & 啟動 AI 規劃 for Subdomain: {sub.name}{tech_str}")

    print("\n" + "="*50)
    print(" ✅ 引導任務完成！已準備好進入自主滲透循環。")
    print("="*50 + "\n")

if __name__ == "__main__":
    bootstrap_overviews()
