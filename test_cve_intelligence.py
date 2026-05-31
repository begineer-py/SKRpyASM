"""
CVE Intelligence Integration - Quick Test

This script tests the basic functionality of the CVE intelligence system.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'c2_core.settings')
django.setup()

import asyncio
from apps.scanners.cve_intelligence.services.cve_enrichment import CVEEnrichmentService
from apps.scanners.cve_intelligence.clients import NVDClient, CISAKEVClient, EPSSClient


async def test_cve_clients():
    """測試 CVE 客戶端"""
    print("=== Testing CVE Clients ===\n")

    # Test NVD Client
    print("1. Testing NVD Client...")
    async with NVDClient() as nvd_client:
        cve_data = await nvd_client.query_cve("CVE-2021-44228")  # Log4Shell
        if cve_data:
            print(f"   ✅ Found: {cve_data['cve_id']}")
            print(f"   Severity: {cve_data['severity']}")
            print(f"   CVSS: {cve_data['cvss_score']}")
        else:
            print("   ❌ CVE not found")

    # Test CISA KEV Client
    print("\n2. Testing CISA KEV Client...")
    async with CISAKEVClient() as kev_client:
        kev_catalog = await kev_client.fetch_kev_catalog()
        print(f"   ✅ Fetched {len(kev_catalog)} KEV entries")

        # Check if Log4Shell is in KEV
        if "CVE-2021-44228" in kev_catalog:
            print("   ✅ Log4Shell (CVE-2021-44228) is in CISA KEV")

    # Test EPSS Client
    print("\n3. Testing EPSS Client...")
    async with EPSSClient() as epss_client:
        epss_data = await epss_client.query_cve("CVE-2021-44228")
        if epss_data:
            print(f"   ✅ EPSS Score: {epss_data['epss_score']:.2%}")
            print(f"   Percentile: {epss_data['percentile']:.2f}")
        else:
            print("   ❌ EPSS data not found")


async def test_enrichment_service():
    """測試 CVE 豐富化服務"""
    print("\n\n=== Testing CVE Enrichment Service ===\n")

    service = CVEEnrichmentService()

    # Test single CVE enrichment
    print("1. Testing single CVE enrichment...")
    cve_intel = await service.enrich_cve("CVE-2021-44228")

    if cve_intel:
        print(f"   ✅ Enriched: {cve_intel.cve_id}")
        print(f"   Severity: {cve_intel.severity}")
        print(f"   CVSS: {cve_intel.cvss_score}")
        print(f"   CISA KEV: {cve_intel.cisa_kev}")
        print(f"   EPSS: {cve_intel.epss_score:.2%}" if cve_intel.epss_score else "   EPSS: N/A")
        print(f"   Risk Score: {cve_intel.risk_score:.1f}/100")
    else:
        print("   ❌ Enrichment failed")

    # Test batch enrichment
    print("\n2. Testing batch CVE enrichment...")
    cve_ids = ["CVE-2021-44228", "CVE-2021-45046", "CVE-2021-45105"]
    cve_intel_map = await service.enrich_cves_batch(cve_ids)

    print(f"   ✅ Enriched {len(cve_intel_map)}/{len(cve_ids)} CVEs")
    for cve_id, cve_intel in cve_intel_map.items():
        if cve_intel:
            print(f"   - {cve_id}: {cve_intel.severity} (CVSS: {cve_intel.cvss_score})")


def test_models():
    """測試資料模型"""
    print("\n\n=== Testing Data Models ===\n")

    from apps.core.models import CVEIntelligence, Vulnerability

    # Check CVEIntelligence records
    cve_count = CVEIntelligence.objects.count()
    print(f"1. CVEIntelligence records: {cve_count}")

    if cve_count > 0:
        # Show top 5 critical CVEs
        critical_cves = CVEIntelligence.objects.filter(
            severity="CRITICAL"
        ).order_by("-cvss_score")[:5]

        print("\n   Top 5 Critical CVEs:")
        for cve in critical_cves:
            kev_flag = "🚨 KEV" if cve.cisa_kev else ""
            print(f"   - {cve.cve_id}: CVSS {cve.cvss_score} {kev_flag}")

    # Check Vulnerability enrichment status
    vuln_stats = {
        "total": Vulnerability.objects.count(),
        "pending": Vulnerability.objects.filter(enrichment_status="pending").count(),
        "enriched": Vulnerability.objects.filter(enrichment_status="enriched").count(),
        "no_cve": Vulnerability.objects.filter(enrichment_status="no_cve").count(),
    }

    print(f"\n2. Vulnerability Enrichment Status:")
    print(f"   Total: {vuln_stats['total']}")
    print(f"   Pending: {vuln_stats['pending']}")
    print(f"   Enriched: {vuln_stats['enriched']}")
    print(f"   No CVE: {vuln_stats['no_cve']}")


if __name__ == "__main__":
    print("CVE Intelligence System - Quick Test\n")
    print("=" * 50)

    try:
        # Test clients and enrichment service
        asyncio.run(test_cve_clients())
        asyncio.run(test_enrichment_service())

        # Test models
        test_models()

        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("\nNext steps:")
        print("1. Apply for NVD API key: https://nvd.nist.gov/developers/request-an-api-key")
        print("2. Add NVD_API_KEY to .env file")
        print("3. Run Nuclei scans to test automatic CVE enrichment")
        print("4. Check CVE intelligence in AutomationAgent tools")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
