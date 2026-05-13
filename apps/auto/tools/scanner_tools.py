import logging
import requests
from django.conf import settings
from django_ai_assistant import method_tool

logger = logging.getLogger(__name__)

# 從設定檔讀取 API Base URL，預留未來多伺服器部署彈性
API_BASE_URL = getattr(settings, "INTERNAL_API_BASE_URL", "http://127.0.0.1:8000/api")

class ScannerToolsMixin:
    """
    Manual wrappers for core scanner endpoints.
    These tools completely abstract away the Step creation, status management, and 
    callback_step_id injection from the AI to prevent schema or lifecycle hallucinations.
    """

    def _dispatch_scanner(self, overview_id: int, tool_name: str, endpoint: str, payload: dict, description: str = "") -> str:
        try:
            from apps.core.models import Step
            from apps.core.models.analyze.Step import StepNote
            from django.utils import timezone
            
            # 1. 僅建立 Step (設定為 WAITING_FOR_ASYNC)
            # 偵察階段 (Reconnaissance) 不應強制綁定 AttackVector，因為此時尚無具體的攻擊向量點
            step = Step.objects.create(
                overview_id=overview_id,
                status="WAITING_FOR_ASYNC"
            )
            
            # 也可以順便將 description 放到 StepNote 幫助人類辨識
            if description:
                StepNote.objects.create(step=step, content=description)

            # 2. 自動注入 callback_step_id
            payload['callback_step_id'] = step.id
            
            # 3. 發送本地 API 請求
            url = f"{API_BASE_URL.rstrip('/')}{endpoint}"
            resp = requests.post(url, json=payload)
            
            if resp.status_code >= 400:
                step.status = "FAILED"
                # 📍 P0 FIX: 設置 completed_at 時間戳
                step.completed_at = timezone.now()
                step.save(update_fields=['status', 'completed_at'])
                StepNote.objects.update_or_create(
                    step=step,
                    defaults={"content": f"{description}\n\n[FAILED] API responded with {resp.status_code}: {resp.text}"}
                )
                return f"CRITICAL_FAILURE: API ({endpoint}) 失敗 (HTTP {resp.status_code}): {resp.text}"
                
            return f"✅ 工具 {tool_name} 已成功發送！(自動管理 Step ID: {step.id} 狀態為 WAITING_FOR_ASYNC)。請等待任務回調或進行其他動作。"
        except Exception as e:
            logger.error(f"Scanner dispatch failed: {e}")
            return f"CRITICAL_FAILURE: 內部執行例外錯誤: {e}"

    @method_tool
    def run_flaresolverr_crawler(self, overview_id: int, target_url: str) -> str:
        """
        [Phase A - Surface Mapping] 使用 Flaresolverr 爬取指定網頁 (GET)。
        會自動找出 URL、Form、Parameters。
        
        Args:
            overview_id: 目標目前的 Overview ID
            target_url: 完整的網址 (例如 'https://example.com/')
        """
        return self._dispatch_scanner(
            overview_id, "flaresolverr", "/api/flaresolverr/start_scanner", 
            {"url": target_url, "method": "GET"}, "Flaresolverr Crawl"
        )
        
    @method_tool
    def run_subfinder_discovery(self, overview_id: int, seed_id: int) -> str:
        """
        [Phase C - Deep Discovery] 呼叫 Subfinder 從 Seed 發掘子域名。
        
        Args:
            overview_id: 目標目前的 Overview ID
            seed_id: 對應的 Seed ID
        """
        return self._dispatch_scanner(
            overview_id, "subfinder", "/api/scanners/subdomain/start_subfinder", 
            {"seed_id": seed_id}, "Subfinder Subdomain Enum"
        )
        
    @method_tool
    def run_gau_url_discovery(self, overview_id: int, subdomain_name: str) -> str:
        """
        [Phase C - Deep Discovery] 呼叫 GAU 被動收集網域的歷史 URL。
        
        Args:
            overview_id: 目標目前的 Overview ID
            subdomain_name: 目標子域名「字串」(e.g., 'vuln-f9wi.onrender.com')，這『不是』ID！
        """
        return self._dispatch_scanner(
            overview_id, "gau", "/api/scanners/crawler/get_all_url", 
            {"name": subdomain_name, "scan_type": "passive"}, "GAU Historical URL Scan"
        )

    @method_tool
    def run_nuclei_tech_scan_subdomains(self, overview_id: int, subdomain_ids: list[int]) -> str:
        """
        [Phase D - Tech Fingerprint] 在子域上執行 Nuclei 技術堆疊掃描 (Tech-stack)。
        """
        return self._dispatch_scanner(
            overview_id, "nuclei-tech", "/api/scanners/vuln/subs_tech", 
            {"ids": subdomain_ids}, "Nuclei Subdomain Tech Scan"
        )

    @method_tool
    def run_nuclei_tech_scan_urls(self, overview_id: int, url_ids: list[int]) -> str:
        """
        [Phase D - Tech Fingerprint] 在 URL 上執行 Nuclei 技術堆疊掃描 (Tech-stack)。
        """
        return self._dispatch_scanner(
            overview_id, "nuclei-tech", "/api/scanners/vuln/urls_tech", 
            {"ids": url_ids}, "Nuclei URL Tech Scan"
        )

    @method_tool
    def run_nuclei_vuln_scan_urls(self, overview_id: int, url_ids: list[int]) -> str:
        """
        [Phase E - Vulnerability Scan] 在 URL 上執行 Nuclei 的「漏洞」模板掃描 (Vuln)。
        注意：請先完成 A~D 階段再調用此工具。
        """
        return self._dispatch_scanner(
            overview_id, "nuclei-vuln", "/api/scanners/vuln/urls", 
            {"ids": url_ids, "tags": []}, "Nuclei URL Vulnerability Scan"
        )

    @method_tool
    def run_nuclei_vuln_scan_subdomains(self, overview_id: int, subdomain_ids: list[int]) -> str:
        """
        [Phase E - Vulnerability Scan] 在子域名上執行 Nuclei 的「漏洞」模板掃描 (Vuln)。
        """
        return self._dispatch_scanner(
            overview_id, "nuclei-vuln", "/api/scanners/vuln/subdomains", 
            {"ids": subdomain_ids, "tags": []}, "Nuclei Subdomain Vulnerability Scan"
        )

    @method_tool
    def run_nmap_port_scan(self, overview_id: int, ip_id: int, seed_id: int) -> str:
        """
        [Phase C - Deep Discovery] 針對發現的 IP 執行 Nmap Full Port Scan 掃描。
        
        Args:
            overview_id: 目標目前的 Overview ID
            ip_id: 要掃描的 IP 資產的 ID (整數)
            seed_id: 該 IP 對應的 Seed ID (整數)
        """
        try:
            from apps.core.models import IP
            ip_obj = IP.objects.filter(id=ip_id).first()
            if not ip_obj:
                return f"CRITICAL_FAILURE: 找不到 IP 資產 (ID: {ip_id})，請先確認資料庫中存在此 IP。"
            ip_str = ip_obj.address
        except Exception as e:
            return f"CRITICAL_FAILURE: 查詢 IP 資產時發生錯誤: {e}"
        
        return self._dispatch_scanner(
            overview_id, "nmap", "/api/scanners/nmap/start_scan", 
            {"ip": ip_str, "seed_ids": [seed_id], "scan_rate": 4, "scan_ports": "top-1000"}, 
            f"Nmap Port Scan for {ip_str}"
        )

    @method_tool
    def analyze_javascript_file(self, overview_id: int, js_id: int, js_type: str) -> str:
        """
        對抓取到的 JavaScript 檔案進行 Nuclei JS 分析。
        
        Args:
            overview_id: 目標目前的 Overview ID
            js_id: 提取到的 JS ID
            js_type: 必須是 "inline" 或 "external"
        """
        if js_type not in ["inline", "external"]:
            return "CRITICAL_FAILURE: js_type 必須為 'inline' 或 'external'"
            
        return self._dispatch_scanner(
            overview_id, "js-analyze", "/api/flaresolverr/json_analyze", 
            {"id": js_id, "type": js_type}, "JavaScript Nuclei Analysis"
        )
