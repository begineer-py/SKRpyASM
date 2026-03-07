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

echo "=== 開始註冊定時任務 (已調慢速度以優化性能) ==="

# --- 1. 基礎掃描與發現 (Discovery) ---

# Nmap IP 掃描 (放慢至 15 分鐘一次)
create_task \
    "Scan IPs without Nmap (Batch 1, every 3m)" \
    "scheduler.tasks.scan_ips_without_nmap_results" \
    1 \
    3 \
    "minutes"

# Subdomain 轉 URL (放慢至 10 分鐘一次)
create_task \
    "Scan Subdomains to URL (Batch 1, every 2m)" \
    "scheduler.tasks.scan_subdomains_without_url_results" \
    1 \
    2 \
    "minutes"

# URL 內容抓取 (原本 5 秒太快，改為 2 分鐘一次，批次稍微加大)
create_task \
    "Scan URLs missing response (Batch 1, every 12)" \
    "scheduler.tasks.scan_urls_missing_response" \
    1 \
    12 \
    "seconds"


# --- 2. Nuclei 漏洞與技術棧掃描 (Vulnerability Scanning) ---

# Nuclei URL 技術掃描
create_task \
    "Nuclei Tech Scan URL (Batch 1, every 20s)" \
    "scheduler.tasks.trigger_nuclei_tech_scan_url" \
    1 \
    20 \
    "seconds"
create_task \
    "Nuclei Tech Scan Subdomain (Batch 1, every 20s)" \
    "scheduler.tasks.trigger_nuclei_tech_scan_subdomain" \
    1 \
    20 \
    "seconds"

# Nuclei IP 漏洞掃描
create_task \
    "Nuclei Scan IPs (Batch 1, every 1m)" \
    "scheduler.tasks.trigger_scan_ips_without_nuclei_results" \
    1 \
    1 \
    "minutes"

# Nuclei Subdomain 漏洞掃描
create_task \
    "Nuclei Scan Subdomains (Batch 1, every 1m)" \
    "scheduler.tasks.trigger_scan_subdomains_without_nuclei_results" \
    1 \
    1 \
    "minutes"

# Nuclei URL 深度掃描
create_task \
    "Nuclei Scan URLs (Batch 1, every 1m)" \
    "scheduler.tasks.trigger_scan_urls_without_nuclei_results" \
    1 \
    1 \
    "minutes"


# --- 3. JS 掃描與分析 ---

# JavaScript 文件掃描
create_task \
    "Scan JS Files (Batch 1, every 6secs)" \
    "scheduler.tasks.trigger_scan_js" \
    1 \
    6 \
    "seconds"


# --- 4. AI 智慧分析 (AI Analysis) ---

# AI 分析 IP
create_task \
    "AI Analyze IPs (Batch 1, every 1m)" \
    "scheduler.tasks.trigger_scan_ips_without_ai_results" \
    1 \
    1 \
    "minutes"

# AI 分析 Subdomains
create_task \
    "AI Analyze Subdomains (Batch 1, every 1m)" \
    "scheduler.tasks.trigger_scan_subdomains_without_ai_results" \
    1 \
    1 \
    "minutes"

# AI 分析 URLs
create_task \
    "AI Analyze URLs (Batch 1, every 1m)" \
    "scheduler.tasks.trigger_scan_urls_without_ai_results" \
    1 \
    1 \
    "minutes"

echo "=== 所有任務註冊完成 ==="