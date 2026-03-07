#!/usr/bin/env python3
"""
Simple wrapper script for the Security Parameter Parser
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security_parser import SecurityAnalyzer

def main():
    """Simple usage example"""
    if len(sys.argv) < 2:
        print("Usage: python simple_parser.py <base_url> [js_file] [forms_file]")
        sys.exit(1)
    
    base_url = sys.argv[1]
    js_file = sys.argv[2] if len(sys.argv) > 2 else None
    forms_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Load JavaScript code
    js_code = ""
    if js_file:
        try:
            with open(js_file, 'r', encoding='utf-8') as f:
                js_code = f.read()
        except Exception as e:
            print(f"Error loading JS file: {e}")
            sys.exit(1)
    
    # Load forms data
    forms_data = []
    if forms_file:
        try:
            import json
            with open(forms_file, 'r', encoding='utf-8') as f:
                forms_data = json.load(f)
        except Exception as e:
            print(f"Error loading forms file: {e}")
            sys.exit(1)
    
    # Run analysis
    analyzer = SecurityAnalyzer()
    json_output = analyzer.analyze_to_json(base_url, js_code, forms_data)
    
    print(json_output)

if __name__ == "__main__":
    main()