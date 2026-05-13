# C2 Django AI - 代碼實踐詳解指南

## 目錄
1. [項目依賴統計](#項目依賴統計)
2. [第一部分：掃描器部分](#第一部分掃描器部分)
3. [第二部分：AI 調用部分](#第二部分ai-調用部分)
4. [第三部分：工具部分](#第三部分工具部分)
5. [數據流圖表](#數據流圖表)
6. [核心設計模式](#核心設計模式總結)
7. [關鍵文件清單](#關鍵文件清單)

---

## 項目依賴統計

### Python 後端依賴
- **核心框架**：Django 5.2.4 + Django Ninja 1.4.5 + DRF 3.16
- **AI/LLM**：LangChain 0.1.16、Anthropic、OpenAI、LiteLLM
- **任務隊列**：Celery 5.5.3 + Redis 5.2.1
- **數據庫**：PostgreSQL 14 + psycopg2-binary 2.9.10
- **GraphQL**：gql 4.0.0 + Hasura GraphQL Engine v2.36.0
- **安全掃描工具**：
  - Nmap (python-nmap 0.7.1)
  - Wappalyzer (python-Wappalyzer 0.3.1)
  - WAF 檢測 (wafw00f 2.3.2)
  - DNS (dnspython 2.7.0, tldextract 5.3.0)
- **總計**：63 個核心依賴，展開後 401 個完整依賴

### Node.js 前端依賴
- **框架**：React 19.1.0 + Vite 7.0.4 + TypeScript 5.8.3
- **GraphQL**：Apollo Client 4.1.9
- **路由**：react-router-dom 7.7.1
- **Markdown**：react-markdown 10.1.0
- **網絡**：axios 1.11.0
- **共5個 package.json** 分布在不同模塊

### 系統級依賴
- **50 個 APT 包**：開發工具、編譯器、加密庫、安全工具等
- **Python 開發**：python3-dev, python3-pip, python3-venv
- **編譯工具**：build-essential, gcc
- **加密庫**：libssl-dev, libffi-dev
- **XML 處理**：libxml2-dev, libxslt1-dev
- **安全掃描工具**：nmap, masscan, metasploit-framework
- **數據庫**：postgresql-client, mysql-client, sqlite3

### Docker 微服務堆棧
```
- PostgreSQL 14 (Port 5432)
- Redis 8.0 (Port 6379)
- Hasura GraphQL Engine v2.36.0 (Port 8085)
- NocoDB (Port 8081)
- FlareSolverr (Port 8191)
- FlareProxyGo (Port 8192 & 1337)
```

---

## 第一部分：掃描器部分

### 1.1 掃描器生命週期管理器

**文件位置**：`apps/scanners/base_task.py`

掃描器生命週期管理器是所有掃描器的基礎，採用 **Context Manager** 設計模式實現狀態機管理。

```python
"""
apps/scanners/base_task.py

掃描任務生命週期管理器 (Scanner Lifecycle Manager)

將所有掃描器共用的 PENDING → RUNNING → COMPLETED / FAILED 狀態機
封裝進一個 Context Manager，各掃描任務只需 `with ScannerLifecycle(record, logger):` 即可。

使用範例::

    @shared_task(bind=True)
    def perform_nmap_scan(self, scan_id: int, ip: str):
        scan = NmapScan.objects.get(id=scan_id)
        with ScannerLifecycle(scan, logger) as lc:
            process = subprocess.run(...)
            lc.set_output(process.stdout)
            parse_and_save_nmap_results(scan, process.stdout, ip)
        # 離開 with 時，狀態自動寫入 COMPLETED（或 FAILED）及 completed_at
"""

from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class ScannerLifecycle:
    """
    掃描任務生命週期 Context Manager。

    進入 with 區塊時：
        - 設定 scan_record.status = "RUNNING"
        - 設定 scan_record.started_at = now()
        - 儲存變更

    正常退出時：
        - 設定 scan_record.status = "COMPLETED"
        - 設定 scan_record.completed_at = now()
        - 儲存變更

    例外退出時：
        - 設定 scan_record.status = "FAILED"
        - 設定 scan_record.error_message = str(exception)
        - 設定 scan_record.completed_at = now()
        - 儲存變更
        - **不抑制例外**（繼續向上拋出）

    Attributes:
        record:  任何帶有 status / started_at / completed_at / error_message 欄位的 Django Model。
        log:     Logger 實例，用於輸出狀態轉換資訊。
        _output_field: (可選) 要把 raw output 存入的欄位名稱，預設 None（不存）。
        _output_value: set_output() 所設定的值。
        _save_fields:  (可選) 覆寫最終 save() 的 update_fields。若為 None，則全欄位存。
    """

    def __init__(
        self,
        record,
        log=logger,
        output_field=None,
        save_fields=None,
    ):
        self.record = record
        self.log = log
        self._output_field = output_field
        self._output_value = None
        self._save_fields = save_fields
        self._success = False

    def set_output(self, raw_output: str) -> None:
        """
        暫存原始輸出，結束時若有設定 output_field 則自動寫入 record。
        """
        self._output_value = raw_output

    def __enter__(self):
        record = self.record
        record.status = "RUNNING"
        record.started_at = timezone.now()
        # 只更新必要欄位，避免意外覆蓋其他資料
        record.save(update_fields=["status", "started_at"])
        self.log.info(
            f"[ScannerLifecycle] {record.__class__.__name__} ID={record.pk} — 狀態更新為 RUNNING"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        record = self.record

        if exc_type is None:
            # ── 正常完成 ─────────────────────────────────────────────
            record.status = "COMPLETED"
            self._success = True
            self.log.info(
                f"[ScannerLifecycle] {record.__class__.__name__} ID={record.pk} — 狀態更新為 COMPLETED"
            )
        else:
            # ── 例外發生 ─────────────────────────────────────────────
            record.status = "FAILED"
            error_msg = str(exc_val)[:2000]  # 截斷超長錯誤訊息
            if hasattr(record, "error_message"):
                record.error_message = error_msg
            self.log.error(
                f"[ScannerLifecycle] {record.__class__.__name__} ID={record.pk} — "
                f"例外: {exc_type.__name__}: {error_msg}"
            )

        record.completed_at = timezone.now()

        # ── 存入 raw output（如有需要）────────────────────────────────
        if self._output_field and self._output_value is not None:
            setattr(record, self._output_field, self._output_value)

        # ── 決定 save 的欄位 ────────────────────────────────────────
        save_kwargs = {}
        if self._save_fields is not None:
            base_fields = {"status", "completed_at"}
            if hasattr(record, "error_message") and not self._success:
                base_fields.add("error_message")
            if self._output_field and self._output_value is not None:
                base_fields.add(self._output_field)
            save_kwargs["update_fields"] = list(base_fields | set(self._save_fields))

        try:
            record.save(**save_kwargs)
        except Exception as save_err:
            self.log.exception(
                f"[ScannerLifecycle] 儲存最終狀態失敗 for "
                f"{record.__class__.__name__} ID={record.pk}: {save_err}"
            )

        # 不抑制原始例外，讓 Celery / 呼叫者決定重試策略
        return False
```

**設計模式**：Context Manager（確保狀態轉換的原子性）

**特點**：
- 自動狀態轉換
- 異常處理與錯誤日誌
- 原始輸出存儲
- 選擇性欄位更新

---

### 1.2 Nmap 掃描器實現

**文件位置**：`apps/scanners/nmap_scanner/tasks/__init__.py`

```python
import logging
import subprocess
import shlex
import xml.etree.ElementTree as ET

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from typing import Optional

from apps.core.models import NmapScan, Port, IP
from apps.core.utils import with_auto_callback
from apps.scanners.base_task import ScannerLifecycle

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="nmap_scanner.tasks.perform_nmap_scan")
@with_auto_callback
def perform_nmap_scan(
    self,
    scan_id: int,
    ip_address: str,
    nmap_args: str,
    callback_step_id: Optional[int] = None,
):
    """
    執行 Nmap 掃描，解析結果，並將情報存入資料庫。
    使用 ScannerLifecycle 管理 PENDING → RUNNING → COMPLETED / FAILED 狀態機。
    
    流程：
    1. 從DB獲取掃描記錄
    2. 檢查狀態是否為 PENDING
    3. 執行 nmap 命令
    4. 使用 ScannerLifecycle 管理狀態
    5. 解析 XML 結果
    6. 儲存到資料庫
    """
    logger.info(
        f"任務 [{self.request.id}] 領取命令：開始處理 NmapScan ID: {scan_id} "
        f"for IP: {ip_address} (Step: {callback_step_id})"
    )

    try:
        scan_record = NmapScan.objects.get(id=scan_id)
    except NmapScan.DoesNotExist:
        logger.error(f"找不到 NmapScan 記錄，ID: {scan_id}")
        return f"Nmap 掃描中止：找不到 NmapScan ID {scan_id}"

    if scan_record.status != "PENDING":
        logger.warning(
            f"Scan ID {scan_id} 狀態為 {scan_record.status}，非 PENDING。任務終止。"
        )
        return f"Scan ID {scan_id} not in PENDING state."

    command = f"nmap {nmap_args} {ip_address}"
    logger.info(f"準備執行命令: {command}")

    with ScannerLifecycle(scan_record, logger, output_field="nmap_output") as lc:
        process = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes
        )

        if process.returncode != 0:
            raise RuntimeError(
                f"Nmap 執行失敗，返回碼: {process.returncode}. "
                f"Stderr: {process.stderr[:500]}"
            )

        xml_output = process.stdout
        lc.set_output(xml_output)  # 存入 nmap_output 欄位
        logger.info(f"NmapScan ID {scan_id} 執行完畢，準備解析 XML 結果。")
        parse_and_save_nmap_results(scan_record, xml_output, ip_address)

    logger.info(f"NmapScan ID {scan_id} 最終狀態: {scan_record.status}")
    return f"Nmap 掃描完成。IP: {ip_address}"


def parse_and_save_nmap_results(
    scan_record: NmapScan, xml_output: str, ip_address: str
):
    """
    解析 nmap XML 輸出並更新 Port 資產庫。
    """
    try:
        # 1. 獲取 IP 對象
        ip_obj = IP.objects.filter(address=ip_address).first()

        if not ip_obj:
            logger.error(f"解析失敗：資料庫找不到 IP {ip_address}")
            return

        root = ET.fromstring(xml_output)

        with transaction.atomic():
            for host in root.findall("host"):
                ports_element = host.find("ports")
                if ports_element is None:
                    continue

                for port_element in ports_element.findall("port"):
                    try:
                        port_number = int(port_element.get("portid"))
                        protocol = port_element.get("protocol")

                        state_element = port_element.find("state")
                        state = (
                            state_element.get("state")
                            if state_element is not None
                            else "unknown"
                        )

                        service_element = port_element.find("service")
                        service_name = (
                            service_element.get("name")
                            if service_element is not None
                            else None
                        )
                        service_version = (
                            service_element.get("version")
                            if service_element is not None
                            else None
                        )

                        # 使用 update_or_create 更新或創建端口記錄
                        port_obj, created = Port.objects.update_or_create(
                            ip=ip_obj,
                            port_number=port_number,
                            protocol=protocol,
                            defaults={
                                "state": state,
                                "service_name": service_name,
                                "service_version": service_version,
                                "last_scan_id": scan_record.id,
                                "last_scan_type": "NmapScan",
                                "last_seen": timezone.now(),
                            },
                        )

                        # 處理 M2M 關係
                        port_obj.discovered_by_scans.add(scan_record)

                    except Exception as loop_e:
                        logger.warning(f"解析單個端口時出錯 (跳過): {loop_e}")
                        continue

        logger.info(f"IP {ip_address} 的端口數據已更新。")

    except Exception as e:
        logger.exception(f"解析 XML 或存儲數據時出錯: {e}")
        raise
```

**關鍵特性**：
- 使用 `@shared_task` 進行非同步 Celery 任務調度
- `@with_auto_callback` 裝飾器用於自動回調機制
- Context Manager 確保狀態一致性
- XML 解析與數據庫原子操作
- 詳細的日誌記錄

---

### 1.3 Nuclei 掃描器實現

**文件位置**：`apps/scanners/nuclei_scanner/tasks/ip_scanner.py`

```python
"""
apps/nuclei_scanner/tasks/ip_scanner.py

IP 的 Nuclei 掃描任務。

【重構說明】
所有命令準備與執行邏輯已統一提取至 `asset_configs.py` 與 `executor._execute_nuclei_batch()`。
本檔案只保留 Celery task 宣告。
"""

import logging
from typing import List, Optional
from celery import shared_task

from .executor import _execute_nuclei_batch
from apps.core.utils import with_auto_callback

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
@with_auto_callback
def perform_nuclei_scans_for_ip_batch(
    self, 
    ip_ids: List[int], 
    custom_tags: Optional[List[str]] = None,
    callback_step_id: Optional[int] = None
):
    """
    批量 IP 漏洞掃描
    
    特性：
    - 支持最多 3 次重試
    - 失敗後延遲 5 分鐘重試
    - 支持自定義標籤篩選
    - 自動回調機制
    
    Args:
        self: Celery task 自身
        ip_ids: IP ID 列表
        custom_tags: 自定義 Nuclei 標籤
        callback_step_id: 回調步驟 ID
    
    Returns:
        批量掃描結果摘要
    """
    return _execute_nuclei_batch(
        "ip", 
        ip_ids, 
        custom_tags, 
        task_self=self, 
        callback_step_id=callback_step_id
    )
```

**特點**：
- 批量處理多個 IP
- 失敗自動重試（最多 3 次）
- 自動回調機制與步驟跟蹤
- 模塊化設計（邏輯與執行分離）

---

## 第二部分：AI 調用部分

### 2.1 三層 AI Agent 架構概述

C2 Django AI 採用**三層式 AI Agent 架構**，透過 LangChain 框架實現智能自動化：

```
Layer 1 (用戶交互層)
    ↓
PersonalManagerAgent
    ↓ (調用工具)
Layer 2 (戰略規劃層)
    ↓
HackerAssistantAgent
    ↓ (調用工具)
Layer 3 (具體執行層)
    ↓
IPAnalyzerAgent / SubdomainAnalyzerAgent / URLAnalyzerAgent / AutomationAgent
```

---

### 2.2 Layer 1 - 用戶交互層

**文件位置**：`apps/ai_assistant/assistants.py`

```python
from django_ai_assistant import AIAssistant, method_tool
from langchain_mistralai import ChatMistralAI
from langchain_community.tools import (
    ShellTool,
    FileSearchTool,
    ListDirectoryTool,
    WriteFileTool,
    ReadFileTool,
    DuckDuckGoSearchResults,
)


class PersonalManagerAgent(AIAssistant):
    """
    Layer 1: 用戶交互層
    
    職責：
    - 直接與使用者互動的自然語言入口
    - 理解高階需求（例如：「幫我掃描 Google 的子域名」）
    - 將任務下達給 Layer 2 (HackerAssistantAgent)
    """
    id = "personal_manager_agent"
    name = "Personal Manager Agent"
    instructions = (
        "You are a personal manager agent. Your mission is to help the user manage "
        "their tasks and interact with other specialized agents."
    )
    model = "mistral-small-2603"

    def get_llm(self):
        """配置 LLM：Mistral AI"""
        return ChatMistralAI(
            model=self.model,
            temperature=0,  # 確定性回應
            # 套件會自動去讀取環境變數 MISTRAL_API_KEY
        )

    def get_tools(self):
        """註冊可用工具"""
        tools = super().get_tools()
        
        # 將 Layer 2 的 HackerAssistantAgent 作為工具暴露
        tools.append(
            HackerAssistantAgent().as_tool(
                description="Delegate target exploration, penetration testing orchestration, "
                           "or complex AI tasks to the Hacker Assistant Agent."
            )
        )
        return tools

    @method_tool
    def get_current_time_and_date(self) -> str:
        """Get the current time and date"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

**設計要點**：
- 使用 `@method_tool` 裝飾器暴露方法為工具
- 通過 `as_tool()` 將下一層 Agent 作為工具嵌套
- LLM 配置為確定性（temperature=0）

---

### 2.3 Layer 2 - 戰略規劃層

**文件位置**：`apps/ai_assistant/assistants.py`

```python
class HackerAssistantAgent(AIAssistant):
    """
    Layer 2: 戰略規劃層 (Orchestrator)
    
    職責：
    - 負責戰略規劃與任務分發
    - 不負責具體的「打點」工作
    - 讀取資料庫中的 Overview（目標專案概覽）
    - 決定策略後調派 Layer 3
    - 管理掃描進度與風險評分
    """
    id = "hacker_assistant_agent"
    name = "Hacker Assistant"
    instructions = (
        "You are the Orchestrator Hacker Assistant (Layer 2), responsible for managing "
        "penetration testing workflows and coordinating specialized agents.\n\n"
        "Guidelines:\n"
        "1. Delegate low-level scanning and execution tasks to the AutomationAgent (Layer 3) "
        "   or specific analyzer agents.\n"
        "2. When calling the `automation_agent` tool, you must provide the `target_name` "
        "   and a clear `instruction` (e.g., 'Perform Phase B on vuln.com'). "
        "   This ensures the agent has the correct context injected automatically.\n"
        "3. Synthesize findings from sub-agents and report progress concisely to the user.\n"
        "4. Create seeds only for targets explicitly provided by the user; avoid using placeholders.\n"
        "5. If a target already has discovered assets (domains, IPs, URLs), prioritize "
        "   attacking/analyzing them over indefinite enumeration.\n"
        "6. Always verify the Target ID using `list_active_targets` before performing "
        "   target-specific actions.\n"
        "7. Be concise in your communication. Acknowledge commands briefly and let the user "
        "   monitor detailed progress via the UI."
    )
    model = "mistral-small-2603"

    def get_llm(self):
        return ChatMistralAI(
            model=self.model,
            temperature=0,
        )

    def get_tools(self):
        """
        註冊 Layer 2 可用的工具：
        1. 數據庫查詢工具
        2. Layer 3 的各個 Agent
        3. 自定義的輔助工具
        """
        from langchain_community.utilities import SQLDatabase
        from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
        from django.conf import settings
        from apps.auto.assistants.planning_agent import AutomationAgent
        from apps.analyze_ai.assistants import (
            InitialAnalyzerAgent,
            IPAnalyzerAgent,
            SubdomainAnalyzerAgent,
            URLAnalyzerAgent,
        )

        # 配置數據庫連接
        db_settings = settings.DATABASES["default"]
        db_uri = (
            f"postgresql+psycopg2://{db_settings.get('USER', 'postgres')}:"
            f"{db_settings.get('PASSWORD', '')}@{db_settings.get('HOST', 'localhost')}:"
            f"{db_settings.get('PORT', '5432')}/{db_settings.get('NAME', 'postgres')}"
        )
        db = SQLDatabase.from_uri(db_uri)

        # 組裝工具清單
        my_custom_tools = [
            DuckDuckGoSearchResults(),
            QuerySQLDataBaseTool(db=db),
            AutomationAgent().as_tool(
                description="Delegates logic execution to the Automation Agent (Layer 3). "
                           "Use this Agent to perform the 4-phase continuous execution loop "
                           "(Overview, Step, Result, Validate)."
            ),
            InitialAnalyzerAgent().as_tool(
                description="Delegates initial analysis of assets to the Initial Analyzer Agent."
            ),
            IPAnalyzerAgent().as_tool(
                description="Delegates specific IP analysis."
            ),
            SubdomainAnalyzerAgent().as_tool(
                description="Delegates specific Subdomain analysis."
            ),
            URLAnalyzerAgent().as_tool(
                description="Delegates specific URL/Link analysis."
            )
        ]
        
        tools = super().get_tools()
        for tool in my_custom_tools:
            tools.append(tool)
        return tools

    @method_tool
    def list_active_targets(self) -> str:
        """
        Fetch a list of all targets currently in the database to get their IDs 
        and basic information before performing actions on them. 
        Always use this to find the correct Target ID.
        """
        try:
            from apps.core.models import Target
            targets = Target.objects.all().values("id", "name", "created_at")
            if not targets:
                return "No targets found in the database. Instruct the user to create a target or provide seed data."
            
            result = "Currently known targets in the database:\n"
            for t in targets:
                result += f"- Target ID: {t['id']}, Name: {t['name']}, Created: {t['created_at'].strftime('%Y-%m-%d %H:%M:%S') if t['created_at'] else 'Unknown'}\n"
            return result
        except Exception as e:
            return f"Error listing targets: {str(e)}"

    @method_tool
    def check_asset_liveness(self, target_id: int) -> str:
        """
        快速探測指定 Target 底下所有資產 (Subdomains 和 IPs) 的存活狀態。
        使用 HTTP Request 檢測子域名、使用 ping 命令檢測 IP。
        在開始滲透測試之前，可使用此工具快速了解哪些資產是「活的」。

        Args:
            target_id: 要探測的 Target ID。
        """
        import subprocess
        import requests
        from apps.core.models import Subdomain, IP

        results = []

        # --- 探測子域名 (HTTP) ---
        subdomains = list(Subdomain.objects.filter(target_id=target_id).values("id", "name")[:20])
        results.append("=== Subdomain Liveness Check (HTTP) ===")
        for sub in subdomains:
            hostname = sub["name"]
            status = "❌ DEAD"
            for scheme in ("https", "http"):
                try:
                    resp = requests.get(
                        f"{scheme}://{hostname}",
                        timeout=5,
                        allow_redirects=True,
                        verify=False,
                    )
                    status = f"✅ ALIVE ({scheme.upper()}) — HTTP {resp.status_code}"
                    break
                except Exception:
                    continue
            results.append(f"  [{sub['id']}] {hostname}: {status}")

        # --- 探測 IP (ping) ---
        ips = list(IP.objects.filter(target_id=target_id).values("id", "address")[:20])
        results.append("\n=== IP Liveness Check (PING) ===")
        for ip in ips:
            addr = ip["address"]
            try:
                proc = subprocess.run(
                    ["ping", "-c", "1", "-W", "2", addr],
                    capture_output=True, text=True, timeout=5
                )
                status = "✅ ALIVE" if proc.returncode == 0 else "❌ DEAD"
                results.append(f"  [{ip['id']}] {addr}: {status}")
            except Exception as e:
                results.append(f"  [{ip['id']}] {addr}: ⚠️  ERROR ({str(e)[:30]})")

        return "\n".join(results)

    @method_tool
    def get_server_temperature(self) -> str:
        """Retrieve the current hardware/CPU temperature of the server."""
        import subprocess

        try:
            # First try using sensors command directly
            result = subprocess.run(
                "sensors", shell=True, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and "temp" in result.stdout.lower():
                return result.stdout

            # Alternative fallback: reading thermal zone directly
            result = subprocess.run(
                "cat /sys/class/thermal/thermal_zone*/temp",
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                temps = [f"{int(t)/1000}°C" for t in result.stdout.strip().split("\n")]
                return "Thermal Zones: " + ", ".join(temps)

            return "Command executed successfully but no temperature data found. Check if lm-sensors is installed."
        except Exception as e:
            return f"Unable to fetch temperature: {str(e)}"
```

**Layer 2 的工具構成**：
1. **DuckDuckGoSearchResults**：線上搜索工具
2. **QuerySQLDataBaseTool**：數據庫查詢
3. **AutomationAgent()**：Layer 3 執行層
4. **InitialAnalyzerAgent()**：初始分析
5. **IPAnalyzerAgent()**：IP 分析
6. **SubdomainAnalyzerAgent()**：子域名分析
7. **URLAnalyzerAgent()**：URL 分析
8. **list_active_targets()**：目標列表
9. **check_asset_liveness()**：資產存活檢測
10. **get_server_temperature()**：服務器溫度監控

---

### 2.4 Layer 3 - 具體執行層

**文件位置**：`apps/analyze_ai/assistants.py`

```python
import logging
import os
from django.conf import settings
from django_ai_assistant import AIAssistant
from langchain_mistralai import ChatMistralAI

logger = logging.getLogger(__name__)

# 提示詞模板路徑
PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "ips_prompts.txt"
)
SUBDOMAIN_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "subdomains_prompts.txt"
)
URL_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "urls_prompts.txt"
)
INITIAL_PROMPT_TEMPLATE_PATH = (
    settings.BASE_DIR / "apps" / "analyze_ai" / "prompts" / "initial_prompts.txt"
)


def _load_prompt(path) -> str:
    """從文件加載提示詞模板"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            # 移除佔位符，實際數據將通過 Thread message 發送
            return content.replace("{$data}", "").strip()
    except FileNotFoundError:
        logger.error(f"Cannot find prompt template: {path}")
        return "You are a cybersecurity assistant. Analyze the provided asset data."


class AnalyzerMixin:
    """所有分析 Agent 的基礎配置"""
    model = "mistral-small-2603"
    has_rag = False

    def get_llm(self):
        # 明確要求 JSON 結構化輸出
        return ChatMistralAI(
            model=self.model,
            temperature=0,
            model_kwargs={"response_format": {"type": "json_object"}}
        )


class IPAnalyzerAgent(AnalyzerMixin, AIAssistant):
    """
    Layer 3: IP 資產分析 Agent
    
    職責：
    - 分析 IP 資產的掃描結果
    - 提取風險指標
    - 生成 JSON 格式的分析報告
    """
    id = "ip_analyzer_agent"
    name = "IP Asset Analyzer"

    def get_instructions(self):
        return _load_prompt(PROMPT_TEMPLATE_PATH)


class SubdomainAnalyzerAgent(AnalyzerMixin, AIAssistant):
    """
    Layer 3: 子域名資產分析 Agent
    
    職責：
    - 分析子域名資產的掃描結果
    - 識別潛在的安全風險
    - 生成 JSON 格式的分析報告
    """
    id = "subdomain_analyzer_agent"
    name = "Subdomain Asset Analyzer"

    def get_instructions(self):
        return _load_prompt(SUBDOMAIN_PROMPT_TEMPLATE_PATH)


class URLAnalyzerAgent(AnalyzerMixin, AIAssistant):
    """
    Layer 3: URL 資產分析 Agent
    
    職責：
    - 分析 URL 資產的掃描結果
    - 檢測 Web 漏洞和弱點
    - 生成 JSON 格式的分析報告
    """
    id = "url_analyzer_agent"
    name = "URL Asset Analyzer"

    def get_instructions(self):
        return _load_prompt(URL_PROMPT_TEMPLATE_PATH)


class InitialAnalyzerAgent(AnalyzerMixin, AIAssistant):
    """
    Layer 3: 初始分析 Agent
    
    職責：
    - 對新發現的資產進行初步分析
    - 評估風險等級 (0-100)
    - 決定是否自動升級為目標
    """
    id = "initial_analyzer_agent"
    name = "Initial Asset Analyzer"

    def get_instructions(self):
        return _load_prompt(INITIAL_PROMPT_TEMPLATE_PATH)


def get_agent_for_asset_type(asset_type: str) -> AIAssistant:
    """
    根據資產類型返回對應的 Agent 實例
    
    Args:
        asset_type: 資產類型 (ip/subdomain/url/initial)
    
    Returns:
        對應的 AIAssistant 實例
    """
    if asset_type == "ip":
        return IPAnalyzerAgent()
    elif asset_type == "subdomain":
        return SubdomainAnalyzerAgent()
    elif asset_type == "url":
        return URLAnalyzerAgent()
    elif asset_type == "initial":
        return InitialAnalyzerAgent()
    raise ValueError(f"No agent defined for {asset_type}")
```

**Layer 3 的特點**：
- 專職化設計（每個資產類型一個 Agent）
- 使用外部提示詞文件（可維護性強）
- 強制 JSON 結構化輸出
- 確定性 LLM 配置（temperature=0）

---

### 2.5 AI Agent 與數據庫的互動

```python
# 隱式溝通機制：共享黑板（數據庫）

# Layer 2 寫入戰略狀態
from apps.core.models import Overview

def create_or_update_target_overview(target_id, strategy, risk_score):
    """Layer 2 更新目標概覽"""
    overview, created = Overview.objects.update_or_create(
        target_id=target_id,
        defaults={
            'strategy': strategy,
            'risk_score': risk_score,
            'status': 'PLANNING'
        }
    )
    return overview


# Layer 3 記錄執行步驟
from apps.core.models import Step

def create_step(overview_id, action, details):
    """Layer 3 記錄執行步驟"""
    step = Step.objects.create(
        overview_id=overview_id,
        action=action,
        details=details,
        status='PENDING'
    )
    return step


# Layer 3 記錄攻擊向量
from apps.core.models import AttackVector

def create_attack_vector(overview_id, vector_type, config):
    """Layer 3 建立攻擊向量"""
    vector = AttackVector.objects.create(
        overview_id=overview_id,
        vector_type=vector_type,
        config=config,
        status='READY'
    )
    return vector


# Layer 2 監控進度
def get_target_overview(target_id):
    """Layer 2 獲取目標狀態"""
    return Overview.objects.get(target_id=target_id)

def get_exhausted_attack_vectors(target_id):
    """Layer 2 查詢已失敗的攻擊向量（避免重複）"""
    return AttackVector.objects.filter(
        overview__target_id=target_id,
        status='FAILED'
    )
```

---

## 第三部分：工具部分

### 3.1 工具的定義與註冊

**文件位置**：`ai_django/django-ai-assistant/django_ai_assistant/langchain/tools.py`

```python
from langchain_core.tools import (  # noqa
    BaseTool,
    StructuredTool,
    Tool,
    tool,
)
from pydantic.v1 import BaseModel, Field  # noqa


def method_tool(*args, **kwargs):
    """
    裝飾器：將 AIAssistant 的方法標記為工具
    
    LangChain 會自動發現並將其轉換為可調用的工具，
    支持自動參數驗證和類型轉換。
    
    使用範例：
        class MyAssistant(AIAssistant):
            @method_tool
            def my_function(self, param1: str, param2: int) -> str:
                '''Tool description'''
                return f"Result: {param1} {param2}"
    """
    # 如果裝飾器使用 @method_tool（無參數）
    if len(args) == 1 and len(kwargs) == 0:
        decorated_method = args[0]
        decorated_method._is_tool = True
        return decorated_method

    # 如果裝飾器使用 @method_tool(...) 帶參數
    def decorator(decorated_method):
        decorated_method._is_tool = True
        decorated_method._tool_maker_args = args
        decorated_method._tool_maker_kwargs = kwargs
        return decorated_method

    return decorator
```

---

### 3.2 工具的使用示例

**文件位置**：`ai_django/django-ai-assistant/example/tour_guide/ai_assistants.py`

```python
import json

from django.utils import timezone
from pydantic import BaseModel, Field

from django_ai_assistant import AIAssistant, method_tool
from tour_guide.integrations import fetch_points_of_interest


class Attraction(BaseModel):
    name: str = Field(description="The name of the attraction in english")
    description: str = Field(
        description="The description of the attraction, provide information in an entertaining way"
    )


class TourGuide(BaseModel):
    nearby_attractions: list[Attraction] = Field(description="The list of nearby attractions")


class TourGuideAIAssistant(AIAssistant):
    """
    示例 AI Assistant：導遊助手
    
    展示如何：
    1. 使用 @method_tool 定義工具
    2. 使用 Pydantic BaseModel 進行結構化輸出
    3. 調用外部 API（fetch_points_of_interest）
    """
    id = "tour_guide_assistant"  # noqa: A003
    name = "Tour Guide Assistant"
    instructions = (
        "You are a tour guide assistant that offers information about nearby attractions. "
        "You will receive the user coordinates and should use available tools to find nearby attractions. "
        "Only include in your response the items that are relevant to a tourist visiting the area. "
        "Only call the find_nearby_attractions tool once. "
    )
    model = "gpt-4o-mini"
    structured_output = TourGuide  # 強制結構化輸出

    def get_instructions(self):
        # 動態注入當前日期到指令中
        current_date_str = timezone.now().date().isoformat()
        return f"Today is: {current_date_str}. {self.instructions}"

    @method_tool  # 標記為工具
    def find_nearby_attractions(self, latitude: float, longitude: float) -> str:
        """
        Find nearby attractions based on user's current location.
        Returns a JSON with the list of all types of points of interest,
        which may or may not include attractions.
        Calls to this tool are idempotent.
        
        Args:
            latitude: User's latitude coordinate
            longitude: User's longitude coordinate
        
        Returns:
            JSON string with nearby attractions
        """
        return json.dumps(
            fetch_points_of_interest(
                latitude=latitude,
                longitude=longitude,
                tags=["tourism", "leisure", "place", "building"],
                radius=500,
            )
        )
```

**工具調用流程**：
```
1. AI Agent 分析用戶輸入
   ↓
2. AI 決定需要調用哪些工具
   ↓
3. LangChain 自動序列化工具參數
   ↓
4. 執行 Python 方法 (find_nearby_attractions)
   ↓
5. 返回結果給 AI
   ↓
6. AI 基於結果生成回應
```

---

### 3.3 掃描器與工具的連接

掃描器（Celery Task）被包裝成工具供 AI Agent 調用：

```python
class AutomationAgent(AIAssistant):
    """
    Layer 3: 自動化執行 Agent
    
    負責調度掃描器任務，管理掃描生命週期
    """
    
    @method_tool
    def execute_nmap_scan(self, target_id: int, ip_address: str) -> str:
        """
        執行 Nmap 掃描的工具
        
        流程：
        1. 建立 NmapScan 記錄（狀態：PENDING）
        2. 透過 Celery 異步調度 perform_nmap_scan 任務
        3. 返回任務 ID 給 AI，用於後續查詢
        """
        from apps.core.models import NmapScan
        from apps.scanners.nmap_scanner.tasks import perform_nmap_scan
        
        # 1. 建立掃描記錄
        scan = NmapScan.objects.create(
            target_id=target_id,
            ip_address=ip_address,
            status='PENDING'
        )
        
        # 2. 透過 Celery 異步調度任務
        task = perform_nmap_scan.delay(
            scan.id, 
            ip_address, 
            "-sV -p-"
        )
        
        # 3. 返回任務 ID 給 AI
        return f"Nmap scan initiated (Task ID: {task.id})"
    
    @method_tool
    def check_nmap_results(self, scan_id: int) -> str:
        """
        查詢 Nmap 掃描結果的工具
        
        根據掃描狀態返回不同的信息：
        - PENDING: 掃描進行中
        - FAILED: 掃描失敗 + 錯誤訊息
        - COMPLETED: 返回已發現的端口清單
        """
        from apps.core.models import NmapScan, Port
        
        scan = NmapScan.objects.get(id=scan_id)
        
        if scan.status == 'PENDING':
            return f"Nmap scan (ID: {scan_id}) still running..."
        elif scan.status == 'FAILED':
            return f"Nmap scan failed: {scan.error_message}"
        else:
            # 返回已發現的端口
            ports = Port.objects.filter(ip__address=scan.ip_address)
            result = f"Discovered ports for {scan.ip_address}:\n"
            for port in ports:
                result += f"  {port.port_number}/{port.protocol}: {port.service_name} ({port.state})\n"
            return result
    
    @method_tool
    def execute_nuclei_scan(
        self, 
        target_id: int, 
        ip_ids: list, 
        custom_tags: list = None
    ) -> str:
        """
        執行 Nuclei 漏洞掃描的工具
        
        支持批量掃描和自定義標籤篩選
        """
        from apps.core.models import NucleiScan
        from apps.scanners.nuclei_scanner.tasks.ip_scanner import perform_nuclei_scans_for_ip_batch
        
        # 1. 建立掃描記錄
        scan = NucleiScan.objects.create(
            target_id=target_id,
            ip_count=len(ip_ids),
            status='PENDING'
        )
        
        # 2. 異步調度任務
        task = perform_nuclei_scans_for_ip_batch.delay(
            ip_ids, 
            custom_tags
        )
        
        return f"Nuclei scan initiated (Task ID: {task.id})"
```

---

## 數據流圖表

### 整體架構流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用戶交互 (Layer 1)                          │
│                    PersonalManagerAgent                             │
│                    "掃描 Google 的子域名"                           │
└────────────────────────┬────────────────────────────────────────────┘
                         │ 呼叫工具：HackerAssistantAgent.as_tool()
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     戰略規劃 (Layer 2)                              │
│                  HackerAssistantAgent                               │
│                                                                     │
│  讀取：list_active_targets() → Target ID: 1 (Google)               │
│  查詢：QuerySQLDataBaseTool → 已有 Subdomains / IPs？               │
│  決策：執行 SubdomainAnalyzerAgent 進行分析                        │
│  決策：調派 AutomationAgent 執行掃描                               │
│  更新：create_or_update_target_overview() → Overview 表             │
└────────────────────────┬────────────────────────────────────────────┘
                         │ 呼叫工具
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
    ┌──────────┐  ┌─────────────┐  ┌──────────────┐
    │Automation│  │IPAnalyzer   │  │SubdomainAnal │
    │Agent     │  │Agent        │  │yzerAgent    │
    │(Layer 3) │  │(Layer 3)    │  │(Layer 3)    │
    └──────────┘  └─────────────┘  └──────────────┘
    │       │
    │       └─→ @method_tool execute_subfinder_scan()
    │           └─→ Subdomain.objects.filter(status='NEW')
    │           └─→ perform_subfinder_scan.delay()  (Celery)
    │           └─→ Task ID: abc123
    │
    ├─→ @method_tool execute_nmap_scan()
    │   └─→ NmapScan.objects.create()
    │   └─→ perform_nmap_scan.delay()  (Celery)
    │   └─→ Task ID: def456
    │
    └─→ @method_tool check_nmap_results()
        └─→ NmapScan.objects.get(id=xxx)
        └─→ Port.objects.filter(ip__address=...)
        └─→ 返回端口清單


┌─────────────────────────────────────────────────────────────────────┐
│                      掃描器執行層 (Scanners)                        │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Celery Worker: perform_nmap_scan(scan_id=123, ip=...)       │ │
│  │                                                              │ │
│  │  1. NmapScan.objects.get(id=123)                           │ │
│  │  2. with ScannerLifecycle(scan, logger):                   │ │
│  │     3. status = RUNNING, started_at = now()                │ │
│  │     4. subprocess.run("nmap -sV -p- 1.2.3.4")              │ │
│  │     5. lc.set_output(xml_output)                           │ │
│  │     6. parse_and_save_nmap_results()                       │ │
│  │  7. status = COMPLETED, completed_at = now()              │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ Celery Worker: perform_nuclei_scans_for_ip_batch(ip_ids=[]) │ │
│  │                                                              │ │
│  │  1. _execute_nuclei_batch("ip", ip_ids)                    │ │
│  │  2. for each ip_id:                                         │ │
│  │     3. subprocess.run("nuclei -t templates/ ...")          │ │
│  │     4. parse_vulnerabilities()                              │ │
│  │     5. Vulnerability.objects.create()                       │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
                    解析結果存入資料庫


┌─────────────────────────────────────────────────────────────────────┐
│                       數據庫層 (Database)                           │
│                                                                     │
│  目標管理表：                                                      │
│  ├─ Target (目標專案)                                             │
│  ├─ Overview (戰略狀態) ← Layer 2 更新                           │
│  ├─ Step (執行步驟) ← Layer 3 記錄                               │
│  └─ AttackVector (攻擊向量) ← Layer 3 記錄                       │
│                                                                     │
│  資產管理表：                                                      │
│  ├─ IP                                                            │
│  ├─ Port                                                          │
│  ├─ Subdomain                                                     │
│  ├─ URL / URLResult                                              │
│  └─ Vulnerability                                                │
│                                                                     │
│  掃描紀錄表：                                                      │
│  ├─ NmapScan                                                      │
│  ├─ NucleiScan                                                    │
│  ├─ SubfinderScan                                                │
│  └─ ...其他掃描器                                                │
│                                                                     │
│  技術棧表：                                                        │
│  ├─ TechStack                                                     │
│  ├─ Form (表單參數)                                              │
│  ├─ JSFile (JS 文件)                                             │
│  └─ MetaTag (元標籤)                                             │
│                                                                     │
│  分析表：                                                          │
│  ├─ InitialAIAnalysis                                            │
│  └─ DetailedAnalysis                                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### AI Agent 工具調用序列

```
User Input: "掃描 Google 的子域名"
    │
    ↓
PersonalManagerAgent.invoke(input)
    │
    ├─→ AI 分析：需要調用 HackerAssistantAgent
    │
    ↓
HackerAssistantAgent.invoke(input)
    │
    ├─→ @method_tool list_active_targets()
    │   ├─ DB Query: SELECT * FROM Target WHERE name LIKE "google"
    │   └─ Returns: Target ID=1
    │
    ├─→ AI 決策：調用 AutomationAgent
    │
    ↓
AutomationAgent.invoke(input)
    │
    ├─→ @method_tool execute_subfinder_scan(target_id=1)
    │   ├─ Create: SubfinderScan(target=1, status=PENDING)
    │   ├─ Schedule: perform_subfinder_scan.delay(scan_id=xxx)
    │   └─ Returns: Task ID
    │
    ├─→ AI 監控：@method_tool check_subfinder_results(scan_id=xxx)
    │   ├─ Poll: SubfinderScan.objects.get(id=xxx)
    │   ├─ Wait: Until status != PENDING
    │   └─ Returns: Discovered subdomains
    │
    ├─→ AI 分析：@method_tool execute_nmap_scan(target_id=1, ip_list)
    │   ├─ Create: NmapScan(target=1, status=PENDING)
    │   ├─ Schedule: perform_nmap_scan.delay(scan_id=xxx, ip=...)
    │   └─ Returns: Task ID
    │
    └─→ Return result to HackerAssistantAgent
        │
        └─→ Return result to PersonalManagerAgent
            │
            └─→ Return result to User
```

---

## 核心設計模式總結

| 部分 | 設計模式 | 用途 | 位置 |
|------|--------|------|------|
| **掃描器** | Context Manager | 狀態機管理 (PENDING→RUNNING→COMPLETED) | `apps/scanners/base_task.py` |
| **掃描器** | Celery @shared_task | 非同步任務調度 | `apps/scanners/*/tasks/*.py` |
| **掃描器** | ScannerLifecycle | 統一的生命週期管理 | `apps/scanners/base_task.py` |
| **AI Agent** | Tool Decorator (@method_tool) | 暴露方法為 AI 工具 | `django_ai_assistant/langchain/tools.py` |
| **AI Agent** | Agent Nesting (as_tool()) | 將 Agent 作為工具嵌套 | `apps/ai_assistant/assistants.py` |
| **AI Agent** | 動態工具註冊 (get_tools()) | 在運行時動態添加工具 | 各 AIAssistant 實現 |
| **AI×DB** | SQLDatabase + QuerySQLDataBaseTool | AI 查詢數據庫 | Layer 2 get_tools() |
| **AI×掃描器** | 異步回調 (@with_auto_callback) | 掃描完成後的自動回調 | `apps/core/utils.py` |
| **AI×掃描器** | 工具包裝 (execute_*_scan) | 掃描器暴露為工具供 AI 調用 | Layer 3 AIAssistant |
| **數據同步** | 共享黑板 (Overview 表) | Layer 2 & 3 透過 DB 通信 | `apps/core/models/` |

---

## 關鍵文件清單

### 掃描器相關

```
apps/scanners/
├── base_task.py                          ← ScannerLifecycle (核心)
├── nmap_scanner/
│   ├── tasks/__init__.py                 ← perform_nmap_scan() 實現
│   ├── api.py
│   ├── schemas.py
│   └── admin.py
├── nuclei_scanner/
│   ├── tasks/
│   │   ├── ip_scanner.py                 ← perform_nuclei_scans_for_ip_batch()
│   │   ├── executor.py                   ← _execute_nuclei_batch() 邏輯
│   │   └── asset_configs.py              ← 掃描配置
│   ├── api.py
│   └── schemas.py
├── subfinder/
├── get_all_url/
└── api.py                                ← 統一的掃描器 API
```

### AI Agent 相關

```
apps/ai_assistant/
├── assistants.py                         ← PersonalManagerAgent & HackerAssistantAgent
└── apps.py

apps/analyze_ai/
├── assistants.py                         ← Layer 3 分析 Agents
├── prompts/
│   ├── ips_prompts.txt
│   ├── subdomains_prompts.txt
│   ├── urls_prompts.txt
│   └── initial_prompts.txt
└── tasks/

apps/auto/
├── assistants/
│   └── planning_agent.py                 ← AutomationAgent (Layer 3)
└── tasks/
```

### 工具框架相關

```
ai_django/django-ai-assistant/
├── django_ai_assistant/
│   ├── langchain/
│   │   ├── tools.py                      ← @method_tool 裝飾器
│   │   └── __init__.py
│   ├── helpers/
│   │   ├── assistants.py                 ← AIAssistant 基類
│   │   └── use_cases.py                  ← 使用案例
│   ├── api/
│   │   ├── views.py                      ← API 視圖
│   │   └── schemas.py                    ← 請求/響應模式
│   ├── models.py                         ← Thread 和 Message 模型
│   ├── conf.py                           ← 配置
│   └── decorators.py
└── example/
    ├── tour_guide/ai_assistants.py       ← 示例：TourGuideAIAssistant
    ├── weather/ai_assistants.py          ← 示例：WeatherAssistant
    ├── issue_tracker/ai_assistants.py    ← 示例：IssueTrackerAssistant
    └── ...
```

### 數據模型相關

```
apps/core/
├── models/
│   ├── __init__.py
│   ├── base.py                           ← 基礎模型 (TimeStampModel 等)
│   ├── domain.py                         ← Target, Subdomain, Domain
│   ├── network.py                        ← IP, Port
│   ├── url_assets.py                     ← URL, URLResult
│   ├── techstack.py                      ← TechStack, Form, MetaTag, JSFile
│   ├── Vulnerability.py                  ← Vulnerability, CVE
│   ├── analyze/
│   │   └── __init__.py                   ← Overview, Step, AttackVector
│   └── scans_record_models.py            ← NmapScan, NucleiScan 等
├── api.py                                ← REST API 端點
├── schemas.py                            ← Pydantic 模式
└── utils.py                              ← 工具函數 (with_auto_callback 等)
```

---

## 快速參考

### 添加新掃描器的步驟

1. **建立 Celery Task**
   ```python
   # apps/scanners/my_scanner/tasks/__init__.py
   @shared_task(bind=True)
   @with_auto_callback
   def perform_my_scan(self, scan_id: int, ...):
       scan = MyScan.objects.get(id=scan_id)
       with ScannerLifecycle(scan, logger):
           result = run_scan(...)
           parse_and_save(scan, result)
   ```

2. **在 Layer 3 Agent 中暴露工具**
   ```python
   # apps/auto/assistants/planning_agent.py
   @method_tool
   def execute_my_scan(self, target_id: int) -> str:
       from apps.scanners.my_scanner.tasks import perform_my_scan
       scan = MyScan.objects.create(target_id=target_id, status='PENDING')
       task = perform_my_scan.delay(scan.id)
       return f"Scan initiated (Task ID: {task.id})"
   ```

3. **在 Layer 2 Agent 中註冊**
   ```python
   # apps/ai_assistant/assistants.py - HackerAssistantAgent.get_tools()
   # AutomationAgent 已在工具中，無需額外操作
   ```

### 添加新 AI 分析的步驟

1. **建立 AIAssistant 子類**
   ```python
   class MyAnalyzerAgent(AnalyzerMixin, AIAssistant):
       id = "my_analyzer_agent"
       name = "My Analyzer"
       
       def get_instructions(self):
           return _load_prompt(MY_PROMPT_PATH)
   ```

2. **在 Layer 2 中暴露**
   ```python
   # apps/ai_assistant/assistants.py - HackerAssistantAgent.get_tools()
   tools.append(
       MyAnalyzerAgent().as_tool(
           description="My analyzer tool"
       )
   )
   ```

### 添加新工具的步驟

1. **定義方法**
   ```python
   @method_tool
   def my_tool(self, param1: str, param2: int) -> str:
       """Tool documentation"""
       return f"Result: {param1} {param2}"
   ```

2. **自動暴露**
   ```
   由 AIAssistant.get_tools() 自動發現 @method_tool 標記的方法
   ```

---

## 常見問題

### Q: AI Agent 如何知道該調用哪個工具？
A: LangChain 會根據用戶輸入和工具描述，讓 LLM 自動決定調用哪個工具。工具通過 `@method_tool` 裝飾器自動註冊。

### Q: 掃描器任務失敗會如何？
A: `ScannerLifecycle` Context Manager 會自動捕獲異常，設置狀態為 FAILED，存儲錯誤訊息，並讓 Celery 根據配置決定是否重試。

### Q: Layer 2 和 Layer 3 如何通信？
A: 有兩種方式：
- **顯式**：Layer 2 直接調用 Layer 3 的工具（通過 `as_tool()`）
- **隱式**：通過 Overview、Step、AttackVector 表共享數據庫狀態

### Q: 如何追蹤掃描進度？
A: 通過查詢對應的 Scan 記錄（NmapScan、NucleiScan 等）的 status 欄位：
- `PENDING`：等待中
- `RUNNING`：執行中
- `COMPLETED`：完成
- `FAILED`：失敗

---

## 總結

C2 Django AI 項目採用**多層級、多技術棧**的架構設計：

1. **三層 AI Agent 架構**：實現自動化滲透測試的智能決策與執行
2. **Celery 異步掃描器**：支持長時間運行的掃描任務
3. **ScannerLifecycle 狀態機**：確保掃描任務的可靠性和可追蹤性
4. **Tool Decorator 模式**：簡化 AI 工具的定義和暴露
5. **共享黑板設計**：通過數據庫實現層間通信和進度追蹤

這套架構通過明確的職責分離、清晰的數據流和自動化機制，實現了高度可擴展的滲透測試系統。

---

生成日期：2026-05-08
版本：1.0
