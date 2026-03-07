"""
Configuration module for the security parameter parser.
"""


class ParserConfig:
    """Configuration class for parser settings."""

    def __init__(self):
        # HTTP methods for parameter classification
        self.query_methods = ["GET", "DELETE", "HEAD", "OPTIONS"]
        self.body_methods = ["POST", "PUT", "PATCH"]

        # Parameter type priorities for conflict resolution
        self.type_priorities = {"form": 3, "javascript": 2, "querystring": 1}

        # Reserved request configuration keys to filter out
        self.reserved_keys = [
            "method",
            "headers",
            "body",
            "url",
            "mode",
            "credentials",
            "cache",
            "redirect",
            "referrer",
            "integrity",
            "keepalive",
        ]

        # JavaScript libraries and methods to track
        self.js_libraries = {
            "axios": ["post", "put", "patch", "get", "delete"],
            "fetch": [],  # fetch uses different pattern
        }

        # Default base URL for relative URL resolution
        self.default_base_url = "https://localhost"

    def is_query_method(self, method: str) -> bool:
        """Check if method uses query parameters."""
        return method.upper().strip() in self.query_methods

    def is_body_method(self, method: str) -> bool:
        """Check if method uses body parameters."""
        return method.upper().strip() in self.body_methods

    def normalize_method(self, method: str) -> str:
        """Normalize HTTP method to uppercase."""
        return method.upper().strip() if method else "GET"
