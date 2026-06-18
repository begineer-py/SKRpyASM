import os
import json
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
import sys
from pathlib import Path

from openai import OpenAI, APIError, RateLimitError

# ------------------------------------------------------------------ #
# API 設定
# ------------------------------------------------------------------ #

_API_KEY = os.environ.get(
    "yunxin"
)
_BASE_URL = "https://api.yuhuanstudio.com/v1"
_MODEL = "tokenrouter/deepseek/deepseek-v4-flash"

# ------------------------------------------------------------------ #
# 通用格式規範（所有主題共用）
# ------------------------------------------------------------------ #

_FORMAT_PROMPT = """\
你是一位資深滲透測試工程師兼 ML 訓練資料品質專家。
你的任務是生成 JSON 節點安全評分訓練資料。

== 資料格式（固定，不可變更） ==
每筆資料是一個 JSON 物件：
{"text": "Path: {path} | Key: {key} | Struct: Leaf | Val: {value}", "label": 0.0~1.0, "depth": N}

== 輸出規範 ==
只輸出 JSON 物件，包含 results 陣列：
{"results": [{"text": "...", "label": 0.0, "depth": N}, ...]}
不要加任何說明文字、markdown、或程式碼區塊。
"""


# ================================================================== #
# 主題載入器
# ================================================================== #

class TopicLoader:
    """從 prompts/ 目錄載入所有主題 JSON 檔案"""

    _PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
    _cache: Optional[List[dict]] = None

    @classmethod
    def list_topics(cls) -> List[dict]:
        """回傳所有主題（含 topic, description, category, label_range）"""
        return [
            {
                "topic": t["topic"],
                "description": t["description"],
                "category": t["category"],
                "label_range": t["label_range"],
            }
            for t in cls._load_all()
        ]

    @classmethod
    def get_topic(cls, topic_name: str) -> Optional[dict]:
        """依 topic name 取得單一主題"""
        for t in cls._load_all():
            if t["topic"] == topic_name:
                return t
        return None

    @classmethod
    def get_by_category(cls, category: str) -> List[dict]:
        """依 category 過濾：hard_positive / hard_negative / ambiguous"""
        return [t for t in cls._load_all() if t["category"] == category]

    @classmethod
    def build_system_prompt(cls, topic: dict) -> str:
        """根據主題 JSON 內容組裝 system prompt"""
        # 主題特定指引
        lines = [f"== 本批次主題：{topic['topic']} =="]
        lines.append(f"類別：{topic['category']}（label {topic['label_range'][0]}~{topic['label_range'][1]}）")
        lines.append(f"說明：{topic['description']}")
        lines.append("")
        lines.append("== 生成指引 ==")
        lines.append(topic["generation_guidelines"])

        # 附加範例（最多 3 筆）
        examples = topic.get("examples", [])
        if examples:
            lines.append("")
            lines.append("== 參考範例 ==")
            for ex in examples[:3]:
                lines.append(json.dumps(ex, ensure_ascii=False))

        lines.append("")
        lines.append("== 多樣性要求 ==")
        lines.append("- 每批 20 筆要包含不同路徑深度（1~10）")
        lines.append("- 避免重複的 path 模式或 cloud provider")
        lines.append("- label 分布要合理，不要全部擠在範圍邊界")
        lines.append("- path 要有真實感：root.app.config.cloud.aws 而非 root.a.b")

        return "\n".join(lines)

    @classmethod
    def _load_all(cls) -> List[dict]:
        if cls._cache is not None:
            return cls._cache

        if not cls._PROMPTS_DIR.exists():
            print(f"[!] prompts 目錄不存在：{cls._PROMPTS_DIR}")
            cls._cache = []
            return cls._cache

        topics = []
        for fpath in sorted(cls._PROMPTS_DIR.glob("*.json")):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if "topic" in data and "generation_guidelines" in data:
                    topics.append(data)
                else:
                    print(f"[!] 跳過 {fpath.name}：缺少 topic 或 generation_guidelines")
            except json.JSONDecodeError:
                print(f"[!] 跳過 {fpath.name}：JSON 解析失敗")

        cls._cache = topics
        print(f"[+] 載入 {len(topics)} 個主題：{', '.join(t['topic'] for t in topics)}")
        return topics


# ================================================================== #
# 知識蒸餾器
# ================================================================== #

class DeepSeekDataDistiller:
    """
    知識蒸餾器：從 prompts/*.json 載入多主題，
    每個 worker 隨機挑選主題，生成多樣化訓練資料。
    """

    def __init__(
        self,
        output_file: str = "datasets/deepseek_distilled.jsonl",
        progress_file: str = "progress_deepseek.txt",
        batch_size: int = 20,
        target_total: int = 50000,
        num_clones: int = 8,
        topic_filter: Optional[List[str]] = None,
    ):
        self.output_file = output_file
        self.progress_file = progress_file
        self.batch_size = batch_size
        self.target_total = target_total
        self.num_clones = num_clones
        self.lock = threading.Lock()
        self.current_count = self._load_progress()

        self.client = OpenAI(api_key=_API_KEY, base_url=_BASE_URL)

        # 載入主題
        all_topics = TopicLoader._load_all()
        if not all_topics:
            print("[!] 沒有任何主題可載入，退出。")
            sys.exit(1)

        if topic_filter:
            self.topics = [t for t in all_topics if t["topic"] in topic_filter]
            if not self.topics:
                print(f"[!] 過濾後沒有任何主題 ({topic_filter})，退出。")
                sys.exit(1)
        else:
            self.topics = all_topics

        print(f"[+] 使用 {len(self.topics)} 個主題：{', '.join(t['topic'] for t in self.topics)}")

        # 確保 output 目錄存在
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    # ------------------------------------------------------------------ #
    # 進度管理
    # ------------------------------------------------------------------ #

    def _load_progress(self) -> int:
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    return int(f.read().strip())
            except Exception:
                return 0
        return 0

    def _save_progress(self):
        with open(self.progress_file, "w", encoding="utf-8") as f:
            f.write(str(self.current_count))

    # ------------------------------------------------------------------ #
    # API 呼叫
    # ------------------------------------------------------------------ #

    def _call_api(self, system_prompt: str, user_prompt: str) -> List[dict]:
        """呼叫 DeepSeek API，回傳解析後的 results list"""
        response = self.client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.9,
            timeout=120,
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        results = data if isinstance(data, list) else data.get("results", [])
        return results

    # ------------------------------------------------------------------ #
    # 資料驗證與寫入
    # ------------------------------------------------------------------ #

    def _validate_item(self, item: dict) -> bool:
        if "text" not in item or "label" not in item:
            return False
        label = item["label"]
        if not isinstance(label, (int, float)):
            return False
        if not (0.0 <= float(label) <= 1.0):
            return False
        if "Path:" not in item["text"] or "Key:" not in item["text"]:
            return False
        return True

    def _write_results(self, results: List[dict]) -> int:
        written = 0
        with self.lock:
            with open(self.output_file, "a", encoding="utf-8") as f:
                for item in results:
                    if self._validate_item(item):
                        f.write(json.dumps(item, ensure_ascii=False) + "\n")
                        written += 1
            self.current_count += written
            self._save_progress()
        return written

    # ------------------------------------------------------------------ #
    # 影分身 Worker
    # ------------------------------------------------------------------ #

    def _clone_worker(self, clone_id: int):
        print(f"[*] 影分身 #{clone_id} 啟動！")

        while True:
            with self.lock:
                if self.current_count >= self.target_total:
                    break
                current_idx = self.current_count

            # 隨機選一個主題（權重：HP:HN:AMB = 40:35:25）
            category_weights = {
                "hard_positive": 40,
                "hard_negative": 35,
                "ambiguous": 25,
            }
            cat_weights = [category_weights[t["category"]] for t in self.topics]
            chosen = random.choices(self.topics, weights=cat_weights, k=1)[0]

            # 組裝 system prompt
            system_prompt = _FORMAT_PROMPT + "\n" + TopicLoader.build_system_prompt(chosen)

            seed = random.randint(1, 999999)
            user_prompt = (
                f"請生成 {self.batch_size} 筆新的訓練資料。\n"
                f"主題：{chosen['topic']}（{chosen['category']}）\n"
                f"隨機種子提示：{seed}。起始索引參考：{current_idx}。\n"
                f"確保 path 和 val 都是全新生成，不要重複已有樣本。"
            )

            try:
                results = self._call_api(system_prompt, user_prompt)
                added = self._write_results(results)
                if added > 0:
                    print(
                        f"[Clone #{clone_id}] +{added} 筆 [{chosen['topic']}] | "
                        f"總計: {self.current_count}/{self.target_total}"
                    )
                else:
                    print(f"[Clone #{clone_id}] '{chosen['topic']}' 解析結果為空")

            except RateLimitError:
                print(f"[Clone #{clone_id}] 速率限制，等待 30s...")
                time.sleep(30)
                continue
            except APIError as e:
                print(f"[Clone #{clone_id}] API 錯誤: {e}，等待 10s...")
                time.sleep(10)
                continue
            except json.JSONDecodeError:
                print(f"[Clone #{clone_id}] JSON 解析失敗")
            except Exception as e:
                print(f"[Clone #{clone_id}] 未知異常: {e}")
                time.sleep(5)

            time.sleep(random.uniform(1.5, 4.0))

        print(f"[Clone #{clone_id}] 任務完成，退出。")

    # ------------------------------------------------------------------ #
    # 主入口
    # ------------------------------------------------------------------ #

    def run(self):
        print(
            f"--- [DeepSeek 知識蒸餾啟動] ---\n"
            f"目標: {self.target_total} 筆 | 影分身: {self.num_clones} 個 | "
            f"已有進度: {self.current_count} 筆\n"
            f"輸出: {self.output_file}\n"
            f"模型: {_MODEL}\n"
        )

        if self.current_count >= self.target_total:
            print("[!] 已達到目標數量，無需重新生成。")
            return

        with ThreadPoolExecutor(max_workers=self.num_clones) as executor:
            for i in range(self.num_clones):
                executor.submit(self._clone_worker, i + 1)

        print(f"\n--- [蒸餾完成] 總計生成 {self.current_count} 筆資料 ---")


# ================================================================== #
# 合併工具
# ================================================================== #

def merge_datasets(
    *inputs: str,
    output: str = "datasets/merged_train.jsonl",
):
    """讀取多個 JSONL 檔案，shuffle 後輸出合併結果"""
    all_lines = []
    for path in inputs:
        if not os.path.exists(path):
            print(f"[!] 找不到 {path}，略過")
            continue
        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        print(f"[+] {path} → {len(lines)} 筆")
        all_lines.extend(lines)

    random.shuffle(all_lines)
    with open(output, "w", encoding="utf-8") as f:
        for line in all_lines:
            f.write(line + "\n")
    print(f"[✓] 合併完成：{len(all_lines)} 筆 → {output}")


# ================================================================== #
# CLI
# ================================================================== #

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="DeepSeek 知識蒸餾資料生成器")
    parser.add_argument("--target", type=int, default=50000, help="目標生成筆數（預設 50000）")
    parser.add_argument("--clones", type=int, default=20, help="並發影分身數量（預設 20）")
    parser.add_argument("--batch", type=int, default=25, help="每批次生成筆數（預設 25）")
    parser.add_argument("--output", type=str, default="datasets/deepseek_distilled.jsonl", help="輸出檔案")
    parser.add_argument("--topics", type=str, nargs="*", default=None,
                        help="指定主題（可多個），預設全部。範例：--topics cloud-credentials sensitive-tokens")
    parser.add_argument("--list-topics", action="store_true", help="列出所有可用主題")
    args = parser.parse_args()

    if args.list_topics:
        print("可用的蒸餾主題：")
        for t in TopicLoader.list_topics():
            lr = t["label_range"]
            print(f"  {t['topic']:30s} [{t['category']:15s}] {lr[0]}~{lr[1]}  {t['description']}")
        sys.exit(0)

    distiller = DeepSeekDataDistiller(
        output_file=args.output,
        target_total=args.target,
        num_clones=args.clones,
        batch_size=args.batch,
        topic_filter=args.topics,
    )
    distiller.run()
