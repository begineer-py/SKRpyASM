"""
URL processing utilities.
"""

import urllib.parse
from typing import Dict, List

from ..core.config import ParserConfig


class URLProcessor:
    """Utility class for URL processing and manipulation."""

    def __init__(self, config: ParserConfig):
        self.config = config

    def resolve_url(self, base_url: str, relative_url: str) -> Dict:
        """
        Convert relative URL to absolute and extract query parameters.

        Args:
            base_url: Base URL for resolution
            relative_url: Relative or absolute URL to process

        Returns:
            Dictionary with absolute URL and extracted query parameters
        """
        try:
            absolute_url = urllib.parse.urljoin(
                base_url or self.config.default_base_url, relative_url
            )
            parsed = urllib.parse.urlparse(absolute_url)

            query_params = []
            if parsed.query:
                for param_name, param_value in urllib.parse.parse_qsl(parsed.query):
                    query_params.append(
                        {
                            "name": param_name,
                            "source": "querystring",
                            "data_type": "string",
                            "value": param_value,
                        }
                    )

            return {
                "absolute_url": absolute_url,
                "query_params": query_params,
                "path": parsed.path,
            }
        except Exception as e:
            return {"absolute_url": relative_url, "query_params": [], "path": ""}

    def normalize_url(self, url: str) -> str:
        """Normalize URL format."""
        if not url:
            return ""

        # Remove fragments and normalize scheme
        parsed = urllib.parse.urlparse(url)
        normalized = urllib.parse.urlunparse(
            (
                parsed.scheme or "https",
                parsed.netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                "",  # Remove fragment
            )
        )
        return normalized

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc
        except:
            return ""

    def is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs belong to the same domain."""
        domain1 = self.extract_domain(url1)
        domain2 = self.extract_domain(url2)
        return domain1.lower() == domain2.lower()
