import os
import time
import concurrent.futures
from openai import OpenAI

# 設定 default 分組的環境變數
API_KEY = os.getenv("AI_API_KEY", "sk-5A7mVLaFowGNNnhQpUWcavd2FugygANH9D2iIKXQ3rkYClir")
BASE_URL = os.getenv("AI_API_BASE_URL", "https://agentrouter.org/v1")

# 初始化 OpenAI 客戶端
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

# 新的 20 個模型清單
models_to_test = [
    "claude-opus-4-6",
    "deepseek-v4-pro",
    "deepseek-v4-flash"
]

def send_single_request(model_name, timeout=15.0):
    """
    根據模型名稱自動路由到對應的 API 接口（對話、圖像或語音）
    """
    start_time = time.time()
    try:
        # 1. 路由至圖像生成介面
        if "image" in model_name or "imagine" in model_name:
            response = client.images.generate(
                model=model_name,
                prompt="a small red apple",
                n=1,
                size="256x256",  # 最小尺寸以節省額度
                timeout=timeout
            )
            latency = time.time() - start_time
            url = response.data[0].url if response.data else ""
            reply = f"[圖像生成成功] URL: {url[:50]}..." if url else "[圖像生成成功，但無回傳網址]"
            return True, latency, reply

        # 2. 路由至音訊合成介面
        elif "-tts" in model_name:
            response = client.audio.speech.create(
                model=model_name,
                voice="alloy",
                input="Hello",
                timeout=timeout
            )
            latency = time.time() - start_time
            # 檢查二進位檔案大小
            data_len = len(response.content) if response.content else 0
            reply = f"[語音合成成功] 檔案大小: {data_len} bytes"
            return True, latency, reply

        # 3. 一般對話模型
        else:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": "Hello, please reply in 5 words."}
                ],
                max_tokens=15,
                temperature=0.3,
                timeout=timeout
            )
            latency = time.time() - start_time
            content = response.choices[0].message.content
            reply = content.strip().replace('\n', ' ') if content else "[空內容/None]"
            return True, latency, reply

    except Exception as e:
        latency = time.time() - start_time
        err_msg = str(e).split('\n')[0]
        return False, latency, err_msg

def run_phase_1():
    """
    第一階段：快速並行掃描
    """
    print("=" * 80)
    print("階段一：開始快速掃描 20 個新模型 (並行限制: 10, 超時限制: 15s)...")
    print("=" * 80)
    
    successful_models = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_model = {executor.submit(send_single_request, model, timeout=15.0): model for model in models_to_test}
        
        for future in concurrent.futures.as_completed(future_to_model):
            model = future_to_model[future]
            success, latency, detail = future.result()
            
            if success:
                successful_models.append(model)
                print(f" [成功] 耗時: {latency:5.2f}s | 模型: {model:<35} | 回應: {detail}")
            else:
                print(f"*[失敗]* 耗時: {latency:5.2f}s | 模型: {model:<35} | 錯誤: {detail}")
                
    print(f"\n階段一完成。掃描成功數: {len(successful_models)}/{len(models_to_test)}")
    return successful_models

def run_phase_2(successful_models):
    """
    第二階段：針對第一階段成功的模型，每個模型獨立進行 10 個並行請求的穩定性壓測
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
    print(" 穩定性測試匯總報告 (default分組)")
    print("=" * 80)
    for r in stability_report:
        err_str = f" | 錯誤: {r['errors']}" if r['errors'] else ""
        print(f"模型: {r['model']:<35} | 成功率: {r['success_rate']:<6} | 平均耗時: {r['avg_latency']:5.2f}s{err_str}")
    print("=" * 80)

if __name__ == "__main__":
    # 執行階段一：快速篩選
    success_list = run_phase_1()
    
    # 執行階段二：測試篩選出模型的穩定性
    run_phase_2(success_list)