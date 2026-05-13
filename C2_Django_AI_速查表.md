# C2 Django AI - 代碼實踐速查表

## 快速導航

| 需求 | 文件位置 | 核心代碼 |
|------|--------|--------|
| 了解掃描器生命週期 | `apps/scanners/base_task.py` | `ScannerLifecycle` Context Manager |
| 了解 Nmap 掃描 | `apps/scanners/nmap_scanner/tasks/__init__.py` | `perform_nmap_scan()` 函數 |
| 了解 Nuclei 掃描 | `apps/scanners/nuclei_scanner/tasks/ip_scanner.py` | `perform_nuclei_scans_for_ip_batch()` |
| 了解 Layer 1 AI | `apps/ai_assistant/assistants.py` | `PersonalManagerAgent` 類 |
| 了解 Layer 2 AI | `apps/ai_assistant/assistants.py` | `HackerAssistantAgent` 類 |
| 了解 Layer 3 AI | `apps/analyze_ai/assistants.py` | `IPAnalyzerAgent` 等類 |
| 了解工具定義 | `django_ai_assistant/langchain/tools.py` | `@method_tool` 裝飾器 |
| 了解工具使用 | `django_ai_assistant/example/tour_guide/ai_assistants.py` | `TourGuideAIAssistant` 例子 |
| 了解數據模型 | `apps/core/models/` | 所有 Django Model 定義 |
| 了解 API | `apps/core/api.py` | REST API 端點 |

---

## 掃描器實踐速查

### 掃描器生命週期狀態

```
PENDING (等待中)
    ↓
RUNNING (執行中) ← with ScannerLifecycle() 進入時設置
    ↓
COMPLETED (完成) ← 正常退出時設置
    或
FAILED (失敗) ← 異常退出時設置 + error_message
```

### 建立新掃描器的最小代碼

```python
# 1. 定義 Celery Task
from celery import shared_task
from apps.scanners.base_task import ScannerLifecycle

@shared_task(bind=True)
def perform_my_scan(self, scan_id: int, target_id: int):
    scan = MyScan.objects.get(id=scan_id)
    
    with ScannerLifecycle(scan, logger) as lc:
        # 執行掃描邏輯
        result = run_my_scan_tool(target_id)
        lc.set_output(result)  # 可選：存儲原始輸出
        
        # 解析結果並保存到 DB
        parse_and_save_my_results(scan, result)
    
    return f"掃描完成"

# 2. 在 Layer 3 Agent 中暴露工具
@method_tool
def execute_my_scan(self, target_id: int) -> str:
    scan = MyScan.objects.create(target_id=target_id, status='PENDING')
    task = perform_my_scan.delay(scan.id, target_id)
    return f"掃描已啟動 (Task ID: {task.id})"
```

### 查詢掃描結果的方式

```python
# 查詢單個掃描狀態
scan = NmapScan.objects.get(id=123)
print(scan.status)  # PENDING / RUNNING / COMPLETED / FAILED
print(scan.error_message)  # 錯誤訊息（若有）
print(scan.nmap_output)  # 原始輸出

# 查詢所有掃描記錄
pending_scans = NmapScan.objects.filter(status='PENDING')
completed_scans = NmapScan.objects.filter(status='COMPLETED')

# 查詢掃描發現的結果
ports = Port.objects.filter(ip__id=ip_id)
for port in ports:
    print(f"{port.port_number}/{port.protocol}: {port.service_name}")
```

---

## AI Agent 實踐速查

### Layer 1 - 用戶交互層

```python
class PersonalManagerAgent(AIAssistant):
    id = "personal_manager_agent"
    model = "mistral-small-2603"
    
    def get_tools(self):
        # 暴露 Layer 2 作為工具
        tools = super().get_tools()
        tools.append(HackerAssistantAgent().as_tool())
        return tools
    
    @method_tool
    def my_tool(self) -> str:
        """執行什麼動作"""
        return "結果"
```

### Layer 2 - 戰略規劃層

```python
class HackerAssistantAgent(AIAssistant):
    id = "hacker_assistant_agent"
    model = "mistral-small-2603"
    
    def get_tools(self):
        tools = super().get_tools()
        
        # 添加數據庫查詢工具
        tools.append(QuerySQLDataBaseTool(db=db))
        
        # 添加 Layer 3 Agents 作為工具
        tools.append(AutomationAgent().as_tool())
        tools.append(IPAnalyzerAgent().as_tool())
        tools.append(SubdomainAnalyzerAgent().as_tool())
        tools.append(URLAnalyzerAgent().as_tool())
        
        return tools
    
    @method_tool
    def strategic_decision_tool(self) -> str:
        """戰略決策"""
        return "決策結果"
```

### Layer 3 - 具體執行層

```python
class IPAnalyzerAgent(AnalyzerMixin, AIAssistant):
    id = "ip_analyzer_agent"
    name = "IP Asset Analyzer"
    
    def get_instructions(self):
        # 從外部提示詞文件加載指令
        return _load_prompt(PROMPT_TEMPLATE_PATH)
    
    # 不需要 @method_tool，因為純分析 Agent
    # 由 Layer 2 調用並傳遞數據
```

### 工具調用工作流

```
用戶: "掃描目標 example.com"
    ↓
PersonalManagerAgent.invoke()
    ├─ AI 決策：調用 HackerAssistantAgent
    ↓
HackerAssistantAgent.invoke()
    ├─ @method_tool list_active_targets() → 獲取 Target ID
    ├─ AI 決策：調用 AutomationAgent
    ↓
AutomationAgent.invoke()
    ├─ @method_tool execute_nmap_scan(target_id=123)
    │  └─ Celery Task: perform_nmap_scan.delay()
    ├─ @method_tool check_nmap_results(scan_id=456)
    │  └─ 返回掃描結果
    └─ 返回執行摘要
    
    ↓ (返回到 Layer 2)
    └─ 返回到 Layer 1
        ↓
        返回到用戶
```

---

## 工具實踐速查

### 定義工具的方式

#### 方式 1：@method_tool 裝飾器

```python
class MyAssistant(AIAssistant):
    @method_tool
    def my_tool(self, param1: str, param2: int) -> str:
        """
        工具的文檔字符串（LLM 會讀取這個）
        
        Args:
            param1: 參數 1 的說明
            param2: 參數 2 的說明
        
        Returns:
            返回值說明
        """
        return f"結果: {param1} {param2}"
```

#### 方式 2：嵌套 Agent

```python
class MyAssistant(AIAssistant):
    def get_tools(self):
        tools = super().get_tools()
        
        # 將另一個 Agent 作為工具
        tools.append(
            SpecializedAgent().as_tool(
                description="這個工具的作用是..."
            )
        )
        
        return tools
```

### 工具的自動發現

```python
# LangChain 會自動發現並註冊所有 @method_tool 標記的方法
class MyAssistant(AIAssistant):
    def get_tools(self):
        # super().get_tools() 會自動返回所有 @method_tool 的方法
        return super().get_tools()
```

### 工具的參數類型支持

```python
@method_tool
def my_tool(
    self,
    str_param: str,           # 字符串
    int_param: int,           # 整數
    float_param: float,       # 浮點數
    bool_param: bool,         # 布爾值
    list_param: list,         # 列表
    dict_param: dict,         # 字典
    optional_param: str = None  # 可選參數
) -> str:
    """工具說明"""
    return "結果"
```

### 工具返回值格式

```python
@method_tool
def my_tool(self) -> str:
    # 返回 JSON 字符串（便於 AI 解析）
    import json
    data = {
        "status": "success",
        "data": [...],
        "message": "..."
    }
    return json.dumps(data)
```

---

## 數據模型速查

### 核心模型關係

```
Target (目標)
├─ Subdomain (子域名)
│  ├─ URLResult (URL)
│  │  └─ Vulnerability (漏洞)
│  └─ TechStack (技術棧)
└─ IP (IP)
   ├─ Port (端口)
   │  └─ Vulnerability (漏洞)
   └─ TechStack (技術棧)

Overview (戰略狀態) ← Layer 2 管理
├─ Step (執行步驟) ← Layer 3 記錄
└─ AttackVector (攻擊向量) ← Layer 3 記錄

掃描記錄
├─ NmapScan
├─ NucleiScan
├─ SubfinderScan
└─ ...

分析結果
├─ InitialAIAnalysis (初始分析)
└─ DetailedAnalysis (詳細分析)
```

### 常用查詢模式

```python
# 獲取目標的所有子域名
from apps.core.models import Target, Subdomain

target = Target.objects.get(id=1)
subdomains = Subdomain.objects.filter(target=target)

# 獲取子域名的所有 URL
urls = URLResult.objects.filter(subdomain__in=subdomains)

# 獲取所有漏洞
vulnerabilities = Vulnerability.objects.filter(
    affected_urls__subdomain__target=target
)

# 獲取技術棧
techstacks = TechStack.objects.filter(
    subdomains__target=target
)

# 獲取掃描歷史
nmap_scans = NmapScan.objects.filter(
    target=target,
    status='COMPLETED'
)

# 獲取發現的端口
ports = Port.objects.filter(
    ip__target=target,
    state='open'
)
```

---

## 常用命令速查

### 運行掃描器

```bash
# 啟動 Celery Worker
celery -A c2_core worker -l info

# 啟動 Celery Beat（定時任務）
celery -A c2_core beat -l info

# 查看 Celery 任務隊列
celery -A c2_core inspect active

# 清空任務隊列
celery -A c2_core purge
```

### 與 AI Agent 互動

```python
# 在 Django Shell 中測試
python manage.py shell

from apps.ai_assistant.assistants import PersonalManagerAgent
agent = PersonalManagerAgent()

# 調用 agent
response = agent.invoke({"input": "掃描 example.com"})
print(response)
```

### 查詢掃描結果

```python
from apps.core.models import NmapScan, Port

# 查詢最近的掃描
recent = NmapScan.objects.order_by('-created_at').first()
print(f"狀態: {recent.status}")
print(f"錯誤: {recent.error_message}")

# 查詢發現的端口
ports = Port.objects.filter(
    ip__address='192.168.1.1'
).order_by('port_number')

for port in ports:
    print(f"{port.port_number}/{port.protocol}: {port.state}")
```

---

## 調試技巧

### 查看日誌

```bash
# 查看 Django 應用日誌
tail -f logs/django.log

# 查看 Celery 任務日誌
tail -f logs/celery.log

# 查看特定應用日誌
tail -f logs/scanners.log
```

### 檢查掃描狀態

```python
from apps.core.models import NmapScan

# 查詢特定掃描
scan = NmapScan.objects.get(id=123)

# 詳細信息
print(f"ID: {scan.id}")
print(f"狀態: {scan.status}")
print(f"開始時間: {scan.started_at}")
print(f"完成時間: {scan.completed_at}")
print(f"錯誤訊息: {scan.error_message}")
print(f"原始輸出字符數: {len(scan.nmap_output) if scan.nmap_output else 0}")
```

### 手動觸發掃描

```python
from apps.core.models import NmapScan, Target, IP
from apps.scanners.nmap_scanner.tasks import perform_nmap_scan

# 建立掃描記錄
target = Target.objects.get(id=1)
ip = IP.objects.get(id=1)
scan = NmapScan.objects.create(
    target=target,
    ip=ip,
    status='PENDING'
)

# 手動觸發任務（不經過 Celery）
perform_nmap_scan(scan.id, ip.address, "-sV")
```

### 監控 AI Agent 執行

```python
from apps.ai_assistant.assistants import HackerAssistantAgent
import logging

# 啟用詳細日誌
logging.basicConfig(level=logging.DEBUG)

agent = HackerAssistantAgent()
response = agent.invoke({"input": "掃描目標"})

# 查看 LangChain 的詳細執行步驟
print(response)
```

---

## 常見錯誤和解決方案

| 錯誤 | 原因 | 解決方案 |
|------|------|--------|
| `ScannerLifecycle 狀態未更新` | 未使用 Context Manager | 確保使用 `with ScannerLifecycle(): ` |
| `Celery Task 未執行` | Worker 未啟動或隊列為空 | 啟動 Worker：`celery -A c2_core worker -l info` |
| `AI 工具未被發現` | 方法未使用 `@method_tool` 裝飾器 | 在方法上添加 `@method_tool` |
| `數據庫連接失敗` | 環境變數配置錯誤 | 檢查 `.env` 文件中的 DB 配置 |
| `AI 返回格式錯誤` | 工具返回值格式不符 | 確保返回字符串（JSON 或純文本） |
| `Layer 間通信失敗` | Overview 表未初始化 | 手動建立 Overview 記錄或使用 API |

---

## 性能優化建議

### 掃描器優化

```python
# 使用批量操作
Port.objects.bulk_create(ports, batch_size=1000)

# 使用 select_related 避免 N+1 查詢
ports = Port.objects.select_related('ip').filter(...)

# 使用 prefetch_related 預加載 M2M 關係
ports = Port.objects.prefetch_related('discovered_by_scans').filter(...)
```

### AI Agent 優化

```python
# 緩存 LLM 結果
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_analysis(data_hash):
    return expensive_analysis(data)

# 使用 Pydantic 模型進行快速驗證
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    risk_score: int
    vulnerabilities: list
```

### 數據庫優化

```python
# 使用索引
class MyScan(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE, db_index=True)
    status = models.CharField(max_length=20, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['target', 'status']),
        ]

# 使用分頁避免一次加載過多數據
from django.core.paginator import Paginator

all_results = Result.objects.all()
paginator = Paginator(all_results, 100)
for page_num in paginator.page_range:
    page = paginator.page(page_num)
    process_results(page.object_list)
```

---

## 相關文檔

- 完整指南：`C2_Django_AI_代码实践指南.md`
- 項目依賴：`requirements.txt` 和 `requirements/requirements.txt`
- Docker 部署：`docker/docker-compose.yml`
- 環境配置：`.env.example`

---

生成日期：2026-05-08
版本：1.0
快速查閱版
