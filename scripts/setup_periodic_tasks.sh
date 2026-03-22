#!/bin/bash

# scripts/setup_periodic_tasks.sh
# 一鍵設定所有自主滲透相關的定時任務

BASE_URL=${BASE_URL:-"http://localhost:8000"}
API_URL="${BASE_URL}/api/scheduler/tasks"

echo "🚀 開始初始化 C2 自主滲透週期性任務..."
echo "📍 目標 API: ${API_URL}"

# 輔助函式：發送 POST 請求建立任務
create_task() {
    local name=$1
    local task=$2
    local every=$3
    local period=$4
    local description=$5

    echo "--------------------------------------------------"
    echo "📦 正在檢查/建立任務: ${name}"
    
    payload=$(cat <<EOF
{
  "name": "$name",
  "task": "$task",
  "interval": {
    "every": $every,
    "period": "$period"
  },
  "description": "$description",
  "enabled": true,
  "args": "[]",
  "kwargs": "{}"
}
EOF
)

    curl -s -X POST "$API_URL" \
         -H "Content-Type: application/json" \
         -d "$payload" | python3 -m json.tool | grep -E "id|name|task"
}

# 1. 高價值資產引導 (Bootstrap) - 每 5 分鐘跑一次，發現大魚
create_task "Continuous High-Value Bootstrap" \
            "scheduler.tasks.trigger_high_value_bootstrap" \
            5 "minutes" \
            "自動掃描新發現的高價值資產並啟動 Overview 循環"

# 2. 自動 AI 規劃觸發 (Auto AI Analysis) - 每 30 秒鐘跑一次
create_task "Continuous AI Planning" \
            "scheduler.tasks.trigger_pending_ai_analyses" \
            30 "seconds" \
            "掃描隸屬於 Planning Overview 底下的 PENDING AI 分析並自動開始規劃"

# 4. Nuclei URL 弱點掃描觸發 - 每 30 秒鐘跑一次
create_task "Trigger Nuclei URL Scan" \
            "scheduler.tasks.trigger_scan_urls_without_nuclei_results" \
            30 "seconds" \
            "選出尚未掃描漏洞的 URL ID 並派發給 Nuclei"

# 5. Nuclei 子域名弱點掃描觸發 - 每 30 秒鐘跑一次
create_task "Trigger Nuclei Subdomain Scan" \
            "scheduler.tasks.trigger_scan_subdomains_without_nuclei_results" \
            30 "seconds" \
            "選出尚未掃描漏洞的子域名 ID 並派發給 Nuclei"

# 6. Nuclei IP 弱點掃描觸發 - 每 30 秒鐘跑一次
create_task "Trigger Nuclei IP Scan" \
            "scheduler.tasks.trigger_scan_ips_without_nuclei_results" \
            30 "seconds" \
            "選出尚未掃描漏洞的 IP ID 並派發給 Nuclei"

# 7. Nmap 端口掃描觸發 - 每 30 秒鐘跑一次
create_task "Trigger Nmap IP Scan" \
            "scheduler.tasks.scan_ips_without_nmap_results" \
            30 "seconds" \
            "查找無 Nmap 記錄的 IP 並觸發端口掃描"

# 8. GAU URL 搜刮觸發 - 每 30 秒鐘跑一次
create_task "Trigger GAU Subdomain Scan" \
            "scheduler.tasks.scan_subdomains_without_url_results" \
            30 "seconds" \
            "查找無被GAU掃描的子域名並觸發 URL 搜刮"

# 9. FlareSolverr HTML 抓取觸發 - 每 30 秒鐘跑一次
create_task "Trigger FlareSolverr Content Fetch" \
            "scheduler.tasks.scan_urls_missing_response" \
            5 "seconds" \
            "查找未抓取內容的 URL 並觸發 FlareSolverr"

# 10. Nuclei URL 技術棧分析觸發 - 每 30 秒鐘跑一次
create_task "Trigger Nuclei Tech Scan (URL)" \
            "scheduler.tasks.trigger_nuclei_tech_scan_url" \
            30 "seconds" \
            "選出尚未掃描技術棧的 URL 並派發"

# 11. Nuclei 子域名技術棧分析觸發 - 每 30 秒鐘跑一次
create_task "Trigger Nuclei Tech Scan (Subdomain)" \
            "scheduler.tasks.trigger_nuclei_tech_scan_subdomain" \
            30 "seconds" \
            "選出尚未掃描技術棧的 Subdomain 並派發"

# 12. JS 敏感資訊 AI 掃描觸發 - 每 30 秒鐘跑一次
create_task "Trigger JS AI Analyze" \
            "scheduler.tasks.trigger_scan_js" \
            30 "seconds" \
            "自動搜刮未分析 JS 透過 API 丟給 AI 掃描"

# 13. 故障恢復看門狗 (Watchdog) - 每 5 分鐘跑一次
create_task "Watchdog Stalled Overviews" \
            "scheduler.tasks.watchdog_stalled_overviews" \
            5 "minutes" \
            "檢查並恢復卡在 PLANNING 或 EXECUTING 狀態過久的 Overview"

echo "--------------------------------------------------"
echo "✅ 定時任務初始化完成！"
echo "💡 注意：請確保 celery worker 和 celery beat 服務已啟動。"
