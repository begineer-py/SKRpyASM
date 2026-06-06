import os
import time
import concurrent.futures
from openai import OpenAI

# 設定環境變數
API_KEY = os.getenv("AI_API_KEY", "sk-nkC4JJnxHtgI-PM_HFc9QPTcwkVqRUP7MAhh6cafk5pvWaO1D6DXr59puppWzVRc")
BASE_URL = os.getenv("AI_API_BASE_URL", "https://api.yuhuanstudio.com/v1")

# 初始化 OpenAI 客戶端
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

# 待測試的模型清單（已整理你提供的新清單）
models_to_test = [
    # --- TokenRouter 來源 ---
    "tokenrouter/deepseek/deepseek-v4-flash",
    "tokenrouter/deepseek/deepseek-v4-pro",
    "tokenrouter/moonshotai/kimi-k2.6",
    "tokenrouter/qwen/qwen3.7-max",
    "tokenrouter/qwen/qwen3.7-plus",
    "tokenrouter/seed-2-0-lite-260428",
    "tokenrouter/seed-2-0-mini-260428",
    "tokenrouter/seed-2-0-pro-260328",
    "tokenrouter/xiaomi/mimo-v2.5",
    "tokenrouter/xiaomi/mimo-v2.5-pro",
    
    # --- Z.ai (Zhipu) 來源 ---
    "zai/glm-4.5",
    "zai/glm-4.5-air",
    "zai/glm-4.6",
    "zai/glm-4.7",
    "zai/glm-5",
    "zai/glm-5-turbo",
    "zai/glm-5.1",
    "zai/glm-5v-turbo",
    
    # --- OpenRouter (免費版) 來源 ---
    "openrouter/google/gemma-4-26b-a4b-it:free",
    "openrouter/google/gemma-4-31b-it:free",
    "openrouter/moonshotai/kimi-k2.6:free",
    "openrouter/openai/gpt-oss-120b:free",
    "openrouter/qwen/qwen3-coder:free",
    "openrouter/qwen/qwen3-next-80b-a3b-instruct:free",
    "openrouter/z-ai/glm-4.5-air:free",
    
    # --- Google 原生 來源 ---
    "google/gemini-3-flash-preview",
    "google/gemini-3.1-flash-lite-preview",
    "google/gemma-4-26b-a4b-it",
    "google/gemma-4-31b-it",
    # "google/gemini-embedding-2",  # Embedding模型，chat.completions會報錯，預設註解

    # --- ModelScope 來源 ---
    # "modelscope/Qwen/Qwen-Image-2512", # 圖片生成，chat.completions會報錯，預設註解
    # "modelscope/Qwen/Qwen-Image-Edit", # 圖片編輯，chat.completions會報錯，預設註解
    "modelscope/deepseek-ai/DeepSeek-V4-Flash",
    "modelscope/deepseek-ai/DeepSeek-V4-Pro",
    "modelscope/zai-org/GLM-5.1",

    # --- MiniMax 來源 ---
    "minimax/MiniMax-M2.5",
    "minimax/MiniMax-M2.5-highspeed",
    "minimax/MiniMax-M2.7",
    "minimax/MiniMax-M2.7-highspeed",

    # --- NVIDIA 來源 ---
    "nvidia/stepfun-ai/step-3.5-flash",
    "nvidia/z-ai/glm-5.1",
    "nvidia/z-ai/glm4.7",

    # --- GitHub Models 來源 ---
    # "github/openai/text-embedding-3-large" # Embedding模型，chat.completions會報錯，預設註解
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