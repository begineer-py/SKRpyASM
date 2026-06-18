import torch
from sentence_transformers import SentenceTransformer, util
import json
import time


class LeafNodeFilter:
    def __init__(self, model_name="./all-MiniLM-L6-v2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[*] Loading model {model_name} on {self.device}...")
        self.model = SentenceTransformer(model_name, device=self.device)

        # 這裡的錨點在微調後可以刪除，現在保留用於對比
        self.security_anchors = [
            "security credential password secret key token auth permission database id"
        ]
        self.noise_anchors = [
            "ui style color theme calendar date time layout translation"
        ]

        self.anchor_embeddings = self.model.encode(
            self.security_anchors, convert_to_tensor=True
        )
        self.noise_embeddings = self.model.encode(
            self.noise_anchors, convert_to_tensor=True
        )

    def process_batch(self, nodes):
        start_time = time.time()
        texts = []
        for node in nodes:
            # --- 關鍵修改：適配訓練數據結構 ---
            # 訓練集格式: "Path: {path} | Key: {key} | Struct: {struct} | Val: {val}"
            path = node.get("where", node.get("path", "unknown"))
            key = node.get("key", "unknown")
            struct = node.get("struct", "Leaf")  # 默認為 Leaf
            val = node.get("value", node.get("val", "null"))

            # 構造與訓練數據完全一致的 Text
            formatted_text = (
                f"Path: {path} | Key: {key} | Struct: {struct} | Val: {val}"
            )
            texts.append(formatted_text)

        node_embeddings = self.model.encode(
            texts, convert_to_tensor=True, show_progress_bar=False
        )

        # 目前仍使用相似度邏輯
        security_scores = util.cos_sim(node_embeddings, self.anchor_embeddings)
        noise_scores = util.cos_sim(node_embeddings, self.noise_embeddings)
        max_sec_scores, _ = torch.max(security_scores, dim=1)
        max_noise_scores, _ = torch.max(noise_scores, dim=1)

        results = []
        for i, node in enumerate(nodes):
            # 模擬分數
            final_score = max_sec_scores[i].item() - (max_noise_scores[i].item() * 0.5)
            results.append(
                {
                    "score": round(final_score, 4),
                    "key": node.get("key"),
                    "value": node.get("value", node.get("val")),
                    "formatted_text": texts[i],  # 顯示構造後的文本
                }
            )

        print(f"[*] Processed {len(nodes)} nodes in {time.time() - start_time:.4f}s")
        return results


# --- 更新測試數據結構 ---

data_high_value = {
    "keys": [
        {
            "key": "parent[1]",
            "value": "63e4640a409dddb1dea464c7",
            "where": "root.allPage[49].parent[1]",
            "struct": "Leaf",
        },
        {
            "key": "permission",
            "value": "admin_denied",
            "where": "root.user.auth.permission",
            "struct": "Leaf",
        },
    ]
}

data_low_value = {
    "keys": [
        {
            "key": "tag",
            "value": "false",
            "where": "root.allPage[49].advertisingLink.tag",
            "struct": "Leaf",
        },
        {
            "key": "color",
            "value": "#FFFFFF",
            "where": "root.theme.background",
            "struct": "Leaf",
        },
    ]
}

if __name__ == "__main__":
    filter_engine = LeafNodeFilter()
    # 測試高價值
    print("\n--- New Structure Test (High) ---")
    results = filter_engine.process_batch(data_high_value["keys"])
    for r in results:
        print(f"[{r['score']}] -> {r['formatted_text']}")

    # 測試低價值
    print("\n--- New Structure Test (Low) ---")
    results = filter_engine.process_batch(data_low_value["keys"])
    for r in results:
        print(f"[{r['score']}] -> {r['formatted_text']}")
