"""
JavaScript parser module for extracting API endpoints and parameters.
"""

import json
import subprocess
import tempfile
import os
import time
from typing import List, Dict, Any

from ..core.config import ParserConfig


class JavaScriptParser:
    """Parser for JavaScript code using Node.js sandbox to extract API endpoints."""

    def __init__(self, config: ParserConfig):
        self.config = config
        self.sandbox_path = os.path.join(
            os.path.dirname(__file__), "..", "sandbox_direct.js"
        )
        # Node.js 可能未安裝（celery/django 容器預設不含 node）。
        # 改為延遲失敗：標記可用性，parse() 直接回空，不讓 SecurityAnalyzer 構造崩潰。
        self._available = self._check_sandbox_available()

    def _check_sandbox_available(self) -> bool:
        """檢查 sandbox 腳本與 Node.js 是否可用。失敗時記錄並回 False，不拋例外。"""
        if not os.path.exists(self.sandbox_path):
            print(f"[js_parser] Sandbox script not found: {self.sandbox_path}")
            return False
        try:
            result = subprocess.run(
                ["node", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                print("[js_parser] Node.js is installed but returned non-zero exit")
                return False
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("[js_parser] Node.js is not available or timed out — JS endpoint extraction disabled")
            return False

    def parse(self, js_code: str) -> List[Dict]:
        """
        Parse JavaScript code using Node.js sandbox and extract API endpoints.

        Args:
            js_code: JavaScript code to parse

        Returns:
            List of endpoint information
        """
        # Node.js 未安裝時優雅降級：回空列表，不拋例外
        if not getattr(self, "_available", False):
            return []
        try:
            # Use the sandbox to extract endpoints
            sandbox_results = self._run_sandbox_extraction(js_code)

            # Convert sandbox results to the expected format
            endpoints = []
            seen_endpoints = set()

            for result in sandbox_results:
                endpoint_info = self._convert_sandbox_result(result)

                if endpoint_info and "url" in endpoint_info:
                    endpoint_key = (
                        endpoint_info.get("url", ""),
                        endpoint_info.get("method", ""),
                    )
                    if endpoint_key not in seen_endpoints:
                        endpoint_info["source"] = "javascript"
                        endpoint_info["line"] = (
                            0  # Sandbox doesn't provide line numbers
                        )
                        if "parameters" not in endpoint_info:
                            endpoint_info["parameters"] = []
                        endpoints.append(endpoint_info)
                        seen_endpoints.add(endpoint_key)

            return endpoints

        except Exception as e:
            print(f"Sandbox parsing failed: {e}")
            return []

    def _run_sandbox_extraction(self, js_code: str) -> List[Dict]:
        """Run the JavaScript code in the Node.js sandbox and extract endpoints."""
        try:
            result = subprocess.run(
                ["node", self.sandbox_path],
                input=js_code,
                text=True,
                capture_output=True,
                timeout=30,  # 30 second timeout
                cwd=os.path.dirname(self.sandbox_path),
            )

            if result.returncode != 0:
                print(f"Sandbox error: {result.stderr}")
                return []

            # Parse the JSON output from the sandbox
            try:
                sandbox_output = json.loads(result.stdout)
                if isinstance(sandbox_output, list):
                    return sandbox_output
                else:
                    print(f"Unexpected sandbox output format: {type(sandbox_output)}")
                    return []
            except json.JSONDecodeError as e:
                print(f"Failed to parse sandbox output: {e}")
                print(f"Raw output: {result.stdout}")
                return []

        except subprocess.TimeoutExpired:
            print("Sandbox execution timed out")
            return []
        except Exception as e:
            print(f"Error running sandbox: {e}")
            return []

    def _convert_sandbox_result(self, sandbox_result: Dict) -> Dict:
        """Convert sandbox result to the expected endpoint format."""
        if not isinstance(sandbox_result, dict):
            return {}

        endpoint_info = {
            "url": sandbox_result.get("url", ""),
            "method": sandbox_result.get("method", "GET"),
            "parameters": [],
        }

        # Convert parameters from sandbox format
        sandbox_params = sandbox_result.get("parameters", [])
        if isinstance(sandbox_params, list):
            for param in sandbox_params:
                if isinstance(param, dict):
                    converted_param = {
                        "name": param.get("name", ""),
                        "data_type": param.get("type", "unknown"),
                        "source": "javascript",
                    }
                    endpoint_info["parameters"].append(converted_param)

        return endpoint_info
