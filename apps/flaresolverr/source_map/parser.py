import json
import base64
import logging
from dataclasses import dataclass, field
from urllib.parse import unquote

logger = logging.getLogger(__name__)


@dataclass
class SourceMapData:
    map_url: str
    sources: list = field(default_factory=list)
    sources_content: list = field(default_factory=list)
    file: str = None


class SourceMapParser:
    """下載並解析 JavaScript Source Map，提取路徑洩漏、機密與 API endpoint。"""

    def __init__(self):
        from apps.flaresolverr.gf.hacker_gf.pygf import PatternAnalyzer
        from apps.flaresolverr.security_parser import SecurityAnalyzer
        self._pattern_analyzer = PatternAnalyzer()
        self._security_analyzer = SecurityAnalyzer()

    def fetch_and_parse(self, map_url: str) -> "SourceMapData | None":
        """下載並解析 source map，失敗時回傳 None。"""
        if map_url.startswith("data:application/json"):
            return self._parse_data_uri(map_url)
        from apps.flaresolverr.utils import downloader
        content = downloader(map_url)
        if not content:
            logger.warning(f"[SourceMap] 無法下載: {map_url[:80]}")
            return None
        return self._parse_json(map_url, content)

    def _parse_data_uri(self, data_uri: str) -> "SourceMapData | None":
        try:
            header, _, payload = data_uri.partition(",")
            if "base64" in header:
                content = base64.b64decode(payload).decode("utf-8", errors="replace")
            else:
                content = unquote(payload)
            return self._parse_json("data:...inline...", content)
        except Exception as e:
            logger.error(f"[SourceMap] inline data URI 解碼失敗: {e}")
            return None

    def _parse_json(self, map_url: str, content: str) -> "SourceMapData | None":
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"[SourceMap] JSON 解析失敗 ({map_url[:60]}): {e}")
            return None
        if not isinstance(data, dict):
            return None
        return SourceMapData(
            map_url=map_url,
            sources=data.get("sources") or [],
            sources_content=data.get("sourcesContent") or [],
            file=data.get("file"),
        )

    def extract_findings(self, data: SourceMapData) -> list[dict]:
        """從 source map 提取安全 findings：路徑洩漏 + gf pattern 命中。"""
        findings = []

        # 1. 路徑洩漏：sources[] 中的原始檔案路徑
        for i, path in enumerate(data.sources):
            if path:
                findings.append({
                    "pattern": "source_map_path",
                    "line": i,
                    "match": path,
                })

        # 2. 機密掃描：對每個 sourcesContent 執行 gf 22 種 pattern
        for i, source_code in enumerate(data.sources_content):
            if not source_code:
                continue
            source_label = data.sources[i] if i < len(data.sources) else f"source_{i}"
            lines = source_code.splitlines()
            try:
                gf_results = self._pattern_analyzer.run_all_patterns(lines)
            except Exception as e:
                logger.error(f"[SourceMap] gf 掃描失敗 ({source_label}): {e}")
                continue
            for group in gf_results:
                pattern_name = group.get("pattern", "unknown")
                for match in group.get("matches", []):
                    findings.append({
                        "pattern": f"srcmap_{pattern_name}",
                        "line": match.get("line", 0),
                        "match": match.get("match", ""),
                        "source_file": source_label,
                    })

        return findings

    def extract_endpoints(self, data: SourceMapData, base_url: str) -> list[dict]:
        """從 sourcesContent 的原始碼中提取 API endpoint。"""
        endpoints = []
        for source_code in data.sources_content:
            if not source_code:
                continue
            try:
                result = self._security_analyzer.analyze(
                    base_url=base_url,
                    js_code=source_code,
                    forms_data=[],
                )
                endpoints.extend(result)
            except Exception as e:
                logger.error(f"[SourceMap] SecurityAnalyzer 失敗: {e}")
        return endpoints
