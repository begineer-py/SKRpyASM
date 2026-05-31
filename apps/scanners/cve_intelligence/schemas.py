from ninja import Schema, ModelSchema
from typing import List, Optional
from datetime import datetime
from apps.core.models import CVEIntelligence


# === Request Schemas ===

class CVEQuerySchema(Schema):
    """查詢特定 CVE 的請求 schema"""
    cve_id: str


class CVESearchSchema(Schema):
    """搜尋技術 CVE 的請求 schema"""
    tech_name: str
    version: Optional[str] = None
    severity_min: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
    exploited_only: bool = False


class CVESearchByTagsSchema(Schema):
    """根據 tags 搜尋 CVE 的請求 schema"""
    tags: List[str]  # 例如: ["apache", "rce", "authentication"]
    severity_min: str = "MEDIUM"  # CRITICAL, HIGH, MEDIUM, LOW
    exploited_only: bool = False
    limit: int = 20  # 返回結果數量限制


class EnrichVulnerabilitiesSchema(Schema):
    """批次豐富化 Vulnerability 的請求 schema"""
    vulnerability_ids: List[int]
    callback_step_id: Optional[int] = None


class SyncTechStackSchema(Schema):
    """同步目標 TechStack CVE 的請求 schema"""
    target_id: int
    callback_step_id: Optional[int] = None


class SyncKEVSchema(Schema):
    """手動觸發 CISA KEV 同步的請求 schema"""
    callback_step_id: Optional[int] = None


# === Response Schemas ===

class CVEIntelligenceOut(ModelSchema):
    """CVE 情報輸出 schema"""
    class Meta:
        model = CVEIntelligence
        fields = [
            "id", "cve_id", "description", "severity",
            "cvss_score", "cvss_vector", "affected_products",
            "exploit_available", "exploited_in_wild", "cisa_kev",
            "epss_score", "references", "published_date",
            "created_at", "updated_at"
        ]

    risk_score: float = 0.0

    @staticmethod
    def resolve_risk_score(obj):
        """計算風險分數"""
        return obj.risk_score if hasattr(obj, 'risk_score') else 0.0


class CVESearchResultOut(Schema):
    """CVE 搜尋結果輸出 schema"""
    total: int
    cves: List[CVEIntelligenceOut]


class TechStackCVEMappingOut(Schema):
    """技術棧 CVE 對應輸出 schema"""
    cve_id: str
    severity: str
    cvss_score: Optional[float]
    cisa_kev: bool
    exploit_available: bool
    techstack_name: str
    techstack_version: Optional[str]
    confidence: float


class TechStackCVEReportOut(Schema):
    """技術棧 CVE 報告輸出 schema"""
    target_id: int
    total_cves: int
    critical_count: int
    high_count: int
    kev_count: int
    top_cves: List[TechStackCVEMappingOut]
