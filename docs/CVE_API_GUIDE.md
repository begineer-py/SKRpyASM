# CVE Intelligence REST API 使用指南

## API 端点总览

所有 CVE Intelligence API 端点都挂载在 `/api/scanners/cve/` 下。

### 1. 查询特定 CVE

**端点**: `POST /api/scanners/cve/query`

**描述**: 查询特定 CVE ID 的详细情报，使用三层缓存策略（PostgreSQL → Redis → External API）

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/scanners/cve/query \
  -H "Content-Type: application/json" \
  -d '{"cve_id": "CVE-2021-44228"}'
```

**响应**: CVEIntelligenceOut (200) 或 ErrorSchema (404)

---

### 2. 根据技术名称搜索 CVE

**端点**: `POST /api/scanners/cve/search`

**描述**: 根据技术名称和版本搜索相关 CVE，支持严重性过滤和版本匹配

**请求参数**:
- `tech_name` (string, 必需): 技术名称，例如 "Apache", "Django", "nginx"
- `version` (string, 可选): 版本号，例如 "2.4.49"
- `severity_min` (string, 默认 "MEDIUM"): 最低严重性 (CRITICAL, HIGH, MEDIUM, LOW)
- `exploited_only` (boolean, 默认 false): 是否只返回已被利用的 CVE

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/scanners/cve/search \
  -H "Content-Type: application/json" \
  -d '{
    "tech_name": "Django",
    "version": "4.2.0",
    "severity_min": "HIGH",
    "exploited_only": false
  }'
```

**响应**: CVESearchResultOut (200)

---

### 3. 根据 Tags 搜索 CVE ⭐ 新功能

**端点**: `POST /api/scanners/cve/search_by_tags`

**描述**: 根据多个 tags 搜索相关技术的 CVE，支持 OR 查询（任一 tag 匹配即可）

**请求参数**:
- `tags` (array[string], 必需): 标签列表，例如 ["apache", "rce", "authentication"]
- `severity_min` (string, 默认 "MEDIUM"): 最低严重性
- `exploited_only` (boolean, 默认 false): 是否只返回已被利用的 CVE
- `limit` (integer, 默认 20): 返回结果数量限制（最多 100）

**使用场景**:
- 搜索特定攻击类型：`["rce", "remote code execution"]`
- 搜索特定技术栈：`["apache", "tomcat", "struts"]`
- 搜索特定漏洞类型：`["sql injection", "xss", "csrf"]`
- 组合搜索：`["authentication", "bypass", "privilege escalation"]`

**请求示例**:
```bash
# 搜索 Apache 相关的 RCE 漏洞
curl -X POST http://localhost:8000/api/scanners/cve/search_by_tags \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["apache", "rce"],
    "severity_min": "HIGH",
    "exploited_only": false,
    "limit": 10
  }'

# 搜索已被利用的认证绕过漏洞
curl -X POST http://localhost:8000/api/scanners/cve/search_by_tags \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["authentication", "bypass"],
    "severity_min": "CRITICAL",
    "exploited_only": true,
    "limit": 20
  }'
```

**响应**: CVESearchResultOut (200)

**排序规则**:
1. 优先显示 CISA KEV（已被利用的 CVE）
2. 按 CVSS 分数降序
3. 按 EPSS 分数降序

---

### 4. 获取技术栈 CVE 报告

**端点**: `GET /api/scanners/cve/techstack_report/{target_id}`

**描述**: 生成目标的技术栈 CVE 风险报告，分析所有已识别的技术栈

**请求示例**:
```bash
curl -X GET http://localhost:8000/api/scanners/cve/techstack_report/1
```

**响应**: TechStackCVEReportOut (200)

**响应字段**:
- `target_id`: 目标 ID
- `total_cves`: 总 CVE 数量
- `critical_count`: CRITICAL 级别 CVE 数量
- `high_count`: HIGH 级别 CVE 数量
- `kev_count`: CISA KEV CVE 数量
- `top_cves`: 前 10 个高危 CVE 列表

---

### 5. 批次豐富化 Vulnerability

**端点**: `POST /api/scanners/cve/enrich_vulnerabilities`

**描述**: 批次豐富化 Vulnerability 记录，从 template_id 提取 CVE ID 并关联 CVE 情报

**请求参数**:
- `vulnerability_ids` (array[int], 必需): Vulnerability ID 列表
- `callback_step_id` (int, 可选): Step ID for callback

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/scanners/cve/enrich_vulnerabilities \
  -H "Content-Type: application/json" \
  -d '{
    "vulnerability_ids": [1, 2, 3, 4, 5],
    "callback_step_id": 100
  }'
```

**响应**: SuccessSendToAISchema (202) - 异步任务已派发

---

### 6. 同步 TechStack CVE

**端点**: `POST /api/scanners/cve/sync_techstack`

**描述**: 同步目标的 TechStack CVE，对应 TechStack 到相关 CVE

**请求参数**:
- `target_id` (int, 必需): Target ID
- `callback_step_id` (int, 可选): Step ID for callback

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/scanners/cve/sync_techstack \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": 1,
    "callback_step_id": 101
  }'
```

**响应**: SuccessSendToAISchema (202) - 异步任务已派发

---

### 7. 手动同步 CISA KEV

**端点**: `POST /api/scanners/cve/sync_kev`

**描述**: 手动触发 CISA KEV 同步，抓取最新的已被利用漏洞目录

**请求参数**:
- `callback_step_id` (int, 可选): Step ID for callback

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/scanners/cve/sync_kev \
  -H "Content-Type: application/json" \
  -d '{"callback_step_id": 102}'
```

**响应**: SuccessSendToAISchema (202) - 异步任务已派发

---

## API Key 管理

### 添加 NVD API Key

NVD API Key 可以将速率限制从 5 req/30s 提升至 50 req/30s。

**申请 API Key**: https://nvd.nist.gov/developers/request-an-api-key

**添加到系统**:
```bash
curl -X POST http://localhost:8000/api/api_keys/ \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "nvd",
    "key_value": "your-nvd-api-key-here",
    "is_active": true,
    "description": "NVD API Key for CVE queries"
  }'
```

**验证支持**:
```bash
curl -X GET http://localhost:8000/api/api_keys/supported-services | grep nvd
```

---

## 使用场景示例

### 场景 1: 发现新技术后立即查询 CVE

```bash
# 1. 技术栈检测发现 Apache Struts 2.5.30
# 2. 立即查询相关 CVE
curl -X POST http://localhost:8000/api/scanners/cve/search \
  -H "Content-Type: application/json" \
  -d '{"tech_name": "Apache Struts", "version": "2.5.30", "severity_min": "HIGH"}'
```

### 场景 2: 搜索特定攻击类型的 CVE

```bash
# 搜索 RCE 相关的高危 CVE
curl -X POST http://localhost:8000/api/scanners/cve/search_by_tags \
  -H "Content-Type: application/json" \
  -d '{"tags": ["rce", "remote code execution"], "severity_min": "HIGH", "limit": 20}'
```

### 场景 3: 监控已被利用的漏洞

```bash
# 搜索 CISA KEV 中的认证相关漏洞
curl -X POST http://localhost:8000/api/scanners/cve/search_by_tags \
  -H "Content-Type: application/json" \
  -d '{"tags": ["authentication"], "exploited_only": true, "severity_min": "MEDIUM"}'
```

### 场景 4: 生成目标风险报告

```bash
# 获取目标的完整技术栈 CVE 报告
curl -X GET http://localhost:8000/api/scanners/cve/techstack_report/1
```

---

## 测试脚本

使用提供的测试脚本快速测试所有端点：

```bash
./test_cve_api.sh
```

---

## 注意事项

1. **三层缓存策略**: 查询优先使用本地数据库，减少 70% 的外部 API 请求
2. **异步任务**: 批次操作（enrich_vulnerabilities, sync_techstack, sync_kev）返回 202，任务在后台执行
3. **速率限制**: 建议申请 NVD API Key 以提高查询速率
4. **Tags 搜索**: 使用 OR 逻辑，任一 tag 匹配即返回结果
5. **结果排序**: Tags 搜索优先显示 CISA KEV，然后按 CVSS 分数排序

---

## 错误处理

- **404**: CVE 不存在或 Target/Vulnerability ID 无效
- **400**: 请求参数错误（例如 tags 为空）
- **500**: 服务器内部错误（查看日志获取详细信息）

所有错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```
