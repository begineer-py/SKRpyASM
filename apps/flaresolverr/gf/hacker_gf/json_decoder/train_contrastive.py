import os
import json
import random
from datetime import datetime
import torch
from torch.utils.data import DataLoader
from sentence_transformers import SentenceTransformer, InputExample, losses
from transformers import AutoTokenizer


class TrainContrastive:
    def __init__(self, MODEL_PATH):
        self.model = SentenceTransformer(MODEL_PATH)
        self.high_risk_data_path = "datasets/high_risk_pool.jsonl"
        self.low_risk_data_path = "datasets/low_risk_pool.jsonl"
        self.output_path = f"./hacker_model_contrastive2"
        self.base_model_path = MODEL_PATH

    def load_data_with_depth(self, file_path):
        data = []
        if not os.path.exists(file_path):
            print(f"[!] 錯誤: 找不到文件 {file_path}")
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    text = obj["text"]
                    depth = obj.get("depth", 0)
                    # --- 關鍵修改：注入深度資訊 ---
                    if "| Depth:" not in text:
                        full_text = f"{text} | Depth: {depth}"
                    else:
                        full_text = text
                    data.append(full_text)
                except:
                    continue
        return data

    def start_training(self, epochs=3, batch_size=64):  # 4060 建議 64
        high_texts = self.load_data_with_depth(self.high_risk_data_path)
        low_texts = self.load_data_with_depth(self.low_risk_data_path)

        # 構造正負樣本 (邏輯與你之前相同)
        pos_pairs = []
        random.shuffle(high_texts)
        for i in range(0, len(high_texts) - 1, 2):
            pos_pairs.append(
                InputExample(texts=[high_texts[i], high_texts[i + 1]], label=1.0)
            )

        neg_pairs = []
        for _ in range(len(pos_pairs)):
            neg_pairs.append(
                InputExample(
                    texts=[random.choice(high_texts), random.choice(low_texts)],
                    label=0.0,
                )
            )

        train_examples = pos_pairs + neg_pairs
        random.shuffle(train_examples)

        train_dataloader = DataLoader(
            train_examples, shuffle=True, batch_size=batch_size
        )
        train_loss = losses.CosineSimilarityLoss(model=self.model)

        print(f"[*] 啟動對比學習 (含 Depth 資訊)。樣本數: {len(train_examples)}")
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=epochs,
            output_path=self.output_path,
            optimizer_params={"lr": 5e-5},
        )

        # 確保 Tokenizer 一併保存
        tokenizer = AutoTokenizer.from_pretrained(self.base_model_path)
        tokenizer.save_pretrained(self.output_path)
        print(f"[✓] 對比學習完成：{self.output_path}")


if __name__ == "__main__":
    # 使用你現有的基礎模型
    trainer = TrainContrastive("sentence-transformers/all-MiniLM-L6-v2")
    trainer.start_training()
