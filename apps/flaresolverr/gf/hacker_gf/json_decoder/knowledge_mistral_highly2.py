import os
import json
import time
import random
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
import sys


# Mistral 請求構造
def _build_payload(final_prompt: str) -> dict:
    return {
        "messages": [{"role": "user", "content": final_prompt}],
        "model": "mistral-small-2603",
        "response_format": {"type": "json_object"},
    }


class CyberDataGenerator:
    def __init__(
        self,
        output_file: str = "datasets/highly_data.jsonl",
        progress_file: str = "progress_count2.txt",
        nyaproxy_url: str = "http://localhost:8502/api/mistral_ai/chat/completions",
        batch_size: int = 20,
        target_total: int = 5000,
        num_clones: int = 10,  # 影分身數量
    ):
        self.output_file = output_file
        self.progress_file = progress_file
        self.nyaproxy_url = nyaproxy_url
        self.batch_size = batch_size
        self.target_total = target_total
        self.num_clones = num_clones

        # 執行緒鎖：確保多個影分身寫入文件時不會發生衝突
        self.lock = threading.Lock()

        # 1. 載入提示詞
        prompt_path = os.path.join(
            os.path.dirname(__file__), "prompt", "highly_data.txt"
        )
        self.base_prompt = self._load_prompt_content(prompt_path)

        # 2. 載入進度
        self.current_count = self._load_progress()

    def _load_prompt_content(self, path: str) -> str:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        print(f"[!] 錯誤: 找不到 Prompt 文件 {path}")
        sys.exit(1)

    def _load_progress(self) -> int:
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    return int(f.read().strip())
            except:
                return 0
        return 0

    def _save_progress(self):
        """保存當前總進度"""
        with open(self.progress_file, "w", encoding="utf-8") as f:
            f.write(str(self.current_count))

    def _process_and_write(self, raw_res: str) -> int:
        """解析並安全寫入數據"""
        try:
            outer = json.loads(raw_res)
            inner_text = outer["choices"][0]["message"]["content"].strip()
            data = json.loads(inner_text)
            results = data if isinstance(data, list) else data.get("results", [])

            written_count = 0
            # 寫入時加鎖，防止多線程寫亂文件
            with self.lock:
                with open(self.output_file, "a", encoding="utf-8") as f:
                    for item in results:
                        if "text" in item and "label" in item:
                            f.write(json.dumps(item, ensure_ascii=False) + "\n")
                            written_count += 1

                # 更新全局計數器
                self.current_count += written_count
                self._save_progress()

            return written_count
        except Exception as e:
            print(f"  [!] 解析失敗: {e}")
            return 0

    def _clone_worker(self, clone_id: int):
        """影分身核心邏輯"""
        print(f"[*] 影分身 #{clone_id} 啟動！")

        while True:
            # 檢查全局進度是否已達標
            with self.lock:
                if self.current_count >= self.target_total:
                    break
                current_idx = self.current_count

            # 加入隨機擾動，讓每個分身生成的內容更具多樣性
            seed_hint = random.randint(1, 100000)
            gen_prompt = (
                f"{self.base_prompt}\n\n"
                f"Please generate {self.batch_size} new and diverse samples. "
                f"Random Seed Hint: {seed_hint}. Start index reference: {current_idx}."
            )

            try:
                res = requests.post(
                    self.nyaproxy_url, json=_build_payload(gen_prompt), timeout=150
                )

                if res.status_code == 200:
                    added = self._process_and_write(res.text)
                    if added > 0:
                        print(
                            f"[Clone #{clone_id}] 成功產出 {added} 條 | 全局總計: {self.current_count}/{self.target_total}"
                        )
                    else:
                        print(f"[Clone #{clone_id}] 未能提取數據。")
                else:
                    print(f"[Clone #{clone_id}] API 報錯: {res.status_code}")
                    time.sleep(10)

            except Exception as e:
                print(f"[Clone #{clone_id}] 異常: {e}")
                time.sleep(5)

            # 每個分身獨立休眠，錯開請求峰值
            time.sleep(random.uniform(1.0, 3.0))

    def run(self):
        print(
            f"--- [影分身術啟動！目標: {self.target_total}, 分身數: {self.num_clones}] ---"
        )

        # 使用線程池管理影分身
        with ThreadPoolExecutor(max_workers=self.num_clones) as executor:
            for i in range(self.num_clones):
                executor.submit(self._clone_worker, i + 1)

        print(f"\n--- [任務完成：影分身回收，總計生成 {self.current_count} 條數據] ---")


if __name__ == "__main__":
    # 配置：10 個影分身同時幹活，產出速度瞬間 10 倍
    generator = CyberDataGenerator(target_total=10000, batch_size=20, num_clones=10)
    generator.run()
