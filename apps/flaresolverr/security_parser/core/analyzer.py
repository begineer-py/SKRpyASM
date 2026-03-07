"""
核心安全分析模組。
"""

from typing import List, Dict, Any, Optional
import json

from .config import ParserConfig
from ..parsers.js_parser import JavaScriptParser
from ..parsers.form_parser import FormParser
from ..utils.url_processor import URLProcessor
from ..utils.json_exporter import JSONExporter


class SecurityAnalyzer:
    """主安全分析器，負責協調整個解析過程。"""

    def __init__(self, config: Optional[ParserConfig] = None):
        """
        初始化分析器。

        Args:
            config: 解析配置對象，若為 None 則使用預設配置
        """
        self.config = config or ParserConfig()
        self.js_parser = JavaScriptParser(self.config)
        self.form_parser = FormParser(self.config)
        self.url_processor = URLProcessor(self.config)
        self.json_exporter = JSONExporter(self.config)

    def analyze(
        self, base_url: str, js_code: str = "", forms_data: List[Dict] = None
    ) -> List[Dict]:
        """
        分析 JavaScript 程式碼和表單數據以提取安全參數。

        Args:
            base_url: 用於解析相對路徑的基礎 URL
            js_code: 要分析的 JavaScript 程式碼
            forms_data: 表單定義列表

        Returns:
            包含提取參數的端點結果列表
        """
        if forms_data is None:
            forms_data = []

        try:
            # 提取 JavaScript 中的端點 (Endpoints)
            js_endpoints = self.js_parser.parse(js_code) if js_code else []

            # 處理每個表單數據
            form_results = []
            for form_data in forms_data:
                form_result = self.form_parser.parse(base_url, form_data)
                form_results.append(form_result)

            # 合併 JavaScript 端點與表單數據
            merged_results = self._merge_js_and_form_data(
                js_endpoints, form_results, base_url
            )

            return merged_results

        except Exception as e:
            # 發生異常時返回空列表
            return []

    def analyze_to_json(
        self,
        base_url: str,
        js_code: str = "",
        forms_data: List[Dict] = None,
        output_file: Optional[str] = None,
    ) -> str:
        """
        分析並將結果導出為 JSON 格式。

        Args:
            base_url: 用於解析相對路徑的基礎 URL
            js_code: 要分析的 JavaScript 程式碼
            forms_data: 表單定義列表
            output_file: 可選，用於儲存 JSON 輸出的文件路徑

        Returns:
            分析結果的 JSON 字串
        """
        results = self.analyze(base_url, js_code, forms_data)
        json_output = self.json_exporter.export(results)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(json_output)

        return json_output

    def _merge_js_and_form_data(
        self, js_endpoints: List[Dict], form_results: List[Dict], base_url: str
    ) -> List[Dict]:
        """合併 JavaScript 端點與表單結果，並進行智慧去重。"""
        # 使用以「規範化 URL + 方法」為鍵的字典進行智慧合併
        merged_dict = {}

        # 優先處理表單結果
        for form_result in form_results:
            key = self._normalize_endpoint_key(
                form_result.get("url", ""), form_result.get("method", "GET")
            )
            merged_dict[key] = {**form_result, "sources": ["form"]}

        # 處理 JavaScript 端點並與現有端點合併
        for js_endpoint in js_endpoints:
            js_url_info = self.url_processor.resolve_url(
                base_url, js_endpoint.get("url", "")
            )
            js_params = js_endpoint.get("parameters", [])
            js_classified = self._classify_parameters(
                js_endpoint.get("method", "GET"), js_params
            )

            js_endpoint_result = {
                "url": js_url_info["absolute_url"],
                "method": js_endpoint.get("method", "GET"),
                "queryParams": js_classified["queryParams"],
                "bodyParams": js_classified["bodyParams"],
                "type": "javascript",
            }

            key = self._normalize_endpoint_key(
                js_endpoint_result["url"], js_endpoint_result["method"]
            )

            if key in merged_dict:
                # 若端點已存在則進行合併
                existing = merged_dict[key]

                # 合併查詢參數 (Query Parameters)
                merged_query_params = self._merge_parameter_lists(
                    existing.get("queryParams", []),
                    js_endpoint_result.get("queryParams", []),
                )

                # 合併請求體參數 (Body Parameters)
                merged_body_params = self._merge_parameter_lists(
                    existing.get("bodyParams", []),
                    js_endpoint_result.get("bodyParams", []),
                )

                # 更新合併後的項目
                merged_dict[key].update(
                    {
                        "queryParams": merged_query_params,
                        "bodyParams": merged_body_params,
                        "type": "merged",  # 標記此端點具有多個來源
                        "sources": existing.get("sources", []) + ["javascript"],
                    }
                )
            else:
                # 若不存在則新增端點
                merged_dict[key] = {**js_endpoint_result, "sources": ["javascript"]}

        # 轉回列表格式並清理內部標記
        result = []
        for endpoint in merged_dict.values():
            # 移除用於內部追蹤的欄位
            endpoint_copy = {k: v for k, v in endpoint.items() if k != "sources"}
            result.append(endpoint_copy)

        return result

    def _normalize_endpoint_key(self, url: str, method: str) -> str:
        """創建用於端點去重的規範化鍵值。"""
        if not url:
            url = ""

        # 移除查詢參數和片段識別符 (#)
        url = url.split("?")[0].split("#")[0]

        # 移除結尾斜槓並轉為小寫
        url = url.rstrip("/").lower()

        # 規範化 HTTP 方法
        method = method.upper().strip() if method else "GET"

        return f"{method}:{url}"

    def _merge_parameter_lists(
        self, existing_params: List[Dict], new_params: List[Dict]
    ) -> List[Dict]:
        """合併兩個參數列表，移除重複項並保留優先級較高的來源。"""
        param_dict = {}

        # 首先加入現有的參數
        for param in existing_params:
            name = param.get("name", "")
            if name:
                param_dict[name] = param

        # 加入新參數，如果新參數的優先級更高則覆蓋
        for param in new_params:
            name = param.get("name", "")
            if name:
                if name not in param_dict:
                    param_dict[name] = param
                else:
                    # 比較來源優先級
                    existing_priority = self.config.type_priorities.get(
                        param_dict[name].get("source", ""), 0
                    )
                    new_priority = self.config.type_priorities.get(
                        param.get("source", ""), 0
                    )
                    if new_priority > existing_priority:
                        param_dict[name] = param
                    elif new_priority == existing_priority:
                        # 優先級相同時，嘗試合併額外資訊
                        existing_param = param_dict[name]
                        # 如果新參數有行號而現有參數沒有，則保留行號
                        if "line" not in existing_param and "line" in param:
                            existing_param["line"] = param["line"]

        return list(param_dict.values())

    def _classify_parameters(self, method: str, parameters: List[Dict]) -> Dict:
        """根據 HTTP 方法將參數歸類為 Query 或 Body。"""
        if not parameters:
            return {"queryParams": [], "bodyParams": []}

        method = self.config.normalize_method(method)

        if self.config.is_query_method(method):
            return {"queryParams": parameters, "bodyParams": []}
        else:
            return {"queryParams": [], "bodyParams": parameters}

    def _remove_duplicate_params(self, params: List[Dict]) -> List[Dict]:
        """移除重複參數，僅保留來源類型最精確的參數。"""
        seen = {}
        for param in params:
            name = param.get("name", "")
            if name not in seen:
                seen[name] = param
            else:
                current_priority = self.config.type_priorities.get(
                    param.get("source", ""), 0
                )
                existing_priority = self.config.type_priorities.get(
                    seen[name].get("source", ""), 0
                )
                if current_priority > existing_priority:
                    seen[name] = param

        return list(seen.values())
