import json
import os
import torch
import chompjs
from typing import List, Dict, Any, Tuple, Optional
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class HackerScanner:
    def __init__(self, model_path: str, device: str = "cuda"):
        # 1. 初始化 AI 模型
        print(f"[*] 正在載入 AI 腦袋: {model_path} ...")
        self.device = device if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path).to(
            self.device
        )
        self.model.eval()

        # 2. 掃描器狀態
        self.path_map: Dict[str, Dict[str, Any]] = {}
        self.depth_map: Dict[int, List[str]] = {}
        self.max_depth = 0

    def _get_struct_type(self, node: Any) -> str:
        """判定是 Leaf (值) 還是 Branch (物件/陣列)"""
        return "Branch" if isinstance(node, (dict, list)) else "Leaf"

    def _walk(self, node: Any, depth: int, path: str, key_name: str):
        """遞迴遍歷並建立 AI 分析需要的元數據"""
        self.max_depth = max(self.max_depth, depth)

        struct_type = self._get_struct_type(node)
        val_str = (
            json.dumps(node, ensure_ascii=False) if struct_type == "Leaf" else "{...}"
        )

        # 儲存節點資訊
        entry = {
            "path": path,
            "key": key_name,
            "struct": struct_type,
            "val": val_str,
            "depth": depth,
            "raw_value": node,
        }
        self.path_map[path] = entry

        if depth not in self.depth_map:
            self.depth_map[depth] = []
        self.depth_map[depth].append(path)

        # 繼續往下鑽
        if isinstance(node, dict):
            for k, v in node.items():
                self._walk(v, depth + 1, f"{path}.{k}", k)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                self._walk(item, depth + 1, f"{path}[{i}]", f"[{i}]")

    def parse_js_content(self, js_code: str):
        """傳入 JS 字串，噴出裡面所有的 Object 並解析"""
        print("[*] 正在從 JS 中提取 Object...")
        try:
            # 使用 chompjs 抓取第一個大物件
            data = chompjs.parse_js_object(js_code)
            self.path_map = {}
            self.depth_map = {}
            self._walk(data, 0, "root", "root")
            print(f"[✓] 解析完成，總共發現 {len(self.path_map)} 個節點")
        except Exception as e:
            print(f"[!] Chompjs 解析失敗: {e}")

    def get_ai_score(self, node: Dict) -> float:
        """把節點丟進模型算分"""
        # 嚴格符合你 train.py 的格式
        text_body = f"Path: {node['path']} | Key: {node['key']} | Struct: {node['struct']} | Val: {node['val']}"
        full_text = f"{text_body} | Depth: {node['depth']}"

        inputs = self.tokenizer(
            full_text,
            return_tensors="pt",
            truncation=True,
            max_length=128,
            padding="max_length",
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            score = outputs.logits.item()

        return round(float(torch.clamp(torch.tensor(score), 0.0, 1.0)), 4)

    def run_scan(self, threshold: float = 0.5):
        """執行全面掃描並印出高風險節點"""
        print(f"{'RISK':<8} | {'DEPTH':<5} | {'KEY':<15} | {'VALUE'}")
        print("=" * 80)

        results = []
        for path, node in self.path_map.items():
            # 我們通常只對 Leaf (真正的資料) 噴分數，Branch 通常是結構
            if node["struct"] == "Leaf":
                score = self.get_ai_score(node)
                if score >= threshold:
                    results.append((score, node))

        # 按分數排序，高的在前
        results.sort(key=lambda x: x[0], reverse=True)

        for score, node in results:
            score_str = f"{score:.4f}"
            if score > 0.8:
                risk_label = f"\033[91m[CRIT] {score_str}\033[0m"
            elif score > 0.5:
                risk_label = f"\033[93m[HIGH] {score_str}\033[0m"
            else:
                risk_label = f"\033[92m[SAFE] {score_str}\033[0m"

            val_disp = (
                str(node["val"])[:50] + "..."
                if len(str(node["val"])) > 50
                else node["val"]
            )
            print(f"{risk_label} | {node['depth']:<5} | {node['key']:<15} | {val_disp}")

    def scan_to_json(self, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        執行全面掃描並回傳 JSON 格式的 List
        """
        json_results = []

        # 遍歷所有節點，計算分數
        for path, node in self.path_map.items():
            # 針對 Leaf 節點進行 AI 評分 (通常機密都在 Leaf)
            if node["struct"] == "Leaf":
                score = self.get_ai_score(node)

                # 如果分數超過門檻才收進來 (設為 0.0 代表全收)
                if score >= threshold:
                    # 格式化成你要的樣子
                    result_item = {
                        "value": node["val"].strip('"'),  # 去掉 JSON 雙引號
                        "where": node["path"],
                        "key": node["key"],
                        "score": score,
                        "depth": node["depth"],
                    }
                    json_results.append(result_item)

        # 依照分數從高到低排，把最危險的排前面
        json_results.sort(key=lambda x: x["score"], reverse=True)
        return json_results


# === 測試執行部分 ===
if __name__ == "__main__":
    # ... 前面的初始化 code 照舊 ...
    MODEL_PATH = "/home/hacker/Desktop/share/C2_Django_AI_git/apps/flaresolverr/gf/hacker_gf/json_decoder/hacker_model_final_v3_low_lr2"

    example_js = """
    const config = {
        api_key: "AKIA-EXAMPLE-FAKE-KEY-FOR-TEST",
        debug: true,
        db_password: "admin_password_123",
        moduleData: [
            { id: 1 },
            { components: [ { i18n: { messages: { "zh-cn": { fileUpload: { errorMessage2: "因无障碍要求请允许odt,ods,odp,pdf类型之档案" } } } } } ] }
        ]
    };
    """

    scanner = HackerScanner(MODEL_PATH)
    scanner.parse_js_content(example_js)

    # 執行掃描並取得 JSON
    final_output = scanner.scan_to_json(threshold=0.1)

    # 噴出 JSON 字串
    print(json.dumps(final_output, indent=2, ensure_ascii=False))
