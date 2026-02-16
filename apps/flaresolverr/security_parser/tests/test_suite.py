import json
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_parser import SecurityAnalyzer
from security_parser.core.config import ParserConfig


def run_real_test():
    # 1. 初始化配置
    config = ParserConfig()
    analyzer = SecurityAnalyzer(config)

    # 模擬基礎網址
    base_url = "https://secure-shop.example.com/api/v1"

    # 2. 準備表單數據 (對應 FormParser 的預期格式)
    # 這是最關鍵的：Action URL 指向 /auth/submit
    forms_data = [
        {
            "action": "/auth/submit",
            "method": "POST",
            "parameters": [
                {"name": "csrf_token", "type": "hidden", "value": "x8822-asdf-9901"},
                {"name": "user_id", "type": "text"},
                {"name": "pass_hash", "type": "password"},
            ],
        }
    ]

    # 3. 準備增強的 JavaScript 程式碼測試新功能
    js_code = """
    (function() {
        // 基礎變數測試
        var _0x41a2 = "/auth/submit";
        
        // 物件變數測試
        var _0x98b1 = {
            "browser_fingerprint": "fp_001",
            "is_headless": false,
            "ua_hash": "a2b3c4"
        };
        
        // 動態建構測試 - Object.assign
        var _0x77d3 = Object.assign({}, _0x98b1, {
            "timestamp": 1707986534,
            "session_id": "sess_123"
        });
        
        // Spread operator 測試
        var _0x99f4 = {
            ..._0x77d3,
            "additional_field": "test_value"
        };
        
        // 模板字串測試
        var baseUrl = "https://secure-shop.example.com";
        var endpoint = `${baseUrl}/api/v1/auth/submit`;
        
        // 基礎 axios 請求
        axios.post(_0x41a2, _0x98b1);
        
        // 使用動態建構的參數
        axios.post(endpoint, _0x99f4);
        
        // 使用 JSON.stringify 與變數
        axios.post('/auth/submit', JSON.stringify(_0x77d3));
        
        // fetch 請求測試
        fetch('/auth/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                event: 'login_attempt',
                ..._0x98b1,
                dynamic_field: 'dynamic_value'
            })
        });
        
        // 測試不同 URL (不應該被合併)
        var analyticsUrl = "https://analytics.example.com/track";
        fetch(analyticsUrl, {
            method: 'POST',
            body: JSON.stringify({
                event: 'page_view',
                url: window.location.href
            })
        });
    })();
    """

    # print("--- 開始執行安全性解析 ---")

    # 執行解析
    results_json = analyzer.analyze_to_json(
        base_url=base_url, js_code=js_code, forms_data=forms_data
    )

    # 格式化輸出
    parsed_results = json.loads(results_json)
    print(json.dumps(parsed_results, indent=2))

    # 驗證結果
    endpoints = parsed_results.get("endpoints", [])
    if not endpoints:
        print("\n❌ 失敗：還是什麼都沒抓到，這工具依然是廢物。")
    else:
        return
        print(f"\n✅ 成功：抓到了 {len(endpoints)} 個端點！")

        # 檢查是否有正確的合併
        auth_submit_endpoints = [ep for ep in endpoints if "/auth/submit" in ep["url"]]
        analytics_endpoints = [
            ep for ep in endpoints if "analytics.example.com" in ep["url"]
        ]

        print(f"\n📊 分析結果:")
        print(
            f" - /auth/submit 相關端點: {len(auth_submit_endpoints)} 個 (應該是 1 個合併後的端點)"
        )
        print(f" - analytics 端點: {len(analytics_endpoints)} 個")

        for ep in endpoints:
            print(
                f"\n🔗 端點: {ep['url']} ({ep['method']}) - 類型: {ep.get('type', 'unknown')}"
            )

            body_params = ep.get("bodyParams", [])
            query_params = ep.get("queryParams", [])

            if body_params:
                print(f"   📦 Body 參數數量: {len(body_params)}")
                for param in body_params[:5]:  # 只顯示前 5 個
                    print(
                        f"      - {param['name']} ({param.get('data_type', 'unknown')}) - 來源: {param.get('source', 'unknown')}"
                    )
                if len(body_params) > 5:
                    print(f"      ... 還有 {len(body_params) - 5} 個參數")

            if query_params:
                print(f"   🔍 Query 參數數量: {len(query_params)}")
                for param in query_params[:3]:  # 只顯示前 3 個
                    print(
                        f"      - {param['name']} ({param.get('data_type', 'unknown')})"
                    )

        # 測試新功能檢查
        print(f"\n🧪 新功能測試:")

        # 檢查變數追蹤是否正常工作
        has_browser_fingerprint = any(
            param["name"] == "browser_fingerprint"
            for ep in endpoints
            for param in ep.get("bodyParams", [])
        )
        print(
            f"   ✅ 變數追蹤 (browser_fingerprint): {'通過' if has_browser_fingerprint else '失敗'}"
        )

        # 檢查動態建構是否正常工作
        has_timestamp = any(
            param["name"] == "timestamp"
            for ep in endpoints
            for param in ep.get("bodyParams", [])
        )
        print(f"   ✅ 動態建構 (Object.assign): {'通過' if has_timestamp else '失敗'}")

        # 檢查 spread operator 是否正常工作
        has_additional_field = any(
            param["name"] == "additional_field"
            for ep in endpoints
            for param in ep.get("bodyParams", [])
        )
        print(f"   ✅ Spread Operator: {'通過' if has_additional_field else '失敗'}")

        # 檢查智能合併是否正常工作
        # 應該有一個 merged 類型的端點，包含 form 和 javascript 的參數
        merged_endpoints = [ep for ep in endpoints if ep.get("type") == "merged"]
        has_merged_endpoint = len(merged_endpoints) >= 1

        # 檢查合併的端點是否同時包含 form 和 javascript 的參數
        merged_has_both_sources = False
        for ep in merged_endpoints:
            sources = set(param.get("source", "") for param in ep.get("bodyParams", []))
            if "form" in sources and "javascript" in sources:
                merged_has_both_sources = True
                break

        smart_merge_passed = has_merged_endpoint and merged_has_both_sources
        print(f"   ✅ 智能合併: {'通過' if smart_merge_passed else '失敗'}")
        print(f"      - 合併端點數量: {len(merged_endpoints)}")
        print(
            f"      - 包含 form + js 參數: {'是' if merged_has_both_sources else '否'}"
        )

        # 總體評估
        all_tests_passed = all(
            [
                has_browser_fingerprint,
                has_timestamp,
                has_additional_field,
                smart_merge_passed,
            ]
        )

        print(
            f"\n🎉 總體評估: {'全部通過！' if all_tests_passed else '部分功能需要改進。'}"
        )


if __name__ == "__main__":
    run_real_test()
