#!/bin/bash

# API 基礎地址
API_URL="http://127.0.0.1:8000/api/scheduler/tasks"

# 函數：發送創建任務請求
create_task() {
    local task_name="$1"
    local task_path="$2"
    local batch_size="$3"
    local every_val="$4"
    local period_unit="$5"

    echo "正在創建任務: [$task_name] ..."

    # 構造 JSON payload
    json_payload=$(cat <<EOF
{
  "name": "${task_name}",
  "task": "${task_path}",
  "interval": {
    "every": ${every_val},
    "period": "${period_unit}"
  },
  "kwargs": "{\\"batch_size\\": ${batch_size}}"
}
EOF
)

    # 發送 CURL 請求
    response=$(curl -s -X POST "$API_URL" \
      -H "Content-Type: application/json" \
      -d "$json_payload")

    echo "響應: $response"
    echo "---------------------------------------------------"
}

echo "=== 開始批量註冊定時任務 (curl-cffi 加速版) ==="

# 1. Nmap IP 掃描 (維持慢速，這是為了網絡安全與隱蔽)
create_task \
    "Scan IPs without Nmap (Batch 3, every 10m)" \
    "scheduler.tasks.scan_ips_without_nmap_results" \
    3 \
    10 \
    "minutes"

# 2. Subdomain URL 發現 (維持中速)
create_task \
    "Scan Subdomains without URL (Batch 5, every 5m)" \
    "scheduler.tasks.scan_subdomains_without_url_results" \
    5 \
    5 \
    "minutes"

# 3. URL 內容抓取 (curl-cffi 加速！)
# 說明: 既然用 curl-cffi，資源消耗極低，直接拉高批次和頻率。
# 設置: 批次 20, 每 2 分鐘一次。
create_task \
    "Scan URLs missing response (Batch 20, every 2m)" \
    "scheduler.tasks.scan_urls_missing_response" \
    20 \
    2 \
    "minutes"

# 4. AI 分析 IP (維持慢速，等待積累)
create_task \
    "AI Analyze IPs (Batch 10, every 15m)" \
    "scheduler.tasks.trigger_scan_ips_without_ai_results" \
    10 \
    15 \
    "minutes"

# 5. AI 分析 Subdomains (維持慢速)
create_task \
    "AI Analyze Subdomains (Batch 10, every 15m)" \
    "scheduler.tasks.trigger_scan_subdomains_without_ai_results" \
    10 \
    15 \
    "minutes"

# 6. AI 分析 URLs (維持慢速)
create_task \
    "AI Analyze URLs (Batch 5, every 15m)" \
    "scheduler.tasks.trigger_scan_urls_without_ai_results" \
    5 \
    15 \
    "minutes"
# 7. Nuclei IP 漏洞掃描 (網絡層協議探測)
# 策略: 針對 Nmap 發現的 IP 進行網絡服務漏洞掃描。
# 設置: 批次 10, 每 10 分鐘一次。
create_task \
    "Nuclei Scan IPs (Batch 10, every 10m)" \
    "scheduler.tasks.trigger_scan_ips_without_nuclei_results" \
    10 \
    10 \
    "minutes"

# 8. Nuclei Subdomain 漏洞掃描 (子域名接管與 DNS 探測)
# 策略: 針對新發現的子域名進行自動化技術棧探測與 DNS 安全檢查。
# 設置: 批次 5, 每 10 分鐘一次。
create_task \
    "Nuclei Scan Subdomains (Batch 5, every 10m)" \
    "scheduler.tasks.trigger_scan_subdomains_without_nuclei_results" \
    5 \
    10 \
    "minutes"

# 9. Nuclei URL 深度漏洞掃描 (Web 漏洞挖掘)
# 策略: 針對抓取成功的 URL 進行 CVE 和高危漏洞挖掘。
# 設置: 批次 5, 每 5 分鐘一次 (URL 掃描較耗時，維持低批次高頻率)。
create_task \
    "Nuclei Scan URLs (Batch 5, every 5m)" \
    "scheduler.tasks.trigger_scan_urls_without_nuclei_results" \
    5 \
    5 \
    "minutes"
echo "=== 所有任務註冊請求已發送 ==="