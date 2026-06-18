import os
import json
import random
from datetime import datetime

import torch
from torch.utils.data import DataLoader
from sentence_transformers import SentenceTransformer, InputExample, losses, evaluation
from transformers import AutoTokenizer


class train_contrastive:
    def __init__(self, MODEL_PATH):
        # 1. 初始化模型與路徑
        self.model = SentenceTransformer(MODEL_PATH)
        # 修正副檔名為 .jsonl (根據你之前的 wc -l 結果)
        self.high_risk_data_path = os.path.join(
            os.path.dirname(__file__), "datasets", "high_risk_pool.jsonl"
        )
        self.low_risk_data_path = os.path.join(
            os.path.dirname(__file__), "datasets", "low_risk_pool.jsonl"
        )
        self.output_path = os.path.join(
            os.path.dirname(__file__),
            f"hacker_model_contrastive_{datetime.now().strftime('%m%d_%H%M')}",
        )
        self.base_model_path = MODEL_PATH

    def load_data(self, file_path):
        data = []
        if not os.path.exists(file_path):
            print(f"[!] 錯誤: 找不到文件 {file_path}")
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data.append(json.loads(line)["text"])
                except Exception as e:
                    continue
        return data

    def pair_positive(self, high_data):
        """
        構造正樣本對 (High vs High) -> Label: 1.0
        讓模型學會將不同類型的 Payload (如 SQLi 與 XSS) 識別為「同屬威脅」
        """
        examples = []
        count = len(high_data)
        print(f"[*] 正在構造正樣本對... 預計數量: {count}")

        # 隨機打亂進行兩兩配對
        random.shuffle(high_data)
        for i in range(0, count - 1, 2):
            examples.append(
                InputExample(texts=[high_data[i], high_data[i + 1]], label=1.0)
            )

        # 額外隨機抽樣補充，確保特徵覆蓋廣度
        for _ in range(count // 2):
            s1, s2 = random.sample(high_data, 2)
            examples.append(InputExample(texts=[s1, s2], label=1.0))

        return examples

    def pair_negative(self, high_data, low_data):
        """
        構造負樣本對 (High vs Low) -> Label: 0.0
        讓模型學會區分惡意 Payload 與正常的 JSON 結構或業務路徑
        """
        examples = []
        # 為了保持數據平衡，負樣本對數量與正樣本對相當
        count = len(high_data)
        print(f"[*] 正在構造負樣本對... 預計數量: {count}")

        for _ in range(count):
            h_sample = random.choice(high_data)
            l_sample = random.choice(low_data)
            examples.append(InputExample(texts=[h_sample, l_sample], label=0.0))

        return examples

    def start_training(self, epochs=3, batch_size=48):
        # A. 加載數據
        high_texts = self.load_data(self.high_risk_data_path)
        low_texts = self.load_data(self.low_risk_data_path)

        if not high_texts or not low_texts:
            print("[!] 數據加載失敗，終止訓練。")
            return

        # B. 構造全量訓練集
        pos_pairs = self.pair_positive(high_texts)
        neg_pairs = self.pair_negative(high_texts, low_texts)
        train_examples = pos_pairs + neg_pairs
        random.shuffle(train_examples)

        # C. 準備 DataLoader 與 Loss
        train_dataloader = DataLoader(
            train_examples, shuffle=True, batch_size=batch_size
        )
        # 使用 CosineSimilarityLoss 作為對比學習的核心
        train_loss = losses.CosineSimilarityLoss(model=self.model)

        # D. 訓練執行
        print(
            f"[*] 啟動對比學習。總樣本對: {len(train_examples)} | 輸出路徑: {self.output_path}"
        )

        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=epochs,
            warmup_steps=int(len(train_dataloader) * 0.1),
            output_path=self.output_path,
            show_progress_bar=True,
            optimizer_params={"lr": 2e-5},  # 低學習率微調
        )

        # E. 保存 Tokenizer (SentenceTransformer .save 不一定會完整保存 tokenizer 配置)
        tokenizer = AutoTokenizer.from_pretrained(self.base_model_path)
        tokenizer.save_pretrained(self.output_path)

        print(f"[✓] 訓練完成！強化版模型已存儲。")


if __name__ == "__main__":
    # 指向你之前全參數微調過的路徑
    BASE_MODEL = "./hacker_model_final"

    trainer = train_contrastive(BASE_MODEL)
    # 啟動訓練，4060 建議 batch_size 設為 48~64
    trainer.start_training(epochs=3, batch_size=32)
