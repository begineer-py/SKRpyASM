import json
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_parser import SecurityAnalyzer
from security_parser.core.config import ParserConfig


def run_impossible_test():
    config = ParserConfig()
    analyzer = SecurityAnalyzer(config)
    base_url = "https://bank-system.com"

    # --- 這是一段不執行就絕對抓不到真相的 JS ---
    # 1. 所有的路徑和 Key 都是 Base64 加密的
    # 2. 參數值是動態計算的 (Date.now)
    # 3. 最終呼叫是透過 eval 執行的
    js_code = """
    (function() {
        var _0xhidden_data = ["L2FwaS92MS90cmFuc2Zlcg==", "POST", "YW1vdW50", "Y3VycmVuY3k=", "dG9rZW4="];
        
        function _decode(idx) {
            // 模擬 Base64 解碼
            return atob(_0xhidden_data[idx]);
        }

        var _u = _decode(0); // "/api/v1/transfer"
        var _m = _0xhidden_data[1];
        
        var payload = {};
        payload[_decode(2)] = 1000 + 500; // amount: 1500
        payload[_decode(3)] = "USD";      // currency: "USD"
        payload[_decode(4)] = (function(s){ return s.split('').reverse().join(''); })("98765-X-123");

        // 靜態分析最怕的 eval
        var cmd = "fetch('" + _u + "', {method:'" + _m + "', body: JSON.stringify(" + JSON.stringify(payload) + ")})";
        eval(cmd);
    })();
    """

    # 直接輸出 JSON 結果
    results_json = analyzer.analyze_to_json(
        base_url=base_url, js_code=js_code, forms_data=[]
    )

    print(results_json)


if __name__ == "__main__":
    run_impossible_test()
