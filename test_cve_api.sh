#!/bin/bash
# CVE Intelligence API 测试脚本

BASE_URL="http://localhost:8000/api/scanners/cve"

echo "=== CVE Intelligence API 测试 ==="
echo ""

# 1. 查询特定 CVE
echo "1. 查询 CVE-2021-44228 (Log4Shell)"
curl -s -X POST "$BASE_URL/query" \
  -H "Content-Type: application/json" \
  -d '{"cve_id": "CVE-2021-44228"}' | python -m json.tool | head -30
echo ""
echo "---"
echo ""

# 2. 搜索技术的 CVE
echo "2. 搜索 Apache 相关的 HIGH 以上 CVE"
curl -s -X POST "$BASE_URL/search" \
  -H "Content-Type: application/json" \
  -d '{"tech_name": "Apache", "severity_min": "HIGH"}' | python -m json.tool | head -40
echo ""
echo "---"
echo ""

# 3. 根据 tags 搜索 CVE（新功能）
echo "3. 根据 tags 搜索 CVE: [\"apache\", \"rce\"]"
curl -s -X POST "$BASE_URL/search_by_tags" \
  -H "Content-Type: application/json" \
  -d '{"tags": ["apache", "rce"], "severity_min": "HIGH", "limit": 10}' | python -m json.tool | head -40
echo ""
echo "---"
echo ""

# 4. 搜索已被利用的 CVE
echo "4. 搜索已被利用的 CVE (CISA KEV)"
curl -s -X POST "$BASE_URL/search_by_tags" \
  -H "Content-Type: application/json" \
  -d '{"tags": ["remote"], "exploited_only": true, "severity_min": "CRITICAL", "limit": 5}' | python -m json.tool | head -40
echo ""
echo "---"
echo ""

# 5. 验证 NVD 在支持的服务列表中
echo "5. 验证 NVD API Key 支持"
curl -s -X GET "http://localhost:8000/api/api_keys/supported-services" | python -m json.tool | grep -A 2 -B 2 "nvd"
echo ""

echo "=== 测试完成 ==="
