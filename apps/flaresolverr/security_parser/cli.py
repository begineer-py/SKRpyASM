#!/usr/bin/env python3
"""
Security Parameter Parser - Command Line Interface
A comprehensive tool for extracting and analyzing security parameters from JavaScript and HTML forms.
"""

import json
import argparse
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from security_parser import SecurityAnalyzer


def load_json_file(filepath: str) -> dict:
    """Load JSON data from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        sys.exit(1)


def load_js_file(filepath: str) -> str:
    """Load JavaScript code from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Security Parameter Parser - Extract security parameters from JavaScript and HTML forms"
    )
    
    parser.add_argument(
        "--base-url",
        required=True,
        help="Base URL for resolving relative paths"
    )
    
    parser.add_argument(
        "--js-file",
        help="Path to JavaScript file to analyze"
    )
    
    parser.add_argument(
        "--forms-file",
        help="Path to JSON file containing form definitions"
    )
    
    parser.add_argument(
        "--js-code",
        help="JavaScript code string to analyze"
    )
    
    parser.add_argument(
        "--output-file",
        help="Output JSON file path (default: stdout)"
    )
    
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print JSON output"
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary statistics only"
    )
    
    args = parser.parse_args()
    
    # Load JavaScript code
    js_code = ""
    if args.js_file:
        js_code = load_js_file(args.js_file)
    elif args.js_code:
        js_code = args.js_code
    
    # Load forms data
    forms_data = []
    if args.forms_file:
        forms_data = load_json_file(args.forms_file)
        if not isinstance(forms_data, list):
            print("Forms file must contain a list of form definitions")
            sys.exit(1)
    
    # Create analyzer and run analysis
    analyzer = SecurityAnalyzer()
    results = analyzer.analyze(args.base_url, js_code, forms_data)
    
    # Generate JSON output
    json_output = analyzer.analyze_to_json(args.base_url, js_code, forms_data)
    
    if args.summary:
        # Show summary only
        data = json.loads(json_output)
        summary = data.get("summary", {})
        print(json.dumps(summary, indent=2 if args.pretty else None))
    else:
        # Show full output
        if args.pretty:
            data = json.loads(json_output)
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(json_output)
    
    # Save to file if specified
    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(json_output)
        print(f"\nResults saved to: {args.output_file}")


if __name__ == "__main__":
    main()