"""
Form parser module for processing HTML form data.
"""

from typing import List, Dict, Any

from ..core.config import ParserConfig
from ..utils.url_processor import URLProcessor


class FormParser:
    """Parser for HTML form data."""

    def __init__(self, config: ParserConfig):
        self.config = config
        self.url_processor = URLProcessor(config)

    def parse(self, base_url: str, form_data: Dict) -> Dict:
        """
        Parse individual form and extract parameters.

        Args:
            base_url: Base URL for resolving relative paths
            form_data: Form definition dictionary

        Returns:
            Processed form result with extracted parameters
        """
        try:
            action = form_data.get("action", "")
            method = self.config.normalize_method(form_data.get("method", "GET"))
            parameters = form_data.get("parameters", [])

            # Process URL
            url_info = self.url_processor.resolve_url(base_url, action)

            # Convert form parameters to standard format
            form_params = []
            for param in parameters:
                param_info = {
                    "name": param.get("name", ""),
                    "source": "form",
                    "data_type": "string",
                    "input_type": param.get("type", "text"),
                }
                form_params.append(param_info)

            # Classify parameters based on method
            classified = self._classify_parameters(method, form_params)

            # Combine with existing query parameters from URL
            all_query_params = url_info["query_params"] + classified["queryParams"]

            return {
                "url": url_info["absolute_url"],
                "method": method,
                "queryParams": all_query_params,
                "bodyParams": classified["bodyParams"],
                "type": "form",
            }
        except Exception as e:
            return {
                "url": "",
                "method": "GET",
                "queryParams": [],
                "bodyParams": [],
                "type": "form",
            }

    def _classify_parameters(self, method: str, parameters: List[Dict]) -> Dict:
        """Classify parameters as query or body based on HTTP method."""
        if not parameters:
            return {"queryParams": [], "bodyParams": []}

        method = self.config.normalize_method(method)

        if self.config.is_query_method(method):
            return {"queryParams": parameters, "bodyParams": []}
        else:
            return {"queryParams": [], "bodyParams": parameters}