import json
import numpy as np
import torch
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)


class JsonDataset(Dataset):
    def __init__(self, samples, tokenizer, max_length=192):
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        encoding = self.tokenizer(
            item["text"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(item["label"], dtype=torch.float),
        }


def load_jsonl(path: str):
    samples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            text = data["text"]
            depth = data.get("depth", 0)
            if "| Depth:" not in text:
                text = f"{text} | Depth: {depth}"
            samples.append({"text": text, "label": float(data["label"])})
    return samples


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.clip(logits.squeeze(), 0.0, 1.0)
    mae = np.mean(np.abs(preds - labels))
    acc = np.mean((preds >= 0.5) == (labels >= 0.5))
    return {"mae": round(float(mae), 4), "acc": round(float(acc), 4)}


def train():
    model_input_path = "./hacker_model_final_v2"
    output_dir = "./hacker_model_final_v3_low_lr2"
    data_path = "datasets/merged_train.jsonl"

    tokenizer = AutoTokenizer.from_pretrained(model_input_path)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_input_path, num_labels=1
    )

    all_samples = load_jsonl(data_path)
    print(f"[+] 載入 {len(all_samples)} 筆訓練資料 from {data_path}")

    # 保持 shuffle 後的順序，前 90% 訓練，後 10% 評估
    train_size = int(0.9 * len(all_samples))
    train_dataset = JsonDataset(all_samples[:train_size], tokenizer)
    eval_dataset = JsonDataset(all_samples[train_size:], tokenizer)

    print(f"[+] Train: {len(train_dataset)}  Eval: {len(eval_dataset)}")

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=8,
        per_device_train_batch_size=64,
        per_device_eval_batch_size=128,
        fp16=True,
        # 從 v2 繼續微調：低 LR 避免遺忘，cosine 衰減防止末期震盪
        learning_rate=5e-5,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        weight_decay=0.01,
        logging_steps=100,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="mae",
        greater_is_better=False,
        save_total_limit=3,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics,
    )

    print("[*] 開始微調（v2 → v3，merged 53K，8 epochs，cosine LR 5e-6）...")
    trainer.train()

    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"[✓] 模型已存至 {output_dir}")


if __name__ == "__main__":
    train()
