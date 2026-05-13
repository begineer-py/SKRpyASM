import os
import django
import sys

# 初始化 Django 環境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "c2_core.settings")
django.setup()

from apps.core.models import Target, Seed, URLResult, Subdomain
import asgiref.sync

def main():
    target_name = "AI自動化測試靶場"
    
    print(f"[*] 嘗試獲取或建立 Target: {target_name}...")
    target, created = Target.objects.get_or_create(
        name=target_name,
        defaults={"description": "為 Automation Agent 準備的自動化測試靶場"}
    )
    if created:
        print(f"  [+] 新建立 Target ID: {target.id}")
    else:
        print(f"  [=] 已存在 Target ID: {target.id}")

    # 1. 建立 Domain 種子
    domain_value = "vuln-f9wi.onrender.com"
    print(f"[*] 嘗試獲取或建立 DOMAIN Seed: {domain_value}...")
    seed_domain, created_dom = Seed.objects.get_or_create(
        target=target, 
        type="DOMAIN", 
        value=domain_value
    )
    
    # 同步建立 Subdomain 資產並關聯
    subdomain, sub_created = Subdomain.objects.get_or_create(
        target=target,
        name=domain_value
    )
    subdomain.which_seed.add(seed_domain)
    
    if created_dom:
        print(f"  [+] 新建立 DOMAIN Seed ID: {seed_domain.id}")
    else:
        print(f"  [=] 已存在 DOMAIN Seed ID: {seed_domain.id}")

    # 2. 建立 URL 種子
    url_value = "https://vuln-f9wi.onrender.com/"
    print(f"[*] 嘗試獲取或建立 URL Seed: {url_value}...")
    seed_url, created_url = Seed.objects.get_or_create(
        target=target,
        type="URL",
        value=url_value
    )
    
    # 同步建立 URLResult 資產
    url_result, url_created = URLResult.objects.get_or_create(
        target=target,
        url=url_value,
        defaults={
            "discovery_source": "MANUAL",
            "content_fetch_status": "PENDING"
        }
    )
    
    if created_url:
        print(f"  [+] 新建立 URL Seed ID: {seed_url.id}")
    else:
        print(f"  [=] 已存在 URL Seed ID: {seed_url.id}")
        
    print("\n✅ 測試案例與所需種子腳本執行完畢！可前往前端確認是否有出現。")

if __name__ == "__main__":
    main()
