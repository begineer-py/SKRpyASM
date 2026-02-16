import subprocess
import json
import os
from typing import Any, List


class JSJsonExtractor:
    def __init__(self, node_path: str = "node", timeout: int = 20):
        self.node_path = node_path
        self.timeout = timeout

    def execute(self, js_code: str) -> List[Any]:
        # 這次我們從 stdin 讀取 JS 代碼，避免參數過長的問題
        wrapper = """
const vm = require('vm');
const fs = require('fs');

// 1. 從標準輸入 (stdin) 讀取完整的 JS 程式碼
const targetJsCode = fs.readFileSync(0, 'utf-8');

// 2. 準備模擬環境
const sandbox = {
    console: console,
    setTimeout: setTimeout,
    setInterval: setInterval,
    Buffer: Buffer,
    process: { env: {} },
    window: {},
    document: {
        createElement: () => ({ style: {} }),
        getElementsByTagName: () => [],
        documentElement: {}
    },
    navigator: { userAgent: 'Mozilla/5.0 (Node.js AI Scanner)' },
    location: { href: '', host: '', pathname: '' },
    screen: {},
    Image: function() {},
    XMLHttpRequest: function() {},
    fetch: () => Promise.resolve()
};
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.top = sandbox;
sandbox.parent = sandbox;

const codeToRun = `
    (function() {
        const require = undefined; 
        try {
            ${targetJsCode}
        } catch (e) {
            // 執行期錯誤不中斷掃描
        }
        
        const results = [];
        const seen = new Set();
        
        function isInteresting(obj) {
            return obj !== null && typeof obj === 'object' && !Array.isArray(obj);
        }

        for (let key in this) {
            if (['window', 'document', 'navigator', 'console', 'sandbox', 'global', 'self', 'top', 'parent', 'process', 'Buffer'].includes(key)) continue;
            
            try {
                let val = this[key];
                if (isInteresting(val)) {
                    results.push({
                        path: key,
                        type: typeof val,
                        data: val
                    });
                }
            } catch(e) {}
        }
        return JSON.stringify(results);
    }).call(window);
`;

try {
    const script = new vm.Script(codeToRun);
    const result = script.runInNewContext(sandbox, { timeout: 10000 });
    process.stdout.write(result);
} catch (err) {
    process.stderr.write(err.message);
}
"""
        try:
            # 關鍵修改：使用 input=js_code 將資料透過 stdin 傳入，而不是 argv
            result = subprocess.run(
                [self.node_path, "-e", wrapper],
                input=js_code,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            if result.stderr and not result.stdout:
                # 如果有報錯且沒輸出，才視為失敗
                print(f"Node.js Debug Error: {result.stderr}")
                return []

            if not result.stdout:
                return []

            return json.loads(result.stdout)

        except subprocess.TimeoutExpired:
            print("JS 解析超時")
            return []
        except Exception as e:
            print(f"執行出錯: {e}")
            return []


if __name__ == "__main__":
    extractor = JSJsonExtractor()

    # 測試讀取本地檔案
    try:
        # 假設你的測試檔案路徑
        test_file = os.path.join(os.path.dirname(__file__), "test.js")
        if os.path.exists(test_file):
            with open(test_file, "r", encoding="utf-8") as f:
                js_content = f.read()

            results = extractor.execute(js_content)
            print(f"找到 {len(results)} 個物件：")
            for r in results:
                print(f" - [{r['path']}] ({r['type']})")
                print(r)
        else:
            print("找不到 test.js")
    except Exception as e:
        print(f"讀取測試檔失敗: {e}")
