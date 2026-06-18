import time
import random
import requests
import os
import json
from typing import List, Dict
from jsonbuster import JsonInspector


class CyberDataFactory:
    def __init__(
        self,
        input_file: str = "raw_assets/target.json",
        output_file: str = "datasets/cyber_train_data.jsonl",
        progress_file: str = "progress_distill.json",
        nyaproxy_url: str = "http://localhost:8502/api/gemini_json_ai/",
        batch_size: int = 30,
    ):
        self.output_file = output_file
        self.progress_file = progress_file
        self.nyaproxy_url = nyaproxy_url
        self.batch_size = batch_size

        # 1. 初始化 Inspector
        self.inspector = JsonInspector(input_file)

        # 2. 載入 Prompt (修正點：讀取文件內容而非路徑)
        prompt_path = os.path.join(
            os.path.dirname(__file__), "prompt", "system_prompt_gemini.txt"
        )
        self.base_prompt = self._load_prompt_content(prompt_path)

        # 3. 讀取進度
        self.progress = self._load_progress()

    def _load_prompt_content(self, path: str) -> str:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                print(f"[*] 成功載入 System Prompt ({len(content)} bytes)")
                return content
        print(f"[!] 警告: 找不到 Prompt 文件 {path}，使用默認指令")
        return "You are a cyber security expert. Score these nodes 0-100 based on ASM value."

    def _load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, "r") as f:
                try:
                    return json.load(f)
                except:
                    pass
        return {"depth": self.inspector.max_depth, "index": 0}

    def _save_progress(self, depth: int, index: int):
        with open(self.progress_file, "w") as f:
            json.dump({"depth": depth, "index": index}, f)

    def _create_payload(self, batch_nodes: List[Dict]) -> Dict:
        payload_items = {}
        for i, node in enumerate(batch_nodes):
            son_keys, son_count = node.get("key_son", [[], 0])
            val = node.get("value")

            if isinstance(val, (dict, list)):
                val_display = f"<{type(val).__name__} with {son_count} children, subtree_h={node.get('subtree_height', 0)}>"
            else:
                val_display = str(val)[:500]

            payload_items[str(i)] = {
                "key": node.get("key"),
                "value": val_display,
                "where": node.get("where"),
                "key_son": son_keys,  # 傳給 AI 參考子結構
                "subtree_height": node.get("subtree_height", 0),
            }
        return payload_items

    def _process_and_write(self, raw_res: str, batch_nodes: List[Dict]):
        try:
            outer = json.loads(raw_res)
            inner_text = outer["candidates"][0]["content"]["parts"][0]["text"]

            # 清理 Markdown (預防萬一)
            inner_text = inner_text.strip()
            if inner_text.startswith("```"):
                inner_text = inner_text.split("\n", 1)[1].rsplit("\n", 1)[0]

            data = json.loads(inner_text)

            # --- 修正解析邏輯：兼容 List 和 Dict 格式 ---
            results = []
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict):
                results = data.get("results", [])

            written_count = 0
            with open(self.output_file, "a", encoding="utf-8") as f:
                for item in results:
                    # 兼容 AI 回傳不同的 key 名稱 (id, ID, score, asm_score)
                    try:
                        raw_id = item.get("id", item.get("ID"))
                        if raw_id is None:
                            continue
                        idx = int(raw_id)

                        score = item.get("score", item.get("asm_score", 0))
                    except (ValueError, TypeError):
                        continue

                    if 0 <= idx < len(batch_nodes):
                        node = batch_nodes[idx]
                        _, son_count = node.get("key_son", [[], 0])
                        h = node.get("subtree_height", 0)

                        struct_str = (
                            f"Branch[w={son_count}, h={h}]" if son_count > 0 else "Leaf"
                        )

                        raw_val = node.get("value")
                        if isinstance(raw_val, (dict, list)):
                            val_str = f"ComplexStructure({son_count} keys)"
                        else:
                            val_str = json.dumps(raw_val, ensure_ascii=False)

                        train_text = (
                            f"Path: {node['where']} | "
                            f"Key: {node['key']} | "
                            f"Struct: {struct_str} | "
                            f"Val: {val_str}"
                        )

                        entry = {
                            "text": train_text,
                            "label": float(score) / 100.0,
                            "depth": node.get("depth", 0),
                        }
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        written_count += 1
            return written_count
        except Exception as e:
            print(f"[!] 解析失敗: {e}")
            # print(f"[DEBUG] Raw Inner: {inner_text[:200]}") # 除錯用
            return 0

    def run(self):
        curr_d = self.progress["depth"]
        curr_idx = self.progress["index"]

        for d in range(curr_d, -1, -1):
            layer_data = self.inspector.get_by_depth(d)
            all_keys = layer_data["keys"]
            total = layer_data["total_at_layer"]

            start_i = curr_idx if d == curr_d else 0
            print(
                f"\n[*] 處理深度 Depth {d} ({total} nodes), 從 Index {start_i} 開始..."
            )

            for i in range(start_i, total, self.batch_size):
                batch = all_keys[i : i + self.batch_size]
                payload = self._create_payload(batch)

                # 發送請求
                full_prompt = f"{self.base_prompt}\n\nData to Triage:\n{json.dumps(payload, ensure_ascii=False)}"
                api_payload = {
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "temperature": 0.2,
                    },
                }

                try:
                    res = requests.post(
                        self.nyaproxy_url, json=api_payload, timeout=120
                    )
                    if res.status_code == 200:
                        count = self._process_and_write(res.text, batch)
                        print(
                            f"  [✓] Batch {i}~{i+len(batch)} 成功標記並寫入 {count} 條數據"
                        )
                        self._save_progress(d, i + self.batch_size)
                    else:
                        print(f"  [!] API 錯誤: {res.status_code}")
                except Exception as e:
                    print(f"  [!] 請求異常: {e}")

                time.sleep(random.uniform(1.0, 2.0))

            curr_idx = 0  # 換層後重置

        print("\n--- 任務完成 ---")


if __name__ == "__main__":
    factory = CyberDataFactory(input_file="target.json", batch_size=30)
    factory.run()
