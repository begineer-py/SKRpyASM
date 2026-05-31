import logging
from typing import Dict, Any, Optional, List
from django.core.cache import cache
from django.utils import timezone
from apps.core.models import CVEIntelligence
from apps.scanners.cve_intelligence.clients import NVDClient, CISAKEVClient, EPSSClient
from apps.api_keys.utils import get_active_api_keys

logger = logging.getLogger(__name__)


class CVEEnrichmentService:
    """
    CVE 豐富化服務
    協調多個資料來源（NVD、CISA KEV、EPSS）並實作三層快取策略
    """

    def __init__(self):
        self.cache_ttl = 86400  # 24 小時

    async def enrich_cve(self, cve_id: str, force_refresh: bool = False) -> Optional[CVEIntelligence]:
        """
        豐富化單個 CVE，使用三層快取策略

        快取策略：
        1. PostgreSQL (CVEIntelligence 模型) - 永久儲存
        2. Redis - 24h TTL
        3. 外部 API - 最後手段

        Args:
            cve_id: CVE 編號
            force_refresh: 是否強制重新查詢外部 API

        Returns:
            CVEIntelligence 實例，若查詢失敗則返回 None
        """
        cve_id = cve_id.upper()

        # Layer 1: 查詢本地資料庫
        if not force_refresh:
            existing = await self._get_from_db(cve_id)
            if existing:
                logger.debug(f"CVE {cve_id} found in local database")
                return existing

        # Layer 2: 查詢 Redis 快取
        if not force_refresh:
            cached = await self._get_from_cache(cve_id)
            if cached:
                logger.debug(f"CVE {cve_id} found in Redis cache")
                return cached

        # Layer 3: 查詢外部 API
        logger.info(f"Fetching CVE {cve_id} from external APIs")
        cve_data = await self._fetch_from_apis(cve_id)

        if not cve_data:
            logger.warning(f"CVE {cve_id} not found in any data source")
            return None

        # 儲存到資料庫
        cve_intel = await self._save_to_db(cve_data)

        # 儲存到快取
        await self._save_to_cache(cve_id, cve_intel)

        return cve_intel

    async def enrich_cves_batch(
        self,
        cve_ids: List[str],
        force_refresh: bool = False
    ) -> Dict[str, Optional[CVEIntelligence]]:
        """
        批次豐富化多個 CVE（優化版，減少 API 請求）

        Args:
            cve_ids: CVE ID 清單
            force_refresh: 是否強制重新查詢外部 API

        Returns:
            以 CVE ID 為 key 的 CVEIntelligence 字典
        """
        cve_ids = [cve.upper() for cve in cve_ids]
        result = {}

        # Layer 1: 批次查詢本地資料庫
        if not force_refresh:
            from asgiref.sync import sync_to_async
            existing_cves = await sync_to_async(list)(
                CVEIntelligence.objects.filter(cve_id__in=cve_ids)
            )
            for cve in existing_cves:
                result[cve.cve_id] = cve

        # 找出缺失的 CVE
        missing_cve_ids = [cve_id for cve_id in cve_ids if cve_id not in result]

        if not missing_cve_ids:
            logger.info(f"All {len(cve_ids)} CVEs found in local database")
            return result

        logger.info(f"Fetching {len(missing_cve_ids)}/{len(cve_ids)} CVEs from external APIs")

        # Layer 3: 批次查詢外部 API（跳過 Redis 以簡化批次邏輯）
        fetched_data = await self._fetch_from_apis_batch(missing_cve_ids)

        # 批次儲存到資料庫
        for cve_id, cve_data in fetched_data.items():
            if cve_data:
                cve_intel = await self._save_to_db(cve_data)
                result[cve_id] = cve_intel
                await self._save_to_cache(cve_id, cve_intel)

        return result

    async def _get_from_db(self, cve_id: str) -> Optional[CVEIntelligence]:
        """從資料庫查詢 CVE"""
        from asgiref.sync import sync_to_async
        try:
            return await sync_to_async(CVEIntelligence.objects.get)(cve_id=cve_id)
        except CVEIntelligence.DoesNotExist:
            return None

    async def _get_from_cache(self, cve_id: str) -> Optional[CVEIntelligence]:
        """從 Redis 快取查詢 CVE"""
        cache_key = f"cve_intel:{cve_id}"
        cve_intel_id = cache.get(cache_key)
        if cve_intel_id:
            return await self._get_from_db(cve_id)
        return None

    async def _save_to_cache(self, cve_id: str, cve_intel: CVEIntelligence):
        """儲存到 Redis 快取"""
        cache_key = f"cve_intel:{cve_id}"
        cache.set(cache_key, cve_intel.id, self.cache_ttl)

    async def _fetch_from_apis(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """從外部 API 查詢單個 CVE"""
        from asgiref.sync import sync_to_async

        # 異步獲取 API keys
        api_keys = await sync_to_async(get_active_api_keys)()
        nvd_key = api_keys.get("nvd", [None])[0] if "nvd" in api_keys else None

        # 初始化客戶端
        async with NVDClient(api_key=nvd_key) as nvd_client, \
                   CISAKEVClient() as kev_client, \
                   EPSSClient() as epss_client:

            # 並發查詢三個資料來源
            import asyncio
            nvd_task = nvd_client.query_cve(cve_id)
            kev_task = kev_client.query_cve(cve_id)
            epss_task = epss_client.query_cve(cve_id)

            nvd_data, kev_data, epss_data = await asyncio.gather(
                nvd_task, kev_task, epss_task, return_exceptions=True
            )

            # 處理異常
            if isinstance(nvd_data, Exception):
                logger.error(f"NVD query failed for {cve_id}: {nvd_data}")
                nvd_data = None
            if isinstance(kev_data, Exception):
                logger.error(f"KEV query failed for {cve_id}: {kev_data}")
                kev_data = None
            if isinstance(epss_data, Exception):
                logger.error(f"EPSS query failed for {cve_id}: {epss_data}")
                epss_data = None

            # 合併資料
            return self._merge_cve_data(cve_id, nvd_data, kev_data, epss_data)

    async def _fetch_from_apis_batch(self, cve_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """批次從外部 API 查詢多個 CVE"""
        from asgiref.sync import sync_to_async

        # 異步獲取 API keys
        api_keys = await sync_to_async(get_active_api_keys)()
        nvd_key = api_keys.get("nvd", [None])[0] if "nvd" in api_keys else None

        result = {}

        async with NVDClient(api_key=nvd_key) as nvd_client, \
                   CISAKEVClient() as kev_client, \
                   EPSSClient() as epss_client:

            # 批次查詢 EPSS（支援批次 API）
            epss_batch = await epss_client.query_cves_batch(cve_ids)

            # 批次檢查 CISA KEV
            kev_batch = await kev_client.check_cves_in_kev(cve_ids)

            # NVD 需要逐個查詢（API 限制）
            import asyncio
            for cve_id in cve_ids:
                try:
                    nvd_data = await nvd_client.query_cve(cve_id)
                    kev_data = await kev_client.query_cve(cve_id) if kev_batch.get(cve_id) else None
                    epss_data = epss_batch.get(cve_id)

                    merged = self._merge_cve_data(cve_id, nvd_data, kev_data, epss_data)
                    result[cve_id] = merged

                    # 速率限制：有 API key 時 50 req/30s，無 key 時 5 req/30s
                    if not nvd_key:
                        await asyncio.sleep(6)  # 保守估計，避免超過速率限制
                    else:
                        await asyncio.sleep(0.6)  # 有 key 時可以更快

                except Exception as e:
                    logger.error(f"Error fetching {cve_id}: {e}")
                    result[cve_id] = None

        return result

    def _merge_cve_data(
        self,
        cve_id: str,
        nvd_data: Optional[Dict[str, Any]],
        kev_data: Optional[Dict[str, Any]],
        epss_data: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """合併多個資料來源的 CVE 資料"""
        if not nvd_data:
            logger.warning(f"No NVD data for {cve_id}, skipping")
            return None

        merged = {
            "cve_id": cve_id,
            "description": nvd_data.get("description", ""),
            "severity": nvd_data.get("severity", "UNKNOWN"),
            "cvss_score": nvd_data.get("cvss_score"),
            "cvss_vector": nvd_data.get("cvss_vector"),
            "affected_products": nvd_data.get("affected_products", []),
            "references": nvd_data.get("references", []),
            "published_date": nvd_data.get("published_date"),
            "last_modified_date": nvd_data.get("last_modified_date"),
            "exploit_available": False,
            "exploited_in_wild": False,
            "cisa_kev": False,
            "epss_score": None,
            "data_sources": {
                "nvd": nvd_data,
            }
        }

        # 整合 CISA KEV 資料
        if kev_data:
            merged["cisa_kev"] = True
            merged["exploited_in_wild"] = True
            merged["data_sources"]["cisa_kev"] = kev_data

        # 整合 EPSS 資料
        if epss_data:
            merged["epss_score"] = epss_data.get("epss_score")
            merged["data_sources"]["epss"] = epss_data

        # 檢查參考連結中是否有 exploit
        for ref in merged["references"]:
            tags = ref.get("tags", [])
            if any(tag.lower() in ["exploit", "exploit-db", "metasploit"] for tag in tags):
                merged["exploit_available"] = True
                break

        return merged

    async def _save_to_db(self, cve_data: Dict[str, Any]) -> CVEIntelligence:
        """儲存或更新 CVE 到資料庫"""
        from asgiref.sync import sync_to_async
        from django.utils.dateparse import parse_datetime

        # 解析日期
        published_date = None
        if cve_data.get("published_date"):
            published_date = parse_datetime(cve_data["published_date"])

        last_modified_date = None
        if cve_data.get("last_modified_date"):
            last_modified_date = parse_datetime(cve_data["last_modified_date"])

        # 使用 update_or_create 避免重複
        cve_intel, created = await sync_to_async(CVEIntelligence.objects.update_or_create)(
            cve_id=cve_data["cve_id"],
            defaults={
                "description": cve_data.get("description", ""),
                "severity": cve_data.get("severity", "UNKNOWN"),
                "cvss_score": cve_data.get("cvss_score"),
                "cvss_vector": cve_data.get("cvss_vector"),
                "affected_products": cve_data.get("affected_products", []),
                "exploit_available": cve_data.get("exploit_available", False),
                "exploited_in_wild": cve_data.get("exploited_in_wild", False),
                "cisa_kev": cve_data.get("cisa_kev", False),
                "epss_score": cve_data.get("epss_score"),
                "references": cve_data.get("references", []),
                "published_date": published_date,
                "last_modified_date": last_modified_date,
                "data_sources": cve_data.get("data_sources", {}),
            }
        )

        action = "Created" if created else "Updated"
        logger.info(f"{action} CVE {cve_data['cve_id']} in database")
        return cve_intel
