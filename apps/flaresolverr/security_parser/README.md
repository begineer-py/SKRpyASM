# Security Parameter Parser

A comprehensive tool for extracting and analyzing security parameters from JavaScript code and HTML forms.

## Features

- **Decoupled Architecture**: Modular design with separate components for parsing, processing, and exporting
- **Multi-source Analysis**: Extract parameters from JavaScript API calls and HTML form data
- **URL Resolution**: Automatically converts relative URLs to absolute paths
- **Smart Parameter Classification**: Separates query vs body parameters based on HTTP method
- **JSON Export**: Structured JSON output with metadata and summary statistics
- **Command Line Interface**: Easy-to-use CLI for batch processing

## Project Structure

```
security_parser/
├── __init__.py              # Main module exports
├── cli.py                   # Command line interface
├── core/                    # Core components
│   ├── __init__.py
│   ├── analyzer.py          # Main security analyzer
│   └── config.py            # Configuration settings
├── parsers/                 # Data parsers
│   ├── __init__.py
│   ├── js_parser.py         # JavaScript parser
│   └── form_parser.py       # Form data parser
├── utils/                   # Utility modules
│   ├── __init__.py
│   ├── url_processor.py     # URL processing utilities
│   └── json_exporter.py     # JSON export utilities
└── tests/                   # Test suite
    ├── __init__.py
    └── test_suite.py         # Comprehensive tests
```

## Installation

1. Install dependencies:
```bash
pip install esprima
```

2. The parser is ready to use!

## Usage

### Command Line Interface

```bash
# Basic usage with JavaScript file and forms data
python security_parser/cli.py \
    --base-url "https://api.target.com" \
    --js-file "app.js" \
    --forms-file "forms.json" \
    --output-file "results.json" \
    --pretty

# With JavaScript code directly
python security_parser/cli.py \
    --base-url "https://api.target.com" \
    --js-code "axios.post('/api/login', {username: 'admin'})" \
    --summary

# Process forms only
python security_parser/cli.py \
    --base-url "https://example.com" \
    --forms-file "forms.json" \
    --output-file "analysis.json"
```

### Python API

```python
from security_parser import SecurityAnalyzer

# Create analyzer
analyzer = SecurityAnalyzer()

# Analyze JavaScript and form data
results = analyzer.analyze(
    base_url="https://api.target.com",
    js_code="axios.post('/api/login', {username: 'admin', password: '123'})",
    forms_data=[{
        "action": "search.php",
        "method": "POST", 
        "parameters": [{"name": "query", "type": "text"}]
    }]
)

# Export to JSON
json_output = analyzer.analyze_to_json(
    base_url="https://api.target.com",
    js_code=js_code,
    forms_data=forms_data,
    output_file="security_analysis.json"
)
```

## Input Formats

### JavaScript Code
The parser supports:
- `axios.get/post/put/delete()` calls
- `fetch()` calls with options
- JSON.stringify() wrapped parameters
- Template literals for URLs

### Forms Data
```json
[
  {
    "action": "search.php?test=query",
    "method": "POST",
    "parameters": [
      {"name": "searchFor", "type": "text"},
      {"name": "goButton", "type": "submit"}
    ]
  }
]
```

## Output Format

```json
{
  "metadata": {
    "generated_at": "2024-01-01T12:00:00",
    "parser_version": "1.0.0",
    "format": "security_parameter_analysis",
    "description": "Security parameter analysis results"
  },
  "summary": {
    "total_endpoints": 3,
    "total_query_parameters": 5,
    "total_body_parameters": 8,
    "methods": {"GET": 1, "POST": 2},
    "types": {"javascript": 2, "form": 1},
    "domains": ["api.target.com"],
    "parameter_types": {"javascript": 6, "form": 4, "querystring": 3}
  },
  "endpoints": [
    {
      "url": "https://api.target.com/api/login",
      "method": "POST",
      "queryParams": [],
      "bodyParams": [
        {"name": "username", "type": "javascript"},
        {"name": "password", "type": "javascript"}
      ],
      "type": "javascript"
    }
  ]
}
```

## Testing

Run the comprehensive test suite:

```bash
cd security_parser/tests
python test_suite.py
```

The test suite includes:
- Basic functionality tests
- URL resolution tests
- Parameter classification tests
- JSON export tests
- Real-world example processing

## Configuration

The parser can be customized through the `ParserConfig` class:

```python
from security_parser.core.config import ParserConfig
from security_parser import SecurityAnalyzer

config = ParserConfig()
config.query_methods = ["GET", "DELETE", "HEAD", "OPTIONS"]
config.type_priorities = {"form": 3, "javascript": 2, "querystring": 1}

analyzer = SecurityAnalyzer(config)
```

## Error Handling

The parser includes comprehensive error handling:
- Invalid JavaScript syntax tolerance
- Malformed JSON handling
- URL processing errors
- Missing or invalid form data
- Graceful fallbacks for edge cases

## Use Cases

- **Security Testing**: Extract parameters for penetration testing
- **API Documentation**: Generate parameter lists from frontend code
- **Compliance Auditing**: Identify all data collection points
- **Bug Bounty**: Map attack surface of web applications
- **Code Analysis**: Understand data flow in web applications

## License

This project is part of a security analysis toolkit. Use responsibly and only on systems you have permission to test.