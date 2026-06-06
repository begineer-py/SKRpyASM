import os
import time
import concurrent.futures
from openai import OpenAI

# 設定環境變數
API_KEY = os.getenv("AI_API_KEY", "sk-GMa3aMdJd2jcnY4dP8h9q8q5PLW6FbtFyCiqoDRrddyhad0v")
BASE_URL = os.getenv("AI_API_BASE_URL", "https://tokeness.cn/v1")

# 初始化 OpenAI 客戶端
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

models_to_test = [
    # Claude 系列
    "claude-haiku-4-5",
    "claude-opus-4-6",
    "claude-opus-4-7",
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    
    # DeepSeek 系列
    "deepseek-v4-flash",
    "deepseek-v4-pro",
    
    # Gemini 系列
    # "gemini-3.1-flash-image", # 圖片生成，文字對話會噴錯，預設註解
    "gemini-3.1-pro",
    "gemini-3.5-flash",
    
    # GLM 系列
    "glm-5.1",
    
    # GPT 系列
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-5.5",
    # "gpt-image-2", # 圖片生成，文字對話會噴錯，預設註解
    
    # Kimi 系列
    "kimi-k2.6", # 注意：此模型可能要求 temperature 必須為 1.0
    
    # MiMo 系列
    "mimo-v2.5",
    "mimo-v2.5-pro",
    
    # MiniMax 系列
    "minimax-m2.7",
    "minimax-m3"
]

def send_single_request(model_name, timeout=15.0):
    """
    發送單次請求的基礎函式，已修正 NoneType 的 strip 錯誤
    """
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": "你是什麼模型"}
            ],
            max_tokens=15,
            temperature=0.3,
            timeout=timeout
        )
        latency = time.time() - start_time
        content = response.choices[0].message.content
        
        # 修正：安全處理 content 為 None 的情況
        reply = content.strip().replace('\n', ' ') if content else "[空內容/None]"
        return True, latency, reply
    except Exception as e:
        latency = time.time() - start_time
        err_msg = str(e).split('\n')[0]
        return False, latency, err_msg

def run_phase_1():
    """
    第一階段：快速掃描所有模型（並行 10 個 worker）
    """
    print("=" * 80)
    print(f"階段一：開始快速掃描 {len(models_to_test)} 個模型 (並行限制: 10, 超時限制: 15s)...")
    print("=" * 80)
    
    successful_models = []
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_model = {executor.submit(send_single_request, model, timeout=15.0): model for model in models_to_test}
        
        for future in concurrent.futures.as_completed(future_to_model):
            model = future_to_model[future]
            success, latency, detail = future.result()
            results.append((model, success, latency, detail))
            
            if success:
                successful_models.append(model)
                print(f" [成功] 耗時: {latency:5.2f}s | 模型: {model:<50} | 回應: {detail}")
            else:
                print(f"*[失敗]* 耗時: {latency:5.2f}s | 模型: {model:<50} | 錯誤: {detail}")
                
    print(f"\n階段一完成。掃描成功數: {len(successful_models)}/{len(models_to_test)}")
    return successful_models

def run_phase_2(successful_models):
    """
    第二階段：針對篩選出的成功模型，每個模型同時發送 10 個請求測試穩定性
    """
    if not successful_models:
        print("\n沒有任何模型成功通過第一階段，無法進行穩定性測試。")
        return

    print("\n" + "=" * 80)
    print(f"階段二：針對成功的 {len(successful_models)} 個模型進行「同時 10 個請求」穩定性測試...")
    print("=" * 80)

    stability_report = []

    for idx, model in enumerate(successful_models, 1):
        print(f"\n[{idx}/{len(successful_models)}] 測試中: {model} ...")
        
        latencies = []
        success_count = 0
        errors = set()
        
        # 同時發起 10 個請求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_single_request, model, timeout=25.0) for _ in range(10)]
            
            for future in concurrent.futures.as_completed(futures):
                success, latency, detail = future.result()
                if success:
                    success_count += 1
                    latencies.append(latency)
                else:
                    errors.add(detail)
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        min_latency = min(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0
        
        print(f" └─> 穩定性結果: {success_count}/10 成功")
        if success_count > 0:
            print(f" └─> 延遲統計: 平均 {avg_latency:.2f}s (最小: {min_latency:.2f}s, 最大: {max_latency:.2f}s)")
        if errors:
            print(f" └─> 出現錯誤: {list(errors)}")
            
        stability_report.append({
            "model": model,
            "success_rate": f"{success_count}/10",
            "avg_latency": avg_latency,
            "errors": list(errors)
        })
        
        # 稍微緩衝，避免對伺服器造成過大壓力
        time.sleep(1.0)

    # 印出最終報告
    print("\n" + "=" * 80)
    print(" 穩定性測試匯總報告")
    print("=" * 80)
    for r in stability_report:
        err_str = f" | 錯誤: {r['errors']}" if r['errors'] else ""
        print(f"模型: {r['model']:<50} | 成功率: {r['success_rate']:<6} | 平均耗時: {r['avg_latency']:5.2f}s{err_str}")
    print("=" * 80)

if __name__ == "__main__":
    # 執行階段一：快速篩選
    success_list = run_phase_1()
    
    # 執行階段二：測試篩選出模型的穩定性
    run_phase_2(success_list)