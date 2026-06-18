import json
import os

# 配置路徑
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "datasets", "merged_train.jsonl")
HIGH_RISK_FILE = os.path.join(BASE_DIR, "datasets", "high_risk_pool.jsonl")
LOW_RISK_FILE = os.path.join(BASE_DIR, "datasets", "low_risk_pool.jsonl")


def triage_data(threshold=0.25):
    """
    將高度敏感數據與背景雜訊數據分離
    """
    high_count = 0
    low_count = 0

    if not os.path.exists(INPUT_FILE):
        print(f"[!] 錯誤：找不到輸入文件 {INPUT_FILE}")
        return

    print(f"[*] 正在掃描數據池：{INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f_in, open(
        HIGH_RISK_FILE, "a", encoding="utf-8"
    ) as f_high, open(LOW_RISK_FILE, "a", encoding="utf-8") as f_low:

        for line in f_in:
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
                label = float(item.get("label", 0))

                # 核心分流邏輯
                if label >= threshold:
                    f_high.write(json.dumps(item, ensure_ascii=False) + "\n")
                    high_count += 1
                else:
                    f_low.write(json.dumps(item, ensure_ascii=False) + "\n")
                    low_count += 1
            except Exception as e:
                print(f"[-] 跳過損壞數據: {e}")

    print(f"\n[✓] MCLim 數據隔離完成：")
    print(f"    - 高危正樣本池 (Score >= {threshold}): {high_count} 條")
    print(f"    - 雜訊負樣本池 (Score <  {threshold}): {low_count} 條")
    print(f"[*] 隔離文件已存儲於 datasets/ 目錄下。")


if __name__ == "__main__":
    triage_data()
