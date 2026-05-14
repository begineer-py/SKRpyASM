import logging
from django_ai_assistant import method_tool
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


class DBToolsMixin:
    """
    提供給 Auto Agent 呼叫的資料庫操縱工具 Mixin。
    所有繼承自此 Mixin 的 Assistant 皆會繼承這些 @method_tool。
    """

    @method_tool
    def get_target_context(self, target_name: str) -> str:
        """
        【必須第一個呼叫】在進行任何操作前，先用此工具查詢目標的所有有效 ID。
        返回：active overview_id、target_id、subdomain IDs、IP IDs、seed IDs、URL result IDs。
        嚴禁在沒有呼叫此工具的情況下自行猜測或假設任何 ID。

        Args:
            target_name: 目標名稱或域名 (e.g., 'vuln-f9wi.onrender.com')。
        """
        try:
            from apps.core.models import Target, Overview, Subdomain, IP, Seed
            from apps.core.models.url_assets import URLResult
            from django.utils import timezone
            
            now_str = timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')

            target = Target.objects.filter(name=target_name).first()
            if not target:
                # 嘗試模糊搜尋
                target = Target.objects.filter(name__icontains=target_name.split(".")[0]).first()
            if not target:
                all_targets = list(Target.objects.values("id", "name"))
                return f"找不到目標 '{target_name}'。現有目標：{all_targets}。請用正確的 target_name 重新呼叫。"

            active_overview = Overview.objects.filter(
                target=target, status__in=["PLANNING", "EXECUTING"]
            ).order_by("-id").first()

            subdomains = list(Subdomain.objects.filter(target=target).values("id", "name")[:15])
            ips = list(IP.objects.filter(target=target).values("id", "address")[:15])
            seeds = list(Seed.objects.filter(target=target).values("id", "type", "value")[:10])
            urls = list(URLResult.objects.filter(target=target).values("id", "url")[:15])

            if not active_overview:
                return (
                    f"=== TARGET CONTEXT ===\n"
                    f"Current System Time: {now_str}\n"
                    f"Target Name: {target.name}\n"
                    f"Target ID: {target.id}\n"
                    f"Active Overview: NONE - No PLANNING/EXECUTING overview found.\n"
                    f"  ⚠ DO NOT call create_step or update_overview_status.\n"
                    f"  👉 You MUST call `create_overview` with target_id={target.id} to initialize a new overview, then call `get_target_context` again.\n"
                    f"Real Seeds: {seeds}\n"
                    f"Real Subdomains: {subdomains}\n"
                    f"Real IPs: {ips}\n"
                    f"Real URLs: {urls}\n"
                    f"=== END OF CONTEXT ==="
                )

            steps_info = ""
            steps = active_overview.steps.all().prefetch_related('discovered_vectors', 'note_detail').order_by('id')
            if steps.exists():
                lines = []
                for s in steps:
                    av = s.discovered_vectors.first()
                    tool = av.name if av else "Unknown Vector"
                    desc = av.description if av else "No description"
                    note = s.note_detail.content if hasattr(s, 'note_detail') and s.note_detail else ""
                    lines.append(f"- Step[{s.id}] Status:{s.status} | Tool/Vector:{tool} | Desc:{desc} | Note:{note}")
                steps_info = "\n  " + "\n  ".join(lines)
            else:
                steps_info = "\n  No Steps created yet."

            return (
                f"=== TARGET CONTEXT (USE ONLY THESE IDs) ===\n"
                f"Current System Time: {now_str}\n"
                f"Target Name: {target.name}\n"
                f"Target ID: {target.id}\n"
                f"Active Overview ID: {active_overview.id}  ← USE THIS as overview_id in ALL tools\n"
                f"Overview Status: {active_overview.status}\n"
                f"Overview Knowledge: {active_overview.knowledge}\n"
                f"Overview Plan: {active_overview.plan}\n"
                f"Overview Active Steps:{steps_info}\n"
                f"Real Seeds (use for Subfinder/crawler): {seeds}\n"
                f"Real Subdomains (use for Nuclei): {subdomains}\n"
                f"Real IPs (use for Nmap/Nuclei): {ips}\n"
                f"Real URLs (use for URL Nuclei/tech): {urls}\n"
                f"=== END OF CONTEXT ===\n"
                f"IMPORTANT: Use overview_id={active_overview.id} in every subsequent tool call."
            )
        except Exception as e:
            logger.error(f"get_target_context failed: {e}")
            return f"查詢目標上下文失敗: {e}"

    @method_tool
    def create_overview(self, target_id: int, thread_id: int = None, parent_thread_id: int = None) -> str:
        """
        為沒有 Active Overview 的 Target 建立一個全新的 Overview。
        建立後，請務必重新呼叫 get_target_context 來獲取新的 overview_id。

        Args:
            target_id: Target 的 ID。
            thread_id: 當前 AI 對話 Thread ID，用於接收非同步掃描器的 Callback。若不能取得，可填 0。
            parent_thread_id: 上層 Calling Agent 的 Thread ID。若上層要求非同步回調，請帶入此 ID。
        """
        try:
            from apps.core.models import Target, Overview
            target = Target.objects.get(id=target_id)
            overview = Overview.objects.create(
                target=target,
                status="PLANNING",
                risk_score=50,
                plan={"steps": []},
                thread_id=thread_id,
                parent_thread_id=parent_thread_id,
            )
            return f"成功為 Target {target.name} (ID: {target.id}) 建立新的 Overview (ID: {overview.id})。請重新呼叫 get_target_context。"
        except Exception as e:
            logger.error(f"Failed to create overview for target {target_id}: {e}")
            return f"建立 Overview 時發生錯誤: {e}"

    @method_tool
    def notify_caller_agent(self, overview_id: int, message: str) -> str:
        """
        如果在長期的非同步自動化任務結束拉！如果 Overview 中存有 parent_thread_id (調用你的上層 Agent)，
        利用此工具將最後的分析結果或是達成目標的消息傳回給上層 Agent 吧。
        """
        try:
            from apps.core.models import Overview
            from django_ai_assistant.models import Thread
            from django_ai_assistant.helpers.use_cases import create_message
            from django.contrib.auth import get_user_model
            
            overview = Overview.objects.get(id=overview_id)
            if not overview.parent_thread_id:
                return "此 Overview 沒有紀錄 parent_thread_id，無法進行回調通知。"
            
            thread_obj = Thread.objects.get(id=overview.parent_thread_id)
            User = get_user_model()
            system_user = thread_obj.created_by or User.objects.filter(is_superuser=True).first()
            
            create_message(
                assistant_id=thread_obj.assistant_id or "hacker_assistant_agent",
                thread=thread_obj,
                user=system_user,
                content=f"[SYSTEM: Layer 3 Async Completion Report For Overview {overview_id}]\n{message}",
            )
            return f"成功回調通知 Parent Thread {overview.parent_thread_id}。"
        except Exception as e:
            logger.error(f"Failed to notify caller agent for overview {overview_id}: {e}")
            return f"通知 Caller Agent 失敗: {e}"

    @method_tool
    def check_scanned_urls(self, target_id: int) -> str:
        """
        檢查某個 Target 底下所有 URL 的抓取紀錄與狀態。
        在執行任何 Flaresolverr 爬蟲、Katana 掃描或其他 URL 掃描與抽取前，請務必先使用此工具，
        以確認該 URL 是否已經被抓取過 (例如 content_fetch_status='SUCCESS_FETCHED')，或是否已用過 Flaresolverr (used_flaresolverr=True)。
        防止重複執行無意義的掃描造成系統負載。
        """
        try:
            from apps.core.models.url_assets import URLResult
            urls = URLResult.objects.filter(target_id=target_id).values(
                "id", "url", "used_flaresolverr", "content_fetch_status", "status_code"
            )
            if not urls:
                return f"No URLs found for Target ID {target_id}."
            
            summary = "URL Scan Status Summary:\n"
            for u in urls:
                used_fs_str = "Yes" if u["used_flaresolverr"] else "No"
                summary += f"- URL ID [{u['id']}]: {u['url']} | Fetch Status: {u['content_fetch_status']} | Flaresolverr Used: {used_fs_str} | Status Code: {u['status_code']}\n"
            return summary
        except Exception as e:
            return f"Error checking scanned URLs: {str(e)}"

    @method_tool
    def check_scanned_subdomains(self, target_id: int) -> str:
        """
        檢查某個 Target 底下所有子域名 (Subdomain) 的掃描狀態與概況。
        在重複使用 Amass, Subfinder 等工具挖掘子域名，或是使用 dnsx/Nuclei 前，
        請務必先使用此工具來「感知」當前資料庫中已經找出的子域名，
        並察看是否已經有 is_tech_analyzed=True 或是否已經成功解析 IP。
        避免永無止盡的執行相同的掃描。
        """
        try:
            from apps.core.models.domain import Subdomain
            subdomains = Subdomain.objects.filter(target_id=target_id).values(
                "id", "name", "is_resolvable", "is_tech_analyzed", "last_scan_type"
            )
            if not subdomains:
                return f"No Subdomains found for Target ID {target_id}."
            
            summary = "Subdomain Scan Status Summary:\n"
            for s in subdomains:
                res_str = "Yes" if s["is_resolvable"] else "No"
                tech_str = "Yes" if s["is_tech_analyzed"] else "No"
                summary += f"- Subdomain ID [{s['id']}]: {s['name']} | Resolvable: {res_str} | Tech Analyzed: {tech_str} | Last Scan: {s['last_scan_type']}\n"
            return summary
        except Exception as e:
            return f"Error checking scanned subdomains: {str(e)}"

    @method_tool
    def check_scanned_ips(self, target_id: int) -> str:
        """
        檢查某個 Target 底下所有 IP 的掃描狀態與概況。
        在對 IP 使用 Nmap, Naabu 等掃描前，請務必先使用此工具，
        確認該 IP 是否已經被掃描過 (例如 last_scan_type 不為空，或是已有掃出的 ports)。
        避免對同一個 IP 重複執行慢速的端口掃描。
        """
        try:
            from apps.core.models.network import IP
            ips = IP.objects.filter(target_id=target_id).prefetch_related('ports')
            if not ips:
                return f"No IPs found for Target ID {target_id}."
            
            summary = "IP Scan Status Summary:\n"
            for ip in ips:
                port_count = ip.ports.count()
                summary += f"- IP ID [{ip.id}]: {ip.address} | Discovered Ports: {port_count} | Last Scan: {ip.last_scan_type}\n"
            return summary
        except Exception as e:
            return f"Error checking scanned IPs: {str(e)}"

    @method_tool
    def update_overview_status(self, overview_id: int, new_status: str = None, new_summary: str = None, new_knowledge: dict = None, new_plan: dict = None, new_risk_score: int = None) -> str:
        """
        更新目標 Overview（專案概覽）的多個欄位。可同時更新以下任意組合：
        - status: 狀態轉換 ('PLANNING' → 'EXECUTING' → 'COMPLETED' → 'STALLED')。
        - summary: 當前目標的文字筆記/總結 (自由文字)。
        - knowledge: 威脅情報與知識 (JSON dict)。
        - plan: 攻擊藍圖 (JSON dict)。
        - risk_score: 風險評分 (0-100)。
        
        Args:
            overview_id: The ID of the Overview.
            new_status: 新的狀態值 ('PLANNING', 'EXECUTING', 'COMPLETED', 'STALLED')。
            new_summary: 更新的文字筆記或總結。
            new_knowledge: A JSON dictionary representing discovered intelligence.
            new_plan: A JSON dictionary outlining the strategic attack plan.
            new_risk_score: 偵測到的風險評分 (0-100)。
        """
        try:
            from apps.core.models import Overview
            if not Overview.objects.filter(id=overview_id).exists():
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist. DO NOT RETRY. Use only IDs given in your starting context."
            overview = Overview.objects.get(id=overview_id)
            update_fields = []

            valid_statuses = ['PLANNING', 'EXECUTING', 'COMPLETED', 'STALLED']
            if new_status is not None:
                if new_status not in valid_statuses:
                    return f"CRITICAL_FAILURE: Invalid status '{new_status}'. Must be one of {valid_statuses}."
                overview.status = new_status
                update_fields.append('status')
            if new_summary is not None:
                overview.summary = new_summary
                update_fields.append('summary')
            if new_knowledge is not None:
                overview.knowledge = new_knowledge
                update_fields.append('knowledge')
            if new_plan is not None:
                overview.plan = new_plan
                update_fields.append('plan')
            if new_risk_score is not None:
                overview.risk_score = new_risk_score
                update_fields.append('risk_score')
            
            if update_fields:
                overview.save(update_fields=update_fields)
            return f"成功更新 Overview#{overview_id} 的 {', '.join(update_fields)}！"
        except Exception as e:
            logger.error(f"Failed to update Overview#{overview_id}: {e}")
            return f"更新 Overview 時發生錯誤: {e}"

    @method_tool
    def query_steps(self, overview_id: int, status_filter: str = None, limit: int = 20) -> str:
        """
        查詢指定 Overview 下的所有 Step 的詳細狀態與內容。
        可以按狀態過濾 (e.g. 只看 COMPLETED 或 FAILED)。
        回傳每個 Step 的 ID、狀態、關聯攻擊向量、筆記內容。

        Args:
            overview_id: 要查詢的 Overview ID。
            status_filter: (選填) 過濾狀態 ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'WAITING_FOR_ASYNC', 'ENDED')。
            limit: (選填) 最大回傳數量，預設 20。
        """
        try:
            from apps.core.models.analyze.Step import Step, StepNote
            from apps.core.models import Overview

            if not Overview.objects.filter(id=overview_id).exists():
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist."

            qs = Step.objects.filter(overview_id=overview_id).prefetch_related(
                'discovered_vectors', 'note_detail', 'content_blobs'
            ).order_by('-created_at')

            if status_filter:
                qs = qs.filter(status=status_filter)

            steps = qs[:limit]
            if not steps:
                return f"Overview#{overview_id} 下沒有找到符合條件的 Step。"

            lines = [f"=== Steps for Overview#{overview_id} (顯示 {len(steps)} 筆) ==="]
            for s in steps:
                # Attack Vector 資訊
                vectors = s.discovered_vectors.all()
                vector_info = ", ".join([f"{v.name}({v.id})" for v in vectors]) if vectors else "None"

                # StepNote 內容
                note_content = ""
                if hasattr(s, 'note_detail') and s.note_detail:
                    note_content = s.note_detail.content[:300] if s.note_detail.content else ""

                # ContentBlob 摘要
                blobs = s.content_blobs.all()
                blob_info = ""
                if blobs:
                    blob_info = " | Blobs: " + ", ".join(
                        [f"blob_id={b.id}({b.content_size}chars)" for b in blobs]
                    )

                lines.append(
                    f"- Step[{s.id}] Status:{s.status} | Created:{s.created_at.strftime('%m-%d %H:%M')} "
                    f"| Vectors:{vector_info}{blob_info}"
                    f"\n  Note: {note_content[:200]}{'...' if len(note_content) > 200 else ''}"
                )

            lines.append("=== END ===")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"query_steps failed for overview {overview_id}: {e}")
            return f"查詢 Steps 失敗: {e}"

    # =========================================================================
    # Asset Creation Tools (AI 發現新資產後寫入資料庫)
    # =========================================================================

    @method_tool
    def create_discovered_url(self, target_id: int, url: str, discovery_source: str = "API", subdomain_id: int = None) -> str:
        """
        當你發現了資料庫中尚未記錄的新 URL（如隱藏的 API 端點、管理面板路徑等），
        使用此工具將它登記進資料庫，以便後續掃描器自動對其進行抓取與漏洞掃描。

        Args:
            target_id: 此 URL 所屬的 Target ID。
            url: 完整的 URL（如 'https://example.com/admin/api/users'）。
            discovery_source: 發現來源 ('SCAN', 'CRAWL_html', 'JS_EXT', 'BRUTE', 'API')。預設 'API'。
            subdomain_id: (選填) 關聯的 Subdomain ID。
        """
        try:
            from apps.core.models.url_assets import URLResult

            existing = URLResult.objects.filter(url=url, target_id=target_id).first()
            if existing:
                return f"URL 已存在: ID={existing.id}, url={existing.url}, fetch_status={existing.content_fetch_status}。不需要重複建立。"

            url_obj = URLResult.objects.create(
                target_id=target_id,
                url=url,
                discovery_source=discovery_source,
                content_fetch_status="PENDING",
            )
            if subdomain_id:
                url_obj.related_subdomains.add(subdomain_id)

            return (
                f"✅ 新 URL 已登記: ID={url_obj.id}, url={url_obj.url}。\n"
                f"系統將在下一個排程週期自動使用 Flaresolverr 抓取此 URL 的內容。"
            )
        except Exception as e:
            logger.error(f"create_discovered_url failed: {e}")
            return f"建立 URL 資產失敗: {e}"

    @method_tool
    def create_discovered_subdomain(self, target_id: int, name: str, seed_id: int = None) -> str:
        """
        當你發現了資料庫中尚未記錄的新子域名（如從 JS 檔案、API 回應中提取），
        使用此工具將它登記進資料庫，以便後續自動進行 DNS 解析、技術分析與漏洞掃描。

        Args:
            target_id: 此子域名所屬的 Target ID。
            name: 子域名名稱（如 'api.example.com'）。
            seed_id: (選填) 發現此子域名的 Seed ID，會自動建立關聯。
        """
        try:
            from apps.core.models.domain import Subdomain, SubdomainSeed

            existing = Subdomain.objects.filter(name=name, target_id=target_id).first()
            if existing:
                return f"子域名已存在: ID={existing.id}, name={existing.name}, resolvable={existing.is_resolvable}。不需要重複建立。"

            sub = Subdomain.objects.create(
                target_id=target_id,
                name=name,
                is_active=True,
                is_resolvable=True,  # 預設可解析，後續掃描器再驗證
                sources_text="AI_DISCOVERY",
            )
            if seed_id:
                SubdomainSeed.objects.get_or_create(subdomain=sub, seed_id=seed_id)

            return (
                f"✅ 新子域名已登記: ID={sub.id}, name={sub.name}。\n"
                f"系統將在下一個排程週期自動進行 DNS 解析與技術棧偵測。"
            )
        except Exception as e:
            logger.error(f"create_discovered_subdomain failed: {e}")
            return f"建立子域名資產失敗: {e}"

    @method_tool
    def create_discovered_ip(self, target_id: int, address: str, seed_id: int = None) -> str:
        """
        當你發現了資料庫中尚未記錄的新 IP 位址（如從 DNS 解析、API 回應中提取），
        使用此工具將它登記進資料庫，以便後續自動進行端口掃描與漏洞分析。

        Args:
            target_id: 此 IP 所屬的 Target ID。
            address: IP 位址字串（如 '192.168.1.1' 或 '2001:db8::1'）。
            seed_id: (選填) 發現此 IP 的 Seed ID。
        """
        try:
            from apps.core.models.network import IP

            existing = IP.objects.filter(address=address, target_id=target_id).first()
            if existing:
                return f"IP 已存在: ID={existing.id}, address={existing.address}。不需要重複建立。"

            version = 6 if ':' in address else 4
            ip_obj = IP.objects.create(
                target_id=target_id,
                address=address,
                version=version,
            )
            if seed_id:
                ip_obj.which_seed.add(seed_id)

            return (
                f"✅ 新 IP 已登記: ID={ip_obj.id}, address={ip_obj.address} (IPv{version})。\n"
                f"系統將在下一個排程週期自動使用 Nmap 掃描此 IP 的端口。"
            )
        except Exception as e:
            logger.error(f"create_discovered_ip failed: {e}")
            return f"建立 IP 資產失敗: {e}"

    # =========================================================================
    # Endpoint Intelligence Tools (API 端點情報查詢與管理)
    # =========================================================================

    @method_tool
    def query_endpoints(self, target_id: int, method_filter: str = None, path_contains: str = None, limit: int = 30) -> str:
        """
        查詢目標的所有 API Endpoint 列表，包含每個端點已知的參數 (URLParameter)。
        可依 HTTP 方法或路徑關鍵字過濾。適合在發動攻擊前了解目標 API 表面積。

        Args:
            target_id: Target 的 ID。
            method_filter: (選填) 依 HTTP 方法過濾，如 'POST', 'GET'。
            path_contains: (選填) 路徑包含的關鍵字，如 '/api/' 或 '/admin'。
            limit: (選填) 最多回傳幾筆，預設 30。
        """
        try:
            from apps.core.models.url_assets import Endpoint

            qs = Endpoint.objects.filter(target_id=target_id).prefetch_related(
                'query_parameters', 'related_subdomains'
            ).order_by('-last_seen')

            if method_filter:
                qs = qs.filter(method=method_filter.upper())
            if path_contains:
                qs = qs.filter(path__icontains=path_contains)

            endpoints = qs[:limit]
            if not endpoints:
                return f"Target#{target_id} 沒有找到符合條件的 Endpoint。"

            lines = [f"=== Endpoints for Target#{target_id} (顯示 {len(endpoints)} 筆) ==="]
            for ep in endpoints:
                params = ep.query_parameters.all()
                param_list = ""
                if params:
                    param_parts = []
                    for p in params:
                        val_hint = f"={p.value[:30]}" if p.value else ""
                        param_parts.append(f"{p.key}{val_hint}[{p.param_location}/{p.source_type or '?'}]")
                    param_list = " | Params: " + ", ".join(param_parts)
                lines.append(f"  EP#{ep.id} [{ep.method}] {ep.path}{param_list}")

            lines.append("=== END ===")
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"query_endpoints failed for target {target_id}: {e}")
            return f"查詢 Endpoints 失敗: {e}"

    @method_tool
    def create_endpoint(self, target_id: int, path: str, method: str = "GET", subdomain_id: int = None) -> str:
        """
        當你從 JS 分析、API 回應或其他偵察手段發現了資料庫中尚未記錄的新 API Endpoint 時，
        使用此工具登記它。去重保護：若已存在則直接回傳現有 ID。

        Args:
            target_id: Target 的 ID。
            path: Endpoint 路徑（如 '/api/v1/users/export' 或 '/admin/secret'）。
            method: HTTP 方法（'GET', 'POST', 'PUT', 'DELETE', 'PATCH'），預設 'GET'。
            subdomain_id: (選填) 關聯的 Subdomain ID。
        """
        try:
            from apps.core.models.url_assets import Endpoint

            ep, created = Endpoint.objects.get_or_create(
                target_id=target_id,
                path=path,
                method=method.upper(),
            )
            if subdomain_id:
                ep.related_subdomains.add(subdomain_id)

            if created:
                return (
                    f"✅ 新 Endpoint 已登記: EP#{ep.id} [{ep.method}] {ep.path}\n"
                    f"可使用 add_endpoint_parameter 為此端點添加已知參數。"
                )
            else:
                params_count = ep.query_parameters.count()
                return f"Endpoint 已存在: EP#{ep.id} [{ep.method}] {ep.path} (現有 {params_count} 個參數)。"
        except Exception as e:
            logger.error(f"create_endpoint failed: {e}")
            return f"建立 Endpoint 失敗: {e}"

    @method_tool
    def add_endpoint_parameter(
        self,
        endpoint_id: int,
        key: str,
        value: str = None,
        param_location: str = "body",
        source_type: str = "javascript",
        data_type: str = None,
    ) -> str:
        """
        為指定的 Endpoint 添加一個新的參數（隱藏參數、注入點、未文檔化欄位等）。
        若此 key 在此 endpoint 的相同位置已存在，會更新 value 而不是重複建立。

        Args:
            endpoint_id: Endpoint 的 ID（來自 query_endpoints 或 create_endpoint 回傳）。
            key: 參數名稱，如 'csrfmiddlewaretoken', 'debug', '_method', 'user_id'。
            value: (選填) 觀察到的範例值，如 'true', '1', 'abc123'。
            param_location: 參數位置 ('query' 或 'body')，預設 'body'。
            source_type: 來源類型 ('form', 'javascript', 'querystring')，預設 'javascript'。
            data_type: (選填) 推斷的資料型別，如 'string', 'int', 'bool', 'json'。
        """
        try:
            from apps.core.models.url_assets import Endpoint, URLParameter

            try:
                ep = Endpoint.objects.get(id=endpoint_id)
            except Endpoint.DoesNotExist:
                return f"CRITICAL_FAILURE: Endpoint ID {endpoint_id} 不存在。請先用 query_endpoints 查詢。"

            param, created = URLParameter.objects.update_or_create(
                which_endpoint=ep,
                param_location=param_location,
                key=key,
                defaults={
                    "value": value,
                    "source_type": source_type,
                    "data_type": data_type,
                }
            )

            action = "✅ 新參數已添加" if created else "🔄 參數已更新"
            val_hint = f" = '{value[:50]}'" if value else ""
            return (
                f"{action}: EP#{ep.id} [{ep.method}] {ep.path}\n"
                f"  {key}{val_hint} [{param_location}/{source_type}]"
            )
        except Exception as e:
            logger.error(f"add_endpoint_parameter failed for endpoint {endpoint_id}: {e}")
            return f"添加 Endpoint 參數失敗: {e}"

    @method_tool
    def write_recon_note(self, overview_id: int, title: str, content: str) -> str:
        """
        快速將偵察發現（例如 curl 的回應、表單結構、注入測試結果）儲存為一個新的 Step + StepNote。
        在完成任何手動操作（如 run_command 執行 curl）後，立刻呼叫此工具保存結果。

        Args:
            overview_id: 當前 Overview 的 ID。
            title: 此發現的簡短標題 (e.g., 'POST /register – SQLi 測試結果')。
            content: 詳細的發現內容（可包含 curl 回應、觀察到的行為、評估等）。
        """
        try:
            from apps.core.models.analyze.Step import Step, StepNote
            from apps.core.models.analyze.overview import Overview
            if not Overview.objects.filter(id=overview_id).exists():
                return f"❌ 錯誤: Overview ID {overview_id} 不存在。請確認你使用 get_target_context 拿到的 Active Overview ID。"
            
            step = Step.objects.create(overview_id=overview_id, status="COMPLETED")
            StepNote.objects.create(step=step, content=f"[{title}]\n\n{content}")
            return f"✅ 已記錄偵察發現至 Step#{step.id} 的 StepNote。"
        except Exception as e:
            logger.error(f"Failed to write recon note for overview {overview_id}: {e}")
            return f"記錄偵察筆記失敗: {e}"

    @method_tool
    def get_url_intelligence(self, url_id: int) -> str:
        """
        【核心情報工具】輸入 URL ID，取得資料庫中已儲存的所有情報：
        - HTTP 狀態、標題、Headers
        - HTML Forms（含 action、method、所有 input 欄位名稱）
        - 發現的 Links 與 Endpoints
        - MetaTags（可推斷技術棧）
        - 分析發現 (AnalysisFinding)：API Key、敏感 pattern 等
        - TechStack：已偵測的技術
        - Vulnerabilities：已記錄的漏洞

        當你想了解一個 URL 的完整情況時，優先呼叫此工具，不要猜測。

        Args:
            url_id: URLResult 的資料庫 ID（從 get_target_context 取得）。
        """
        try:
            from apps.core.models.url_assets import URLResult

            try:
                url_obj = URLResult.objects.prefetch_related(
                    'forms', 'links', 'meta_tags', 'findings',
                    'found_endpoints__query_parameters',
                    'technologies',
                    'vulnerabilities',
                ).get(id=url_id)
            except URLResult.DoesNotExist:
                return f"URL ID {url_id} 不存在於資料庫中。請用 get_target_context 確認正確的 URL IDs。"

            sections = []
            sections.append(f"=== URL INTELLIGENCE (ID: {url_id}) ===")
            sections.append(f"URL: {url_obj.url}")
            sections.append(f"Status: {url_obj.status_code} | Title: {url_obj.title}")
            sections.append(f"Fetch Status: {url_obj.content_fetch_status}")

            # Headers
            if url_obj.headers:
                interesting_headers = {
                    k: v for k, v in (url_obj.headers if isinstance(url_obj.headers, dict) else {}).items()
                    if k.lower() in ('server', 'x-powered-by', 'content-type', 'set-cookie',
                                     'x-frame-options', 'content-security-policy', 'strict-transport-security',
                                     'x-content-type-options', 'access-control-allow-origin')
                }
                if interesting_headers:
                    sections.append(f"\n[Security-Relevant Headers]\n{interesting_headers}")

            # Forms
            forms = list(url_obj.forms.all())
            if forms:
                sections.append(f"\n[Forms Found: {len(forms)}]")
                for f in forms:
                    params = f.parameters  # JSONField
                    field_names = [p.get('name', '?') for p in params] if isinstance(params, list) else list(params.keys()) if isinstance(params, dict) else [str(params)]
                    sections.append(f"  FORM: {f.method} {f.action} | Fields: {field_names}")
            else:
                sections.append("\n[Forms] None found.")

            # Endpoints
            endpoints = list(url_obj.found_endpoints.all().prefetch_related('query_parameters'))
            if endpoints:
                sections.append(f"\n[Endpoints Discovered: {len(endpoints)}]")
                for ep in endpoints[:10]:
                    params = [p.key for p in ep.query_parameters.all()]
                    sections.append(f"  [{ep.method}] {ep.path} | Params: {params}")

            # Links
            links = list(url_obj.links.values_list('href', flat=True)[:15])
            if links:
                sections.append(f"\n[Links ({len(links)} shown)]: {links}")

            # MetaTags
            meta_tags = list(url_obj.meta_tags.values_list('attributes', flat=True)[:8])
            if meta_tags:
                sections.append(f"\n[MetaTags]: {meta_tags}")

            # AnalysisFindings (sensitive patterns, API keys, etc.)
            findings = list(url_obj.findings.values('pattern_name', 'match_content')[:10])
            if findings:
                sections.append(f"\n[Analysis Findings – Sensitive Patterns!]")
                for fi in findings:
                    sections.append(f"  [{fi['pattern_name']}]: {fi['match_content'][:100]}")

            # TechStack
            try:
                techs = list(url_obj.technologies.values_list('name', 'version')[:10])
                if techs:
                    tech_str = [f"{n} {v or ''}".strip() for n, v in techs]
                    sections.append(f"\n[Tech Stack]: {tech_str}")
            except Exception:
                pass

            # Vulnerabilities
            try:
                vulns = list(url_obj.vulnerabilities.values('name', 'severity', 'template_id')[:5])
                if vulns:
                    sections.append(f"\n[Known Vulnerabilities!]: {vulns}")
            except Exception:
                pass

            # Content preview (cleaned HTML, truncated)
            content = url_obj.cleaned_html or url_obj.text or ""
            if content:
                sections.append(f"\n[Content Preview (2000 chars)]\n{content[:2000]}")
            else:
                sections.append("\n[Content] No HTML content stored yet – may need Flaresolverr crawl.")

            sections.append("=== END URL INTELLIGENCE ===")
            return "\n".join(sections)

        except Exception as e:
            logger.error(f"get_url_intelligence failed for url_id={url_id}: {e}")
            return f"Error fetching URL intelligence for ID {url_id}: {e}"


    # =========================================================================
    # Context Compression System (長期記憶)
    # =========================================================================

    def _generate_summary(self, content: str, max_chars: int = 500) -> str:
        """內部工具：呼叫輕量 LLM 對超長內容產生摘要。"""
        try:
            from langchain_mistralai import ChatMistralAI
            from langchain_core.messages import HumanMessage

            llm = ChatMistralAI(model="mistral-small-2503", temperature=0, max_tokens=600)
            prompt = (
                "你是一個專業的安全分析師。以下是一段超長的工具輸出（可能是 HTML、Stack Trace、或掃描報告）。"
                "請用繁體中文產生一份精簡摘要（最多 500 字），重點提取：\n"
                "1. 主要技術棧或框架\n"
                "2. 任何錯誤訊息、異常、或安全漏洞線索\n"
                "3. 表單、端點、敏感路徑等\n"
                "4. 其他值得注意的情報\n\n"
                f"=== 原始內容（截取前 30000 字）===\n{content[:30000]}"
            )
            resp = llm.invoke([HumanMessage(content=prompt)])
            return resp.content[:max_chars]
        except Exception as e:
            logger.error(f"Auto-summary generation failed: {e}")
            return f"[Auto-summary failed: {e}]"

    @method_tool
    def save_long_content(self, content: str, source_type: str = "other", source_url: str = None, step_id: int = None) -> str:
        """
        [Context Compression] 當你獲取到超長的輸出（> 2000 字的 HTML/Stack Trace/報告）時，
        呼叫此工具將它存入長期記憶庫 (ContentBlob)。系統會自動產生 AI 摘要，你只需要記住 blob_id。
        之後若需要深入查看原文，再使用 read_content_blob。

        Args:
            content: 要儲存的超長原始內容
            source_type: 來源類型 ('curl', 'crawler', 'nuclei', 'other')
            source_url: 來源網址 (選填)
            step_id: 關聯的 Step ID (選填)
        """
        from apps.core.models.analyze.ContentBlob import ContentBlob

        # 產生 AI 摘要
        ai_summary = self._generate_summary(content)

        blob = ContentBlob.objects.create(
            raw_content=content,
            content_size=len(content),
            ai_summary=ai_summary,
            source_type=source_type,
            source_url=source_url,
            step_id=step_id
        )
        return (
            f"[Long Output Saved] blob_id={blob.id} | Size: {blob.content_size} chars\n"
            f"Summary: {ai_summary}\n\n"
            f"若需要深入閱讀原文，請呼叫 read_content_blob(blob_id={blob.id})"
        )

    @method_tool
    def read_content_blob(self, blob_id: int, focus_query: str = None) -> str:
        """
        [Context Compression] 讀取長期記憶中的內容。
        - 不帶 focus_query：回傳先前自動生成的 AI 摘要 (ai_summary)。
        - 帶 focus_query：啟動壓縮助手，針對原始全文進行聚焦式提取。
          例如 focus_query='幫我找出裡面的 SQL 語法錯誤' 會讓助手只提取相關段落。

        Args:
            blob_id: ContentBlob 的 ID
            focus_query: (選填) 聚焦問題，讓系統針對原文提取特定資訊
        """
        from apps.core.models.analyze.ContentBlob import ContentBlob

        try:
            blob = ContentBlob.objects.get(id=blob_id)
        except ContentBlob.DoesNotExist:
            return f"ContentBlob ID {blob_id} 不存在。"

        if not focus_query:
            return (
                f"=== ContentBlob #{blob.id} Summary ===\n"
                f"Source: {blob.source_type} | URL: {blob.source_url or 'N/A'} | Size: {blob.content_size} chars\n\n"
                f"{blob.ai_summary or 'No summary available.'}"
            )

        # 帶 focus_query：啟動聚焦式壓縮
        try:
            from langchain_mistralai import ChatMistralAI
            from langchain_core.messages import HumanMessage

            llm = ChatMistralAI(model="mistral-small-2503", temperature=0, max_tokens=800)
            prompt = (
                f"你是一個安全分析師。以下是一段超長的內容（{blob.content_size} 字），"
                f"請針對以下問題進行聚焦式提取（最多 800 字）：\n"
                f"問題：{focus_query}\n\n"
                f"=== 原始內容（截取前 50000 字）===\n{blob.raw_content[:50000]}"
            )
            resp = llm.invoke([HumanMessage(content=prompt)])
            return f"=== Focused Analysis for Blob #{blob.id} ===\nQuery: {focus_query}\n\n{resp.content}"
        except Exception as e:
            logger.error(f"Focused read failed for blob {blob_id}: {e}")
            return f"聚焦分析失敗: {e}. 摘要: {blob.ai_summary}"

    @method_tool
    def search_skills(self, query: str) -> str:
        """
        [Skill System] 透過關鍵字搜尋全域通用的技能清單 (Skill Templates)。
        這能幫助你發現在過去任務中寫好的自動化繞過腳本 (如 CSRF token 獲取工具等)。
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        from django.db.models import Q
        
        skills = SkillTemplate.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        ).order_by('-usage_count')[:10]
        
        if not skills.exists():
            return f"找不到符合 '{query}' 的 Skill。"
            
        res = [f"Found {skills.count()} skills:"]
        for s in skills:
            res.append(f"- Name: {s.name}\n  Tags: {s.tags}\n  Usage Count: {s.usage_count}\n  Description: {s.description}")
        return "\n".join(res)

    @method_tool
    def load_skill(self, name: str) -> str:
        """
        [Skill System] 載入指定名稱的 Skill 詳細內容，包括如何使用的 Instructions 以及底層的 script_content。
        你在執行此技能前，必須先 Load 閱讀其 Instructions 了解具體傳參格式與執行方式。
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        try:
            skill = SkillTemplate.objects.get(name=name)
            return f"Skill Name: {skill.name}\nTags: {skill.tags}\nUsage Count: {skill.usage_count}\n\n=== INSTRUCTIONS ===\n{skill.instructions}\n\n=== SCRIPT CONTENT ({skill.language}) ===\n{skill.script_content or 'No script contents.'}"
        except SkillTemplate.DoesNotExist:
            return f"Skill '{name}' 不存在。"

    @method_tool
    def create_or_update_skill(self, name: str, description: str, instructions: str, script_content: str, language: str = "python", tags: list[str] = None) -> str:
        """
        [Skill System] 讓AI自我進化：當你手刻了繞過腳本或高度可重用的工具（例如自動登入、獲取 CSRF）時，呼叫此系統永久儲存進資料庫。
        這能讓你在未來遇到其他目標時，透過 search_skills 重新找回並重用這段智慧，避免重複造輪子。
        
        Args:
            name: 唯一標識符，如 'django-csrf-bypass'
            description: 供搜尋用的摘要（請寫清楚這能解決什麼痛點）
            instructions: 指南。該如何執行腳本？有什麼必要的 args (例如目標 URL)
            script_content: 程式碼本體字串
            language: 'python' 或 'bash'
            tags: 相關標籤陣列，例如 ["django", "csrf", "bypass"]
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        if tags is None:
            tags = []
            
        skill, created = SkillTemplate.objects.update_or_create(
            name=name,
            defaults={
                "description": description,
                "instructions": instructions,
                "script_content": script_content,
                "language": language,
                "tags": tags
            }
        )
        action = "Created new" if created else "Updated existing"
        return f"[SUCCESS] {action} Skill '{name}'. ID: {skill.id}. 它現在已常駐於資料庫中，供未來調用。"

    @method_tool
    def delete_skill(self, name: str) -> str:
        """
        [Skill System] 刪除資料庫中指定的 Skill。
        如果發現某個 Skill 已經無效、有語法錯誤、或是防禦價值過低（例如只是發送簡單的 GET 請求），必須呼叫此工具將其永久刪除，以保持技能庫的整潔。
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        try:
            skill = SkillTemplate.objects.get(name=name)
            skill.delete()
            return f"[SUCCESS] 已經成功從資料庫刪除 Skill '{name}'。"
        except SkillTemplate.DoesNotExist:
            return f"Skill '{name}' 不存在，無須刪除。"

    @method_tool
    def execute_skill_script(self, name: str, args_string: str = "") -> str:
        """
        [Skill System] 安全地執行資料庫中已存檔的 Skill 腳本。
        系統會將程式碼 dump 到暫存檔，並搭配你提供的 args_string (如 '--url https://target.com') 執行，執行後自動清理暫存。
        
        Args:
            name: 技能名稱 (需已存在於庫中)
            args_string: 命令列參數字串
        """
        from apps.core.models.analyze.SkillTemplate import SkillTemplate
        import subprocess
        import tempfile
        import os
        
        try:
            skill = SkillTemplate.objects.get(name=name)
        except SkillTemplate.DoesNotExist:
            return f"Skill '{name}' does not exist. Use load_skill or search_skills to verify."
            
        # 增加使用次數 (自我演化排序權重)
        skill.usage_count += 1
        skill.save(update_fields=["usage_count"])
        
        ext = ".py" if skill.language.lower() == "python" else ".sh"
        runner = "python3" if skill.language.lower() == "python" else "bash"
        host_sandbox_dir = "/tmp/c2_sandbox_scripts"
        import tempfile
        import os
        import docker
        os.makedirs(host_sandbox_dir, exist_ok=True)
        
        try:
            client = docker.from_env()
            container = client.containers.get('c2_kali_sandbox')
            
            # 將檔案寫入本機與 Docker 共享的 Volume 內
            with tempfile.NamedTemporaryFile(dir=host_sandbox_dir, suffix=ext, delete=False, mode='w', encoding='utf-8') as f:
                f.write(skill.script_content or "")
                tmp_filename = os.path.basename(f.name)
                host_path = f.name
                
            # 使用 docker sdk 將執行環境徹底轉換至 Kali 容器中
            sandbox_path = f"/scripthub/{tmp_filename}"
            # 若 args_string 含有引號，在 shell cmd 時處理比較安全
            exit_code, output_bytes = container.exec_run(
                cmd=f"{runner} {sandbox_path} {args_string}",
                detach=False,
                stream=False
            )
            
            # 執行後清理腳本
            if os.path.exists(host_path):
                os.remove(host_path)
            
            output = f"Executed Skill: {name} (Usage Count now {skill.usage_count})\n"
            output += f"Execution Environment: Kali Docker Sandbox (c2_kali_sandbox)\n"
            output += f"Return Code: {exit_code}\n\n"
            output += f"--- OUTPUT ---\n{output_bytes.decode('utf-8', errors='replace')}\n"
                
            return output
            
        except docker.errors.NotFound:
            if 'host_path' in locals() and os.path.exists(host_path):
                os.remove(host_path)
            return "錯誤：找不到 Sandbox 容器 (c2_kali_sandbox)。請手動啟動 sandbox。"
        except Exception as e:
            if 'host_path' in locals() and os.path.exists(host_path):
                os.remove(host_path)
            return f"[ERROR] Kali Sandbox 執行發生系統異常: {e}"

    @method_tool
    def install_sandbox_dependency(self, package_manager: str, package_name: str) -> str:
        """
        [Skill System] 當你的腳本缺少相依套件 (例如執行時跳出 ImportError，或 bash 跳出 command not found) 時，你可以呼叫此工具自行為 Kali Docker Sandbox 安裝套件。
        
        Args:
            package_manager: 只能是 'apt' 或 'pip'
            package_name: 要安裝的套件名稱 (例如 'paramiko' 或 'mariadb-client')
        """
        import docker
        if package_manager not in ['apt', 'pip']:
            return "package_manager 必須是 'apt' 或 'pip'"
            
        if package_manager == "apt":
            cmd = f"apt-get update && apt-get install -y --no-install-recommends {package_name}"
        else:
            # Kali is PEP-668 managed, we must append --break-system-packages
            cmd = f"pip3 install {package_name} --break-system-packages"
            
        try:
            client = docker.from_env()
            container = client.containers.get('c2_kali_sandbox')
            exit_code, output_bytes = container.exec_run(
                cmd=["/bin/bash", "-c", cmd],
                detach=False,
                stream=False
            )
            res = f"Installed {package_name} via {package_manager}.\nExit Code: {exit_code}\nOutput:\n{output_bytes.decode('utf-8', errors='replace')}"
            return res
        except docker.errors.NotFound:
            return "錯誤：找不到 Sandbox 容器 (c2_kali_sandbox)。"
        except Exception as e:
            return f"[ERROR] 安裝套件時發生錯誤: {e}"

    @method_tool
    def run_command(self, command: str) -> str:
        """
        Run shell commands in a completely isolated Kali Linux Sandbox.
        Use this as a fallback if API scanners fail, or to curl/interact with pages natively during Phase B.
        The executed commands will run securely via Docker.
        """
        import docker
        try:
            client = docker.from_env()
            container = client.containers.get('c2_kali_sandbox')
            
            exit_code, output_bytes = container.exec_run(
                cmd=["/bin/bash", "-c", command],
                detach=False,
                stream=False
            )
            
            res = f"Execution Environment: Kali Docker Sandbox\n"
            res += f"Exit Code: {exit_code}\n"
            res += f"Output:\n{output_bytes.decode('utf-8', errors='replace')}"
            return res
        except docker.errors.NotFound:
            return "錯誤：找不到 Sandbox 容器 (c2_kali_sandbox)。請先透過 start_sandbox.sh 啟動。"
        except Exception as e:
            return f"Sandbox Command Failed: {e}"

    @method_tool
    def create_step(
        self, 
        overview_id: int, 
        command_name: str,
        command_template_str: str, 
        description: str,
        asset_fk_field: str,
        asset_fk_value_id: int,
        parent_step_id: int = None,
        tool_name: str = None,
        note: str = None,
        ai_thoughts: str = None
    ) -> str:
        """
        為自動化滲透測試流程建立一個新的執行步驟（Step）。
        這會同步建立關聯的 StepNote、AttackVector 以及 CommandTemplate。

        Args:
            overview_id: 關聯的 Overview ID。
            command_name: 命令的簡稱。
            command_template_str: 要執行的 CLI 命令（例如 'nmap -sV -p 80 {{ip}}'）。
            description: 這個步驟的說明與目的。
            asset_fk_field: 關聯的資產類型 ('ip', 'subdomain', 或 'url_result')。
            asset_fk_value_id: 關聯的資產主鍵 ID。
            parent_step_id: (Optional) 父步驟 ID。
            tool_name: (Optional) 使用的工具名稱 (nmap, nuclei 等)。
            note: (Optional) AI寫給人類看的進度筆記。
            ai_thoughts: (Optional) AI內部推理過程筆記。
        """
        try:
            from apps.core.models import Step, AttackVector, Overview
            from apps.core.models.analyze.Step import StepNote
            from apps.core.models.analyze.AttackVector import CommandTemplate
            
            # Overview ID 前置驗證：AI 幻覺防火牆
            if not Overview.objects.filter(id=overview_id).exists():
                logger.error(f"Hallucinated overview_id={overview_id}, does not exist in DB.")
                return f"CRITICAL_FAILURE: overview_id={overview_id} does not exist. DO NOT RETRY. Use only the overview_id given in your starting context."
            
            if parent_step_id and not Step.objects.filter(id=parent_step_id).exists():
                logger.warning(f"Invalid parent_step_id {parent_step_id}, setting to None")
                parent_step_id = None

            step = Step.objects.create(
                overview_id=overview_id,
                parent_step_id=parent_step_id,
                status="PENDING"
            )
            
            if asset_fk_field and asset_fk_value_id:
                # 資產 ID 前置驗證：在寫入 M2M 前先確認資產存在
                _asset_model_map = {
                    "ip": ("apps.core.models", "IP"),
                    "subdomain": ("apps.core.models", "Subdomain"),
                    "url_result": ("apps.core.models.url_assets", "URLResult"),
                }
                _model_info = _asset_model_map.get(asset_fk_field)
                if _model_info:
                    import importlib
                    _mod = importlib.import_module(_model_info[0])
                    _AssetModel = getattr(_mod, _model_info[1])
                    if not _AssetModel.objects.filter(id=asset_fk_value_id).exists():
                        logger.warning(f"Hallucinated asset {asset_fk_field}_id={asset_fk_value_id}. Rolling back step and returning CRITICAL_FAILURE.")
                        step.delete()
                        return f"CRITICAL_FAILURE: asset {asset_fk_field}_id={asset_fk_value_id} does not exist in the database. Use ONLY IDs from your starting context. DO NOT RETRY with the same ID."

                m2m_mgr = getattr(step, asset_fk_field, None)
                if m2m_mgr is not None:
                    try:
                        m2m_mgr.add(asset_fk_value_id)
                    except Exception as m2m_err:
                        logger.warning(f"Invalid asset {asset_fk_field}={asset_fk_value_id}, ignored: {m2m_err}")
            
            if note or ai_thoughts:
                StepNote.objects.create(step=step, content=note, ai_thoughts=ai_thoughts)
            
            vector = AttackVector.objects.create(
                overview_id=overview_id,
                discovery_step=step,
                name=f"Attack Vector via {tool_name or 'Tool'}",
                description=description,
                status="IDENTIFIED"
            )
            
            cmd = CommandTemplate.objects.create(
                attack_vector=vector,
                name=command_name,
                description=description,
                tool_name=tool_name,
                command=command_template_str
            )
            
            return f"成功建立新的 Step#{step.id}, AttackVector#{vector.id}, 與 CommandTemplate#{cmd.id}！"
        except Exception as e:
            logger.error(f"Failed to create step: {e}")
            return f"建立 Step 時發生錯誤: {e}"

    @method_tool
    def update_step_status(
        self,
        step_id: int,
        status: str,
        execution_output: str = None,
    ) -> str:
        """
        更新指定 Step 的執行狀態。
        
        **AI 使用規則 (MANDATORY WORKFLOW)**:
        - 在呼叫任何掃描 API 工具「之前」，先呼叫此工具將 Step 設為 RUNNING。
        - 如果工具是非同步的 (會有 callback)，呼叫後設為 WAITING_FOR_ASYNC。
        - 如果工具立即返回成功結果，設為 COMPLETED。
        - 如果工具返回 CRITICAL_FAILURE，設為 FAILED 並附上錯誤輸出。
        
        Valid status values: PENDING, RUNNING, COMPLETED, FAILED, WAITING_FOR_ASYNC, ENDED

        Args:
            step_id: 要更新的 Step ID。
            status: 新狀態 (RUNNING / COMPLETED / FAILED / WAITING_FOR_ASYNC / ENDED)。
            execution_output: (Optional) 執行結果摘要或錯誤訊息。
        """
        try:
            from apps.core.models import Step
            from apps.core.models.analyze.Step import StepNote
            from django.utils import timezone
            
            step = Step.objects.get(id=step_id)
            valid_statuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED", "WAITING_FOR_ASYNC", "ENDED"]
            if status not in valid_statuses:
                return f"無效的 status 值: '{status}'。請使用: {valid_statuses}"
            
            step.status = status
            
            # 📍 P0 FIX: 當 Step 完成或失敗時，設置 completed_at 時間戳
            if status in ["COMPLETED", "FAILED", "ENDED"]:
                step.completed_at = timezone.now()
            
            step.save(update_fields=["status", "completed_at"])
            
            # 附加執行輸出到 StepNote
            if execution_output:
                note, _ = StepNote.objects.get_or_create(step=step)
                note.content = (note.content or "") + f"\n[{status}] {execution_output}"
                note.save(update_fields=["content"])
            
            return f"Step#{step_id} 狀態已更新為 {status}。"
        except Exception as e:
            return f"更新 Step#{step_id} 狀態失敗: {e}"

    @method_tool
    def create_verification(
        self,
        attack_vector_id: int,
        observation_prompt: str,
        confidence_threshold: int = 75,
        auto_create_vulnerability: bool = False
    ) -> str:
        """
        為指定的 AttackVector 建立 AI 驗證規則（Verification）。
        設定成功標準，系統執行後將依此評估該向量是否成功並建立 Vulnerability。
        
        Args:
            attack_vector_id: 目標 AttackVector 的 ID。
            observation_prompt: 驗證標準，描述「這個步驟的成功標準」(如: 'nmap 輸出中出現漏洞 CVE')。
            confidence_threshold: 信心門檻 (預設 75)。
            auto_create_vulnerability: 驗證通過時是否自動回報漏洞 (預設 False)。
        """
        try:
            from apps.core.models.analyze.Step import Verification
            v = Verification.objects.create(
                attack_vector_id=attack_vector_id,
                observation_prompt=observation_prompt,
                confidence_threshold=confidence_threshold,
                auto_create_vulnerability=auto_create_vulnerability,
                verdict="PENDING"
            )
            return f"成功為 AttackVector#{attack_vector_id} 建立 Verification#{v.id}！"
        except Exception as e:
            return f"建立 Verification 發生錯誤: {e}"

    @method_tool
    def get_exhausted_attack_vectors(self, overview_id: int) -> str:
        """
        取得此 Overview 中所有狀態為 EXHAUSTED (失敗) 或 MITIGATED (已緩解) 的攻擊向量。
        AI 在規劃 Step 前應先呼叫此工具，避免重複使用已經失敗的攻擊向量！
        """
        try:
            from apps.core.models import AttackVector
            vectors = AttackVector.objects.filter(
                overview_id=overview_id, 
                status__in=["EXHAUSTED", "MITIGATED"]
            )
            if not vectors.exists():
                return "目前沒有已失敗或無效的攻擊向量。可自由進行測試。"
            
            res = []
            for v in vectors:
                cmds = list(v.command_templates.values_list('command', flat=True))
                res.append(f"Vector ID: {v.id} | Name: {v.name} | Commands tried: {cmds} | Status: {v.status}")
            return "\n".join(res)
        except Exception as e:
            return f"獲取失敗的攻擊向量時發生錯誤: {e}"

    @method_tool
    
