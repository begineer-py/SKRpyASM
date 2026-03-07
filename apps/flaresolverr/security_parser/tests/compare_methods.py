import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_parser import SecurityAnalyzer
from security_parser.core.config import ParserConfig

def compare_methods():
    config = ParserConfig()
    analyzer = SecurityAnalyzer(config)
    
    js_code = """
    axios.post('/api/login', {
        username: 'admin',
        password: 'secret123',
        remember: true
    });
    """
    
    print("=== analyze() 方法結果 ===")
    analyze_results = analyzer.analyze(
        base_url="https://example.com",
        js_code=js_code,
        forms_data=[]
    )
    
    print("類型:", type(analyze_results))
    print("內容:", json.dumps(analyze_results, indent=2, ensure_ascii=False))
    
    print("\n" + "="*50)
    print("=== analyze_to_json() 方法結果 ===")
    json_results = analyzer.analyze_to_json(
        base_url="https://example.com",
        js_code=js_code,
        forms_data=[]
    )
    
    print("類型:", type(json_results))
    print("內容:", json_results)

if __name__ == "__main__":
    compare_methods()
