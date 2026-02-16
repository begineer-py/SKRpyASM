"""
Security Parameter Parser - Main Module
A comprehensive tool for extracting and analyzing security parameters from JavaScript and HTML forms.
"""

from .core.analyzer import SecurityAnalyzer
from .core.config import ParserConfig
from .parsers.js_parser import JavaScriptParser
from .parsers.form_parser import FormParser
from .utils.url_processor import URLProcessor
from .utils.json_exporter import JSONExporter

__version__ = "1.0.0"
__all__ = [
    "SecurityAnalyzer",
    "ParserConfig", 
    "JavaScriptParser",
    "FormParser", 
    "URLProcessor",
    "JSONExporter"
]