import logging
import re
from typing import Optional, List, Tuple
from packaging import version as pkg_version

logger = logging.getLogger(__name__)


class VersionMatcher:
    """
    版本匹配邏輯
    用於判斷技術棧版本是否受 CVE 影響
    """

    @staticmethod
    def parse_version(version_str: str) -> Optional[pkg_version.Version]:
        """
        解析版本字串

        Args:
            version_str: 版本字串 (例如 "2.5.30", "4.2.0")

        Returns:
            packaging.version.Version 物件，若解析失敗則返回 None
        """
        try:
            # 清理版本字串
            cleaned = re.sub(r'[^\d.]', '', version_str)
            return pkg_version.parse(cleaned)
        except Exception as e:
            logger.warning(f"Failed to parse version '{version_str}': {e}")
            return None

    @staticmethod
    def is_version_affected(
        tech_version: str,
        affected_versions: List[str]
    ) -> Tuple[bool, str, float]:
        """
        判斷技術版本是否受影響

        Args:
            tech_version: 技術棧版本 (例如 "2.5.30")
            affected_versions: 受影響的版本清單 (例如 ["2.5.0-2.5.30", "2.6.0"])

        Returns:
            (是否受影響, 匹配類型, 信心度)
            匹配類型: "exact", "range", "unknown"
            信心度: 0.0-1.0
        """
        if not tech_version or not affected_versions:
            return False, "unknown", 0.0

        parsed_tech_version = VersionMatcher.parse_version(tech_version)
        if not parsed_tech_version:
            return False, "unknown", 0.0

        for affected_ver in affected_versions:
            # 精確匹配
            if tech_version == affected_ver or tech_version == affected_ver.strip():
                return True, "exact", 1.0

            # 範圍匹配 (例如 "2.5.0-2.5.30")
            if "-" in affected_ver:
                parts = affected_ver.split("-")
                if len(parts) == 2:
                    start_ver = VersionMatcher.parse_version(parts[0])
                    end_ver = VersionMatcher.parse_version(parts[1])

                    if start_ver and end_ver:
                        if start_ver <= parsed_tech_version <= end_ver:
                            return True, "range", 0.9

            # 萬用字元匹配 (例如 "2.5.*")
            if "*" in affected_ver:
                pattern = affected_ver.replace(".", r"\.").replace("*", r".*")
                if re.match(f"^{pattern}$", tech_version):
                    return True, "range", 0.8

        return False, "unknown", 0.0

    @staticmethod
    def match_cpe_to_techstack(
        tech_name: str,
        tech_version: str,
        cpe_products: List[dict]
    ) -> Tuple[bool, str, float]:
        """
        將 TechStack 與 CPE 產品清單匹配

        Args:
            tech_name: 技術名稱 (例如 "Apache Struts")
            tech_version: 技術版本 (例如 "2.5.30")
            cpe_products: CPE 產品清單，格式：[{"vendor": "apache", "product": "struts", "version": "2.5.30"}]

        Returns:
            (是否匹配, 匹配類型, 信心度)
        """
        if not tech_name or not cpe_products:
            return False, "unknown", 0.0

        tech_name_lower = tech_name.lower()

        for cpe_product in cpe_products:
            vendor = cpe_product.get("vendor", "").lower()
            product = cpe_product.get("product", "").lower()
            cpe_version = cpe_product.get("version", "")

            # 檢查技術名稱是否匹配
            name_match = False
            if product in tech_name_lower or tech_name_lower in product:
                name_match = True
            elif vendor in tech_name_lower:
                name_match = True

            if not name_match:
                continue

            # 檢查版本是否匹配
            if not tech_version or cpe_version == "*":
                # 版本未知或 CPE 為萬用字元，降低信心度
                return True, "unknown", 0.5

            # 版本匹配
            is_affected, match_type, confidence = VersionMatcher.is_version_affected(
                tech_version, [cpe_version]
            )

            if is_affected:
                return True, match_type, confidence

        return False, "unknown", 0.0
