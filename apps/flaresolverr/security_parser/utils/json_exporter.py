"""
JSON export utilities for the security parameter parser.
"""

import json
from datetime import datetime
from typing import List, Dict, Any

from ..core.config import ParserConfig


class JSONExporter:
    """Utility class for exporting analysis results to JSON format."""

    def __init__(self, config: ParserConfig):
        self.config = config

    def export(self, results: List[Dict]) -> str:
        """
        Export analysis results to JSON format.

        Args:
            results: List of analysis results

        Returns:
            JSON string representation
        """
        export_data = {
            "metadata": self._create_metadata(),
            "summary": self._create_summary(results),
            "endpoints": results,
        }

        return json.dumps(export_data, indent=2, ensure_ascii=False)

    def export_to_file(self, results: List[Dict], filename: str) -> None:
        """
        Export analysis results to JSON file.

        Args:
            results: List of analysis results
            filename: Output filename
        """
        json_output = self.export(results)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(json_output)

    def _create_metadata(self) -> Dict:
        """Create metadata for the export."""
        return {
            "generated_at": datetime.now().isoformat(),
            "parser_version": "1.0.0",
            "format": "security_parameter_analysis",
            "description": "Security parameter analysis results from JavaScript and form data",
        }

    def _create_summary(self, results: List[Dict]) -> Dict:
        """Create summary statistics from results."""
        total_endpoints = len(results)
        total_query_params = sum(
            len(endpoint.get("queryParams", [])) for endpoint in results
        )
        total_body_params = sum(
            len(endpoint.get("bodyParams", [])) for endpoint in results
        )

        method_counts = {}
        type_counts = {}
        domains = set()

        for endpoint in results:
            method = endpoint.get("method", "GET")
            endpoint_type = endpoint.get("type", "unknown")
            domain = self._extract_domain(endpoint.get("url", ""))

            method_counts[method] = method_counts.get(method, 0) + 1
            type_counts[endpoint_type] = type_counts.get(endpoint_type, 0) + 1
            if domain:
                domains.add(domain)

        return {
            "total_endpoints": total_endpoints,
            "total_query_parameters": total_query_params,
            "total_body_parameters": total_body_params,
            "methods": method_counts,
            "types": type_counts,
            "domains": list(domains),
            "parameter_types": self._count_parameter_types(results),
        }

    def _count_parameter_types(self, results: List[Dict]) -> Dict:
        """Count parameter types across all endpoints."""
        type_counts = {}

        for endpoint in results:
            query_params = endpoint.get("queryParams", [])
            body_params = endpoint.get("bodyParams", [])

            # Ensure we're working with lists
            if not isinstance(query_params, list):
                query_params = []
            if not isinstance(body_params, list):
                body_params = []

            all_params = query_params + body_params
            for param in all_params:
                param_type = param.get("source", "unknown")
                type_counts[param_type] = type_counts.get(param_type, 0) + 1

        return type_counts

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            import urllib.parse

            parsed = urllib.parse.urlparse(url)
            return parsed.netloc
        except:
            return ""
