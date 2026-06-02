from django.test import TestCase
from django.db.models import Q
from apps.core.models import CVEIntelligence
from apps.scanners.cve_intelligence.clients.nvd_client import NVDClient


def _make_cve(**kwargs):
    """建立 CVEIntelligence 測試記錄的 helper"""
    defaults = {
        "description": "test cve",
        "severity": "HIGH",
        "cvss_score": 7.0,
        "data_sources": {},
    }
    defaults.update(kwargs)
    return CVEIntelligence.objects.create(**defaults)


class CVECPESearchTest(TestCase):
    """測試 CPE 結構化搜索和 description fallback"""

    def setUp(self):
        _make_cve(
            cve_id="CVE-2021-44228",
            description="Remote code execution vulnerability in a logging framework",
            severity="CRITICAL",
            cvss_score=10.0,
            affected_products=[
                {"vendor": "apache", "product": "log4j2", "version": "2.14.1",
                 "cpe": "cpe:2.3:a:apache:log4j2:2.14.1:*:*:*:*:*:*:*"},
                {"vendor": "cisco", "product": "crosswork_data_gateway", "version": "3.0.0",
                 "cpe": "cpe:2.3:a:cisco:crosswork_data_gateway:3.0.0:*:*:*:*:*:*:*"},
                {"vendor": "siemens", "product": "6bk1602-0aa12-0tp0_firmware", "version": "*",
                 "cpe": "cpe:2.3:a:siemens:6bk1602-0aa12-0tp0_firmware:*:*:*:*:*:*:*:*"},
            ],
            cwe_ids=["CWE-917", "CWE-502"],
            data_sources={"nvd": {"severity": "CRITICAL", "cvss_score": 10.0}},
        )
        _make_cve(
            cve_id="CVE-2022-22965",
            description="Spring Framework RCE via data binding",
            severity="CRITICAL",
            cvss_score=9.8,
            affected_products=[
                {"vendor": "vmware", "product": "spring_framework", "version": "5.3.17",
                 "cpe": "cpe:2.3:a:vmware:spring_framework:5.3.17:*:*:*:*:*:*:*"},
            ],
            cwe_ids=["CWE-94"],
            data_sources={"nvd": {"severity": "CRITICAL", "cvss_score": 9.8}},
        )
        _make_cve(
            cve_id="CVE-2022-0778",
            description="OpenSSL infinite loop in BN_mod_sqrt",
            severity="HIGH",
            cvss_score=7.5,
            affected_products=[],
            cwe_ids=[],
            data_sources={"nvd": {"severity": "HIGH", "cvss_score": 7.5}},
        )

    def test_cpe_product_search(self):
        """CPE product 欄位精準匹配"""
        results = CVEIntelligence.objects.filter(
            Q(affected_products__contains=[{"product": "log4j2"}]) |
            Q(affected_products__contains=[{"vendor": "log4j2"}]) |
            Q(description__icontains="log4j2")
        )
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().cve_id, "CVE-2021-44228")

    def test_cpe_vendor_search(self):
        """CPE vendor 欄位精準匹配"""
        results = CVEIntelligence.objects.filter(
            Q(affected_products__contains=[{"product": "apache"}]) |
            Q(affected_products__contains=[{"vendor": "apache"}]) |
            Q(description__icontains="apache")
        )
        cve_ids = list(results.values_list("cve_id", flat=True))
        self.assertIn("CVE-2021-44228", cve_ids)

    def test_cisco_vendor_finds_log4j(self):
        """
        核心 Bug 驗證：搜索 cisco 必須找到 CVE-2021-44228。
        即使 description 完全沒有 'cisco' 文字，CPE vendor 匹配仍能正確返回。
        """
        log4j = CVEIntelligence.objects.get(cve_id="CVE-2021-44228")
        self.assertNotIn("cisco", log4j.description.lower())  # 確認 description 沒有 cisco

        results = CVEIntelligence.objects.filter(
            Q(affected_products__contains=[{"product": "cisco"}]) |
            Q(affected_products__contains=[{"vendor": "cisco"}]) |
            Q(description__icontains="cisco")
        )
        cve_ids = list(results.values_list("cve_id", flat=True))
        self.assertIn("CVE-2021-44228", cve_ids)

    def test_siemens_vendor_finds_log4j(self):
        """搜索 siemens 也必須找到 CVE-2021-44228（同一個 CVE 多個 vendor）"""
        results = CVEIntelligence.objects.filter(
            Q(affected_products__contains=[{"vendor": "siemens"}]) |
            Q(description__icontains="siemens")
        )
        cve_ids = list(results.values_list("cve_id", flat=True))
        self.assertIn("CVE-2021-44228", cve_ids)

    def test_description_fallback(self):
        """無 CPE 資料時，description icontains fallback 仍能找到"""
        results = CVEIntelligence.objects.filter(
            Q(affected_products__contains=[{"product": "openssl"}]) |
            Q(affected_products__contains=[{"vendor": "openssl"}]) |
            Q(description__icontains="openssl")
        )
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().cve_id, "CVE-2022-0778")

    def test_cpe_and_description_both_match_no_duplicate(self):
        """CPE 和 description 都匹配時，OR 邏輯不重複返回"""
        results = CVEIntelligence.objects.filter(
            Q(affected_products__contains=[{"product": "log4j2"}]) |
            Q(affected_products__contains=[{"vendor": "log4j2"}]) |
            Q(description__icontains="log4j2")
        ).distinct()
        self.assertEqual(results.count(), 1)


class CVEJSONBFilterTest(TestCase):
    """測試 JSONB 路徑查詢過濾器（severity, min_cvss, min_epss）"""

    def setUp(self):
        _make_cve(
            cve_id="CVE-2021-CRIT-HIGH",
            description="critical cvss 10",
            severity="CRITICAL",
            cvss_score=10.0,
            data_sources={"nvd": {"severity": "CRITICAL", "cvss_score": 10.0},
                          "epss": {"epss_score": 0.95}},
        )
        _make_cve(
            cve_id="CVE-2021-HIGH-7",
            description="high cvss 7.5",
            severity="HIGH",
            cvss_score=7.5,
            data_sources={"nvd": {"severity": "HIGH", "cvss_score": 7.5},
                          "epss": {"epss_score": 0.3}},
        )
        _make_cve(
            cve_id="CVE-2021-MED-5",
            description="medium cvss 5",
            severity="MEDIUM",
            cvss_score=5.0,
            data_sources={"nvd": {"severity": "MEDIUM", "cvss_score": 5.0},
                          "epss": {"epss_score": 0.05}},
        )

    def test_severity_filter_via_jsonb(self):
        """severity__in on data_sources.nvd.severity 應正確過濾"""
        results = CVEIntelligence.objects.filter(
            data_sources__nvd__severity__in=["CRITICAL", "HIGH"]
        )
        cve_ids = set(results.values_list("cve_id", flat=True))
        self.assertIn("CVE-2021-CRIT-HIGH", cve_ids)
        self.assertIn("CVE-2021-HIGH-7", cve_ids)
        self.assertNotIn("CVE-2021-MED-5", cve_ids)

    def test_min_cvss_filter_via_jsonb(self):
        """data_sources.nvd.cvss_score__gte 應過濾低分 CVE"""
        results = CVEIntelligence.objects.filter(
            data_sources__nvd__cvss_score__gte=9.0
        )
        cve_ids = set(results.values_list("cve_id", flat=True))
        self.assertIn("CVE-2021-CRIT-HIGH", cve_ids)
        self.assertNotIn("CVE-2021-HIGH-7", cve_ids)
        self.assertNotIn("CVE-2021-MED-5", cve_ids)

    def test_min_epss_filter_via_jsonb(self):
        """data_sources.epss.epss_score__gte 應過濾低 EPSS CVE"""
        results = CVEIntelligence.objects.filter(
            data_sources__epss__epss_score__gte=0.5
        )
        cve_ids = set(results.values_list("cve_id", flat=True))
        self.assertIn("CVE-2021-CRIT-HIGH", cve_ids)
        self.assertNotIn("CVE-2021-HIGH-7", cve_ids)
        self.assertNotIn("CVE-2021-MED-5", cve_ids)

    def test_combined_cvss_and_severity(self):
        """組合 CVSS + severity 過濾"""
        results = CVEIntelligence.objects.filter(
            data_sources__nvd__severity__in=["CRITICAL", "HIGH"],
            data_sources__nvd__cvss_score__gte=8.0,
        )
        cve_ids = set(results.values_list("cve_id", flat=True))
        self.assertIn("CVE-2021-CRIT-HIGH", cve_ids)
        self.assertNotIn("CVE-2021-HIGH-7", cve_ids)  # cvss=7.5 < 8.0


class NVDClientCWEExtractionTest(TestCase):
    """測試 NVD client 的 CWE 提取邏輯"""

    def setUp(self):
        self.client = NVDClient()

    def test_cwe_extraction_from_weaknesses(self):
        """從 NVD weaknesses 欄位正確提取 CWE IDs"""
        raw_item = {
            "id": "CVE-2021-44228",
            "descriptions": [{"lang": "en", "value": "test description"}],
            "metrics": {},
            "configurations": [],
            "references": [],
            "weaknesses": [
                {"type": "Primary", "description": [{"lang": "en", "value": "CWE-917"}]},
                {"type": "Secondary", "description": [{"lang": "en", "value": "CWE-502"}]},
            ],
        }
        result = self.client._normalize_cve_data(raw_item)
        self.assertEqual(result["cwe_ids"], ["CWE-917", "CWE-502"])

    def test_cwe_deduplication(self):
        """同一個 CWE 出現多次時，只保留一個"""
        raw_item = {
            "id": "CVE-2021-00001",
            "descriptions": [{"lang": "en", "value": "test"}],
            "metrics": {},
            "configurations": [],
            "references": [],
            "weaknesses": [
                {"type": "Primary", "description": [{"lang": "en", "value": "CWE-79"}]},
                {"type": "Secondary", "description": [{"lang": "en", "value": "CWE-79"}]},
            ],
        }
        result = self.client._normalize_cve_data(raw_item)
        self.assertEqual(result["cwe_ids"], ["CWE-79"])

    def test_empty_weaknesses(self):
        """沒有 weaknesses 資料時，cwe_ids 為空陣列"""
        raw_item = {
            "id": "CVE-2021-00002",
            "descriptions": [{"lang": "en", "value": "test"}],
            "metrics": {},
            "configurations": [],
            "references": [],
        }
        result = self.client._normalize_cve_data(raw_item)
        self.assertEqual(result["cwe_ids"], [])

    def test_non_cwe_values_ignored(self):
        """非 CWE- 開頭的值（如 NVD-CWE-noinfo）不被提取"""
        raw_item = {
            "id": "CVE-2021-00003",
            "descriptions": [{"lang": "en", "value": "test"}],
            "metrics": {},
            "configurations": [],
            "references": [],
            "weaknesses": [
                {"type": "Primary", "description": [
                    {"lang": "en", "value": "NVD-CWE-noinfo"},
                    {"lang": "en", "value": "CWE-200"},
                ]},
            ],
        }
        result = self.client._normalize_cve_data(raw_item)
        self.assertEqual(result["cwe_ids"], ["CWE-200"])


class CWEStorageTest(TestCase):
    """測試 CWE 資料正確儲存至資料庫"""

    def test_cwe_ids_stored_and_retrieved(self):
        """cwe_ids 欄位正確寫入並讀取"""
        _make_cve(cve_id="CVE-2024-99999", cvss_score=8.0, cwe_ids=["CWE-79", "CWE-89"])
        fetched = CVEIntelligence.objects.get(cve_id="CVE-2024-99999")
        self.assertEqual(fetched.cwe_ids, ["CWE-79", "CWE-89"])

    def test_cwe_ids_default_empty_list(self):
        """未指定 cwe_ids 時，預設為空陣列"""
        _make_cve(cve_id="CVE-2024-99998", cvss_score=5.0)
        fetched = CVEIntelligence.objects.get(cve_id="CVE-2024-99998")
        self.assertEqual(fetched.cwe_ids, [])
