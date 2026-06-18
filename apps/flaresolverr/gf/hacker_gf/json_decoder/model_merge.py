"""
model_merge.py — 模型融合工具

支援三種融合策略：
  linear   : 線性加權平均（所有層同樣 alpha）
  slerp    : 球面線性插值（保留參數空間方向，常用於語言模型融合）
  task_arith: Task Arithmetic（v3 − v2 的 delta 加回 v2，放大 v3 學到的新知識）

用法：
  python model_merge.py                          # 預設 slerp α=0.5
  python model_merge.py --method linear --alpha 0.6
  python model_merge.py --method task_arith --alpha 0.7
  python model_merge.py --method slerp --alpha 0.4 --output ./hacker_model_merged
  python model_merge.py --test                   # 融合後直接跑測試案例
"""

import argparse
import os
import torch
import numpy as np
from pathlib import Path
from transformers import AutoModelForSequenceClassification, AutoTokenizer


# ------------------------------------------------------------------ #
# 融合策略
# ------------------------------------------------------------------ #

def merge_linear(sd_a: dict, sd_b: dict, alpha: float) -> dict:
    """線性加權：merged = (1-α)*A + α*B"""
    merged = {}
    for key in sd_a:
        pa, pb = sd_a[key].float(), sd_b[key].float()
        merged[key] = ((1.0 - alpha) * pa + alpha * pb).to(sd_a[key].dtype)
    return merged


def merge_slerp(sd_a: dict, sd_b: dict, alpha: float) -> dict:
    """
    球面線性插值 (SLERP)：
    在參數向量的超球面上插值，保留旋轉方向，
    對 embedding / attention 層效果比 linear 好。
    退化為 linear 時（兩向量幾乎相同）自動 fallback。
    """
    merged = {}
    for key in sd_a:
        pa = sd_a[key].float().flatten()
        pb = sd_b[key].float().flatten()

        dot = (pa * pb).sum()
        norm_a = pa.norm()
        norm_b = pb.norm()

        # scalar 或全零張量直接線性插值
        if pa.numel() == 1 or norm_a < 1e-8 or norm_b < 1e-8:
            result = (1.0 - alpha) * pa + alpha * pb
        else:
            cos_theta = (dot / (norm_a * norm_b)).clamp(-1.0, 1.0)
            theta = torch.acos(cos_theta)
            sin_theta = torch.sin(theta)

            if sin_theta.abs() < 1e-6:
                # 向量幾乎平行，fallback linear
                result = (1.0 - alpha) * pa + alpha * pb
            else:
                result = (
                    torch.sin((1.0 - alpha) * theta) / sin_theta * pa
                    + torch.sin(alpha * theta) / sin_theta * pb
                )

        merged[key] = result.reshape(sd_a[key].shape).to(sd_a[key].dtype)
    return merged


def merge_task_arithmetic(sd_base: dict, sd_b: dict, alpha: float) -> dict:
    """
    Task Arithmetic（Ilharco et al. 2023）：
    delta = B − base（B 額外學到的知識向量）
    merged = base + α * delta
    α > 1.0 放大新知識，< 1.0 保守融合
    """
    merged = {}
    for key in sd_base:
        base = sd_base[key].float()
        delta = sd_b[key].float() - base
        merged[key] = (base + alpha * delta).to(sd_base[key].dtype)
    return merged


# ------------------------------------------------------------------ #
# 主要融合流程
# ------------------------------------------------------------------ #

def merge_models(
    path_a: str,
    path_b: str,
    output_dir: str,
    method: str = "slerp",
    alpha: float = 0.5,
):
    print(f"\n[*] 融合策略: {method.upper()}  α={alpha}")
    print(f"    A (base)  : {path_a}")
    print(f"    B (target): {path_b}")
    print(f"    輸出      : {output_dir}\n")

    # 載入
    tokenizer = AutoTokenizer.from_pretrained(path_a)
    model_a = AutoModelForSequenceClassification.from_pretrained(path_a)
    model_b = AutoModelForSequenceClassification.from_pretrained(path_b)

    sd_a = model_a.state_dict()
    sd_b = model_b.state_dict()

    # 確認架構相同
    if set(sd_a.keys()) != set(sd_b.keys()):
        raise ValueError("兩個模型的參數鍵不一致，無法融合")

    total = len(sd_a)
    print(f"[+] 共 {total} 個參數張量，開始融合...")

    if method == "linear":
        merged_sd = merge_linear(sd_a, sd_b, alpha)
    elif method == "slerp":
        merged_sd = merge_slerp(sd_a, sd_b, alpha)
    elif method == "task_arith":
        # A 是 base（v2），B 是新訓練的（v3）
        merged_sd = merge_task_arithmetic(sd_a, sd_b, alpha)
    else:
        raise ValueError(f"未知策略: {method}，可選 linear / slerp / task_arith")

    # 寫入融合後的模型
    model_a.load_state_dict(merged_sd)
    os.makedirs(output_dir, exist_ok=True)
    model_a.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"[✓] 已存至 {output_dir}")
    return output_dir


# ------------------------------------------------------------------ #
# 測試案例
# ------------------------------------------------------------------ #

TEST_CASES = [
    ("root.env.cloud.aws",               "access_key", "Leaf", '"[REDACTED_AWS_EXAMPLE]"',                          4),
    ("root.user.git",                    "token",      "Leaf", '"ghp_v9L3p0K1mN2bV5c8X7z4A1q9W0e3R2t1Y4u5"',    3),
    ("root.db.config",                   "url",        "Leaf", '"postgres://admin:topsecret@internal-db.local:5432/main"', 5),
    ("root.i18n.en.placeholders",        "pwd",        "Leaf", '"Please enter your password"',                    6),
    ("root.theme.styles",                "activeColor","Leaf", '"ocean-blue"',                                    3),
    ("root.network.nodes[4]",            "private_ip", "Leaf", '"192.168.1.105"',                                 5),
    ("root.features.adminConsole",       "is_enabled", "Leaf", '"true"',                                          4),
    ("root.services.monitoring",         "dsn",        "Leaf", '"https://ae2b@sentry.io/12345"',                  5),
    ("root.app.build",                   "version",    "Leaf", '"v2.1.0-release-candidate"',                      2),
    ("root.infra.secrets.manager.v1",    "ssh_key",    "Leaf", '"-----BEGIN RSA PRIVATE KEY-----"',               8),
]

EXPECTED = [
    ("access_key",  "CRIT",  0.85),
    ("token",       "CRIT",  0.85),
    ("url",         "CRIT",  0.85),
    ("pwd",         "SAFE",  0.15),
    ("activeColor", "SAFE",  0.10),
    ("private_ip",  "HIGH",  0.55),
    ("is_enabled",  "AMB",   None),   # 模糊，不設強期望
    ("dsn",         "HIGH",  0.65),
    ("version",     "LOW",   0.50),
    ("ssh_key",     "CRIT",  0.75),
]


def run_test(model_path: str, label: str = ""):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path).to(device)
    model.eval()

    def score(path, key, struct, val, depth):
        text = f"Path: {path} | Key: {key} | Struct: {struct} | Val: {val} | Depth: {depth}"
        inputs = tokenizer(text, return_tensors="pt", truncation=True,
                           max_length=192, padding="max_length").to(device)
        with torch.no_grad():
            s = model(**inputs).logits.item()
        return round(max(0.0, min(1.0, s)), 4)

    scores = [score(*tc) for tc in TEST_CASES]

    title = f"[ {label or model_path} ]"
    print(f"\n{'='*72}")
    print(f"  {title}")
    print(f"{'='*72}")
    print(f"{'RISK':<8} {'SCORE':>6}  {'KEY':<15}  VALUE")
    print("-" * 72)

    for (p, k, st, v, d), s in zip(TEST_CASES, scores):
        if s > 0.8:    tag = "\033[91m[CRIT]\033[0m"
        elif s > 0.5:  tag = "\033[93m[HIGH]\033[0m"
        elif s > 0.2:  tag = "\033[96m[MED ]\033[0m"
        else:          tag = "\033[92m[SAFE]\033[0m"
        val_short = (v[:30] + "..") if len(v) > 32 else v
        print(f"{tag} {s:>6.4f}  {k:<15}  {val_short}")

    print("-" * 72)
    mae = np.mean([abs(s - tc[2]) for s, tc in zip(scores, EXPECTED) if tc[2] is not None])
    print(f"  MAE (vs 期望, 跳過 AMB): {mae:.4f}")
    return scores


# ------------------------------------------------------------------ #
# CLI
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="模型融合工具")
    parser.add_argument("--model_a",  default="./hacker_model_final_v2",       help="Base 模型路徑")
    parser.add_argument("--model_b",  default="./hacker_model_final_v3_low_lr",help="Target 模型路徑")
    parser.add_argument("--output",   default="./hacker_model_merged",          help="輸出目錄")
    parser.add_argument("--method",   default="slerp",
                        choices=["linear", "slerp", "task_arith"],
                        help="融合策略 (預設 slerp)")
    parser.add_argument("--alpha",    type=float, default=0.7,
                        help="融合比例 0.0=全A, 1.0=全B (task_arith 可>1)")
    parser.add_argument("--test",     action="store_true",
                        help="融合後跑 10 個測試案例並與 v2/v3 比較")
    parser.add_argument("--test_only",action="store_true",
                        help="只測試現有模型，不融合")
    args = parser.parse_args()

    if args.test_only:
        run_test(args.model_a, "v2")
        run_test(args.model_b, "v3")
    else:
        output = merge_models(
            path_a=args.model_a,
            path_b=args.model_b,
            output_dir=args.output,
            method=args.method,
            alpha=args.alpha,
        )

        if args.test:
            run_test(args.model_a, "v2 (base)")
            run_test(args.model_b, "v3 (target)")
            run_test(output, f"merged ({args.method} α={args.alpha})")
