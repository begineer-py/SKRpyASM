import logging
from apps.ai_assistant import method_tool
from apps.core.models import CVEIntelligence, Vulnerability, TechStack, TechStackCVEMapping
from apps.scanners.cve_intelligence.services.cve_enrichment import CVEEnrichmentService
from apps.scanners.cve_intelligence.services.version_matcher import VersionMatcher
import asyncio

logger = logging.getLogger(__name__)


class CVEIntelligenceMixin:
    """
    CVE Intelligence Tools Mixin
    提供 CVE 查詢、搜尋和豐富化工具給 AutomationAgent
    """

    @method_tool
    def query_cve_by_id(self, cve_id: str) -> str:
        """
        查詢特定 CVE 的詳細情報（從 NVD、CISA KEV、EPSS 等來源）。

        Args:
            cve_id: CVE 編號 (例如 'CVE-2024-12345')

        Returns:
            CVE 詳細資訊，包含 CVSS 分數、描述、受影響版本、是否有 exploit、CISA KEV 狀態等
        """
        try:
            cve_id = cve_id.upper()
            logger.info(f"Querying CVE: {cve_id}")

            # 使用豐富化服務（三層快取策略）
            service = CVEEnrichmentService()
            cve_intel = asyncio.run(service.enrich_cve(cve_id))

            if not cve_intel:
                return f"❌ CVE {cve_id} 未找到。請確認 CVE ID 是否正確。"

            # 格式化輸出
            output = [
                f"=== CVE 情報：{cve_intel.cve_id} ===",
                f"",
                f"📊 嚴重性：{cve_intel.severity}",
                f"🎯 CVSS 分數：{cve_intel.cvss_score or 'N/A'}",
                f"📈 風險分數：{cve_intel.risk_score:.1f}/100",
                f"",
                f"📝 描述：",
                f"{cve_intel.description[:500]}..." if len(cve_intel.description) > 500 else cve_intel.description,
                f"",
            ]

            # 威脅情報
            threats = []
            if cve_intel.cisa_kev:
                threats.append("🚨 CISA KEV（已被利用）")
            if cve_intel.exploited_in_wild:
                threats.append("⚠️ 野外利用")
            if cve_intel.exploit_available:
                threats.append("💣 Exploit 可用")
            if cve_intel.epss_score:
                threats.append(f"📊 EPSS: {cve_intel.epss_score:.2%}")

            if threats:
                output.append("🔥 威脅情報：")
                for threat in threats:
                    output.append(f"  • {threat}")
                output.append("")

            # 受影響產品
            if cve_intel.affected_products:
                output.append("🎯 受影響產品：")
                for product in cve_intel.affected_products[:5]:
                    vendor = product.get("vendor", "unknown")
                    prod_name = product.get("product", "unknown")
                    version = product.get("version", "*")
                    output.append(f"  • {vendor}/{prod_name} {version}")
                if len(cve_intel.affected_products) > 5:
                    output.append(f"  ... 及其他 {len(cve_intel.affected_products) - 5} 個產品")
                output.append("")

            # CWE 分類
            if cve_intel.cwe_ids:
                output.append("🔐 CWE 分類：")
                for cwe in cve_intel.cwe_ids[:5]:
                    output.append(f"  • {cwe}")
                output.append("")

            # 參考連結
            if cve_intel.references:
                output.append("🔗 參考連結：")
                for ref in cve_intel.references[:3]:
                    url = ref.get("url", "")
                    tags = ref.get("tags", [])
                    tag_str = f" [{', '.join(tags)}]" if tags else ""
                    output.append(f"  • {url}{tag_str}")
                if len(cve_intel.references) > 3:
                    output.append(f"  ... 及其他 {len(cve_intel.references) - 3} 個連結")

            return "\n".join(output)

        except Exception as e:
            logger.error(f"Error querying CVE {cve_id}: {e}")
            return f"❌ 查詢 CVE {cve_id} 時發生錯誤：{str(e)}"

    @method_tool
    def search_cves_for_technology(
        self,
        tech_name: str,
        version: str = None,
        severity_min: str = "MEDIUM",
        exploited_only: bool = False,
        min_cvss: float = None,
        min_epss: float = None,
    ) -> str:
        """
        根據技術名稱和版本搜尋相關的 CVE。

        Args:
            tech_name: 技術名稱 (例如 'Apache Struts', 'Django', 'nginx')
            version: 版本號 (例如 '2.5.30', '4.2.0')，若為 None 則搜尋所有版本
            severity_min: 最低嚴重性 (CRITICAL, HIGH, MEDIUM, LOW)
            exploited_only: 是否只返回已被利用的 CVE (CISA KEV 或 exploit available)
            min_cvss: 最低 CVSS 分數 (0.0-10.0)，例如 7.0
            min_epss: 最低 EPSS 分數 (0.0-1.0)，例如 0.5

        Returns:
            相關 CVE 列表，按 CVSS 分數和 EPSS 分數排序
        """
        try:
            logger.info(f"Searching CVEs for {tech_name} {version or 'all versions'}")

            from django.db.models import Q

            # 查詢本地資料庫
            query = CVEIntelligence.objects.all()

            # CPE 優先 + description fallback（GIN index 加速 affected_products 查詢）
            if tech_name:
                tech_lower = tech_name.lower()
                cve_filter = (
                    Q(affected_products__contains=[{"product": tech_lower}]) |
                    Q(affected_products__contains=[{"vendor": tech_lower}]) |
                    Q(description__icontains=tech_name)
                )
                query = query.filter(cve_filter)

            # 嚴重性過濾
            severity_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            min_level = severity_order.get(severity_min.upper(), 2)
            severity_filter = [k for k, v in severity_order.items() if v >= min_level]
            query = query.filter(severity__in=severity_filter)

            # 已利用過濾
            if exploited_only:
                query = query.filter(Q(cisa_kev=True) | Q(exploit_available=True))

            # CVSS / EPSS 分數過濾
            if min_cvss is not None:
                query = query.filter(cvss_score__gte=min_cvss)
            if min_epss is not None:
                query = query.filter(epss_score__gte=min_epss)

            # 排序（不在版本匹配前截斷，避免漏掉低排名但版本吻合的 CVE）
            query = query.order_by("-cvss_score", "-epss_score")

            cves = list(query)

            if not cves:
                return f"❌ 未找到 {tech_name} 相關的 CVE（嚴重性 >= {severity_min}）"

            # 版本匹配（如果提供了版本）
            if version:
                matcher = VersionMatcher()
                matched_cves = []

                for cve in cves:
                    is_match, match_type, confidence = matcher.match_cpe_to_techstack(
                        tech_name, version, cve.affected_products
                    )
                    if is_match and confidence >= 0.5:
                        matched_cves.append((cve, confidence))

                if not matched_cves:
                    return f"❌ 未找到 {tech_name} {version} 的匹配 CVE"

                # 按信心度排序
                matched_cves.sort(key=lambda x: (x[0].cvss_score or 0, x[1]), reverse=True)
                cves = [cve for cve, _ in matched_cves]

            # 格式化輸出
            output = [
                f"=== CVE 搜尋結果：{tech_name} {version or ''} ===",
                f"找到 {len(cves)} 個相關 CVE（嚴重性 >= {severity_min}）",
                f""
            ]

            for i, cve in enumerate(cves[:10], 1):
                kev_flag = "🚨 KEV" if cve.cisa_kev else ""
                exploit_flag = "💣" if cve.exploit_available else ""
                epss_str = f"EPSS: {cve.epss_score:.2%}" if cve.epss_score else ""

                flags = " ".join(filter(None, [kev_flag, exploit_flag, epss_str]))
                flags_str = f" [{flags}]" if flags else ""

                output.append(
                    f"{i}. {cve.cve_id} - {cve.severity} (CVSS: {cve.cvss_score or 'N/A'}){flags_str}"
                )
                output.append(f"   {cve.description[:100]}...")
                output.append("")

            if len(cves) > 10:
                output.append(f"... 及其他 {len(cves) - 10} 個 CVE")

            output.append(f"\n💡 提示：使用 query_cve_by_id() 查看完整詳情")

            return "\n".join(output)

        except Exception as e:
            logger.error(f"Error searching CVEs for {tech_name}: {e}")
            return f"❌ 搜尋 CVE 時發生錯誤：{str(e)}"

    @method_tool
    def enrich_vulnerability_with_cve(self, vulnerability_id: int) -> str:
        """
        為已發現的 Vulnerability 記錄豐富化 CVE 情報。
        自動從 template_id 或 extracted_results 中提取 CVE ID，並關聯 CVE 情報。

        Args:
            vulnerability_id: Vulnerability 記錄的 ID

        Returns:
            豐富化結果，包含關聯的 CVE 詳情
        """
        try:
            logger.info(f"Enriching vulnerability {vulnerability_id}")

            # 查詢 Vulnerability
            try:
                vuln = Vulnerability.objects.get(id=vulnerability_id)
            except Vulnerability.DoesNotExist:
                return f"❌ Vulnerability ID {vulnerability_id} 不存在"

            # 提取 CVE ID
            from apps.scanners.cve_intelligence.tasks.enrichment_tasks import _extract_cve_id_from_vulnerability
            cve_id = _extract_cve_id_from_vulnerability(vuln)

            if not cve_id:
                vuln.enrichment_status = "no_cve"
                vuln.save(update_fields=["enrichment_status"])
                return f"❌ 無法從 Vulnerability {vulnerability_id} 中提取 CVE ID"

            # 豐富化 CVE
            service = CVEEnrichmentService()
            cve_intel = asyncio.run(service.enrich_cve(cve_id))

            if not cve_intel:
                vuln.enrichment_status = "failed"
                vuln.save(update_fields=["enrichment_status"])
                return f"❌ CVE {cve_id} 查詢失敗"

            # 關聯 CVE 情報
            vuln.cve_intelligence = cve_intel
            vuln.enrichment_status = "enriched"
            vuln.save(update_fields=["cve_intelligence", "enrichment_status"])

            # 格式化輸出
            output = [
                f"✅ Vulnerability {vulnerability_id} 已豐富化",
                f"",
                f"🎯 CVE ID: {cve_intel.cve_id}",
                f"📊 嚴重性: {cve_intel.severity} (CVSS: {cve_intel.cvss_score or 'N/A'})",
                f"📈 風險分數: {cve_intel.risk_score:.1f}/100",
            ]

            if cve_intel.cisa_kev:
                output.append(f"🚨 警告：此 CVE 在 CISA KEV 清單中（已被利用）")
            if cve_intel.exploit_available:
                output.append(f"💣 警告：公開 exploit 可用")
            if cve_intel.epss_score and cve_intel.epss_score > 0.5:
                output.append(f"📊 警告：高 EPSS 分數 ({cve_intel.epss_score:.2%})")

            return "\n".join(output)

        except Exception as e:
            logger.error(f"Error enriching vulnerability {vulnerability_id}: {e}")
            return f"❌ 豐富化 Vulnerability {vulnerability_id} 時發生錯誤：{str(e)}"

    @method_tool
    def get_techstack_cve_report(self, target_id: int = None, overview_id: int = None) -> str:
        """
        生成目標的技術棧 CVE 風險報告。
        分析目標所有已識別的技術棧，並列出相關的高危 CVE。

        Args:
            target_id: Target ID (可選)
            overview_id: Overview ID (自動注入)

        Returns:
            技術棧 CVE 風險報告，按嚴重性排序
        """
        try:
            # 如果沒有提供 target_id，從 overview 取得
            if not target_id and overview_id:
                from apps.core.models import Overview
                try:
                    overview = Overview.objects.get(id=overview_id)
                    target_id = overview.target_id
                except Overview.DoesNotExist:
                    return f"❌ Overview ID {overview_id} 不存在"

            if not target_id:
                return "❌ 請提供 target_id 或確保 overview_id 有效"

            logger.info(f"Generating TechStack CVE report for target {target_id}")

            # 查詢目標的所有 TechStack
            techstacks = TechStack.objects.filter(target_id=target_id)

            if not techstacks.exists():
                return f"❌ Target {target_id} 沒有已識別的技術棧"

            # 查詢所有 TechStackCVEMapping
            mappings = TechStackCVEMapping.objects.filter(
                techstack__target_id=target_id
            ).select_related("techstack", "cve_intelligence").order_by(
                "-cve_intelligence__cvss_score"
            )

            if not mappings.exists():
                return f"ℹ️ Target {target_id} 的技術棧尚未發現相關 CVE\n\n💡 提示：執行技術棧掃描後會自動對應 CVE"

            # 統計（使用 aggregate 一次查詢獲取所有統計）
            from django.db.models import Count, Q

            stats = mappings.aggregate(
                total=Count('id'),
                critical=Count('id', filter=Q(cve_intelligence__severity="CRITICAL")),
                high=Count('id', filter=Q(cve_intelligence__severity="HIGH")),
                kev=Count('id', filter=Q(cve_intelligence__cisa_kev=True))
            )

            total_cves = stats['total']
            critical_cves = stats['critical']
            high_cves = stats['high']
            kev_cves = stats['kev']

            # 格式化輸出
            output = [
                f"=== 技術棧 CVE 風險報告 ===",
                f"Target ID: {target_id}",
                f"",
                f"📊 統計：",
                f"  • 總 CVE 數：{total_cves}",
                f"  • CRITICAL：{critical_cves}",
                f"  • HIGH：{high_cves}",
                f"  • CISA KEV：{kev_cves}",
                f"",
                f"🎯 高風險 CVE（前 10）：",
                f""
            ]

            for i, mapping in enumerate(mappings[:10], 1):
                cve = mapping.cve_intelligence
                tech = mapping.techstack

                kev_flag = "🚨 KEV" if cve.cisa_kev else ""
                exploit_flag = "💣" if cve.exploit_available else ""
                flags = " ".join(filter(None, [kev_flag, exploit_flag]))
                flags_str = f" [{flags}]" if flags else ""

                output.append(
                    f"{i}. {cve.cve_id} - {cve.severity} (CVSS: {cve.cvss_score or 'N/A'}){flags_str}"
                )
                output.append(f"   技術棧：{tech.name} {tech.version or ''}")
                output.append(f"   匹配信心度：{mapping.confidence:.0%}")
                output.append("")

            if total_cves > 10:
                output.append(f"... 及其他 {total_cves - 10} 個 CVE")

            output.append(f"\n💡 提示：使用 query_cve_by_id() 查看 CVE 完整詳情")

            return "\n".join(output)

        except Exception as e:
            logger.error(f"Error generating TechStack CVE report: {e}")
            return f"❌ 生成報告時發生錯誤：{str(e)}"
