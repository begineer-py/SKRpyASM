#!/bin/bash

API_BASE="http://127.0.0.1:8000/api/scheduler/tasks"

update_task() {
    local id="$1"
    local name="$2"
    local task_path="$3"
    local batch_size="$4"

    echo "正在更新任務 ID ${id}: [${name}] ..."
    echo " -> 設定為: 每 1 分鐘執行一次, 每次處理 ${batch_size} 個目標"

    # 構造 JSON payload (注意轉義)
    json_payload=$(cat <<EOF
{
  "name": "${name}",
  "task": "${task_path}",
  "interval": {
    "every": 1,
    "period": "minutes"
  },
  "kwargs": "{\\"batch_size\\": ${batch_size}}",
  "enabled": true
}
EOF
)

    # 發送 PUT 請求
    response=$(curl -s -X PUT "${API_BASE}/${id}" \
      -H "Content-Type: application/json" \
      -d "$json_payload")

    echo "API 響應: $response"
    echo "---------------------------------------------------"
}

echo "=== 開始調整 Nuclei 掃描頻率 (高頻低負載模式) ==="

# 1. Update Nuclei Scan URLs (ID 11)
# 原速: 5/5m = 1/m -> 新速: 1/1m
update_task \
    11 \
    "Nuclei Scan URLs (Batch 1, every 1m)" \
    "scheduler.tasks.trigger_scan_urls_without_nuclei_results" \
    1

# 2. Update Nuclei Scan Subdomains (ID 10)
# 原速: 5/10m = 0.5/m -> 新速: 1/1m (最小單位限制，稍微加速)
update_task \
    10 \
    "Nuclei Scan Subdomains (Batch 1, every 1m)" \
    "scheduler.tasks.trigger_scan_subdomains_without_nuclei_results" \
    1

# 3. Update Nuclei Scan IPs (ID 9)
# 原速: 10/10m = 1/m -> 新速: 1/1m
update_task \
    9 \
    "Nuclei Scan IPs (Batch 1, every 1m)" \
    "scheduler.tasks.trigger_scan_ips_without_nuclei_results" \
    1

echo "=== 任務更新完成：已切換為每分鐘平滑掃描模式 ==="