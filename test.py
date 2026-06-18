import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_openai import ChatOpenAI

# ================= 配置區域 =================
API_KEY = "sk-yBMQgpSlo1wG44xOOhqdWWAwKojv1XtUTESg8nO6X4GKTt9_mv_atJmiap7H8mlY"
BASE_URL = "https://api.yuhuanstudio.com/v1"
MODEL_NAME = "tokenrouter/MiniMax-M3"

CONCURRENT_REQUESTS = 100  
TOTAL_REQUESTS = 100       
TIMEOUT = 150              
# ============================================

client_kwargs = {
    "api_key": API_KEY,
    "base_url": BASE_URL,
    "temperature": 0.7,      
    "request_timeout": TIMEOUT,
    # 【改進 1】啟用自動重試，當遇到連線錯誤或 5xx 錯誤時自動重試 2 次
    "max_retries": 2, 
}

BASE_PROMPTS = [
    "請用五個字形容今天的天氣。",
    "請用一句話推薦一本書。",
    "請寫出一個只有三個字的問候語。",
    "請用四個字祝福寫程式的人。",
    "請用一句話說一個冷笑話。"
]

def warmup_connection():
    """【改進 2】發送預熱請求，喚醒中轉伺服器"""
    print("🔄 正在進行首次連線預熱 (Warm-up)...")
    try:
        # 使用極小的 max_tokens 減少等待
        warmup_chat = ChatOpenAI(
            model=MODEL_NAME,
            max_tokens=1,
            **client_kwargs
        )
        start_warmup = time.time()
        # 僅發送一個空字元或簡短字詞
        warmup_chat.invoke("ping")
        print(f"✅ 預熱完成！中轉站已喚醒，耗時: {time.time() - start_warmup:.2f}s。")
    except Exception as e:
        # 預熱失敗也不影響後續執行，僅做提示
        print(f"⚠️ 預熱請求未成功（可能因伺服器啟動慢），準備進入正式測試。原因: {str(e).split('\n')[0]}")
    print("=" * 70)

def send_request(task_id, prompt_content):
    """向 MiniMax-M3 發送單次請求並記錄數據"""
    start_time = time.time()
    try:
        chat = ChatOpenAI(
            model=MODEL_NAME,
            max_tokens=50,  
            **client_kwargs
        )
        
        response = chat.invoke(prompt_content)
        latency = time.time() - start_time
        reply = response.content.strip()
        
        return {
            "task_id": task_id,
            "status": "success",
            "prompt": prompt_content,
            "latency": latency,
            "reply": reply
        }
    except Exception as e:
        err_msg = str(e).split('\n')[0]
        return {
            "task_id": task_id,
            "status": "failed",
            "prompt": prompt_content,
            "error": err_msg
        }

def run_stress_test():
    # 1. 在正式測試前，先執行連線預熱
    warmup_connection()
    
    # 2. 準備測試任務
    tasks = []
    for i in range(1, TOTAL_REQUESTS + 1):
        base_prompt = BASE_PROMPTS[(i - 1) % len(BASE_PROMPTS)]
        prompt_with_id = f"({i}) {base_prompt}"
        tasks.append((i, prompt_with_id))

    print(f"開始對 {MODEL_NAME} 進行高併發壓力測試...")
    print(f"配置執行緒併發數: {CONCURRENT_REQUESTS}")
    print(f"總計劃發送請求數: {TOTAL_REQUESTS}")
    print("=" * 70)
    
    start_total = time.time()
    results = []
    
    # 3. 併發執行
    with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = {
            executor.submit(send_request, task_id, prompt_content): task_id
            for task_id, prompt_content in tasks
        }
        
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            
            if res["status"] == "success":
                print(f"[任務 #{res['task_id']}] ✅ 成功 | 延遲: {res['latency']:.2f}s | 內容簡短摘要: {res['reply'][:20]}...")
            else:
                print(f"[任務 #{res['task_id']}] ❌ 失敗 | 原因: {res['error']}")
            
    total_duration = time.time() - start_total
    
    # 4. 統計分析
    successes = [r for r in results if r["status"] == "success"]
    failures = [r for r in results if r["status"] == "failed"]
    
    print("\n" + "=" * 70)
    print(" 壓力測試統計摘要 ")
    print("=" * 70)
    print(f"總共發送請求數 : {TOTAL_REQUESTS}")
    print(f"成功請求數     : {len(successes)}")
    print(f"失敗請求數     : {len(failures)}")
    print(f"測試總耗時     : {total_duration:.2f} 秒")
    
    if successes:
        latencies = [r["latency"] for r in successes]
        avg_latency = sum(latencies) / len(latencies)
        print(f"平均響應時間   : {avg_latency:.2f} 秒")

if __name__ == "__main__":
    run_stress_test()