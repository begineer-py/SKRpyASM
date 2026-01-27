# test.py
import httpx
from Wappalyzer import Wappalyzer, WebPage
import json

print("--- 準備測試 python-wappalyzer 功能 ---")

# 這次用會出問題的目標 URL，驗證修正
TARGET_URL = "https://www.djangoproject.com"

print(f"目標 URL: {TARGET_URL}")

try:
    # --- 步驟 1: 發送 HTTP 請求，獲取響應 ---
    print("發送 HTTP 請求中...")
    with httpx.Client(follow_redirects=True, timeout=15) as client:
        response = client.get(TARGET_URL)
        response.raise_for_status()  # 媽的，如果狀態碼不是 2xx，就報錯！

    print(f"HTTP 請求成功！狀態碼: {response.status_code}, 最終 URL: {response.url}")

    # --- 步驟 2: 初始化 Wappalyzer ---
    print("初始化 Wappalyzer...")
    wappalyzer = Wappalyzer.latest()
    print("Wappalyzer 初始化完成。")

    # --- 步驟 3: 創建 WebPage 對象 ---
    print("準備 WebPage 對象...")
    webpage = WebPage(
        url=str(response.url),  # 確保是字符串
        html=response.text,
        headers=dict(response.headers),  # httpx.Headers 轉成普通字典
    )
    print("WebPage 對象準備完成。")

    # --- 步驟 4: 執行 Wappalyzer 分析 ---
    print("執行技術偵測分析...")
    detected_apps = wappalyzer.analyze(webpage)

    print("\n--- 偵測結果 ---")
    if detected_apps:
        # 媽的，先打印原始輸出，看看這狗東西到底返回了什麼！
        print("\n--- Wappalyzer 原始偵測結果 (Raw Output) ---")
        print(detected_apps)
        print("-------------------------------------------\n")

        # 格式化結果，這次會判斷類型，避免 'str' object has no attribute 'get'
        formatted_results = []
        for app in detected_apps:
            if isinstance(app, dict):  # 媽的，如果它是字典，就正常處理
                formatted_results.append(
                    {
                        "Name": app.get("name"),
                        "Version": app.get("version", "N/A"),
                        "Confidence": app.get("confidence", "N/A"),
                        "Categories": [
                            cat.get("name")
                            for cat in app.get("categories", [])
                            if isinstance(cat, dict)
                        ],  # 確保 category 也是字典
                    }
                )
            elif isinstance(app, str):  # 媽的，如果它是字符串，就當成技術名稱
                formatted_results.append(
                    {
                        "Name": app,
                        "Version": "N/A",
                        "Confidence": "N/A",
                        "Categories": [],
                    }
                )
            else:  # 媽的，遇到未知類型了
                formatted_results.append(
                    {
                        "Name": f"UNKNOWN_TYPE: {type(app).__name__}",
                        "RawData": str(app),
                        "Error": "媽的，Wappalyzer 輸出了無法識別的類型！",
                    }
                )

        # 媽的，直接打印漂亮的 JSON 格式！
        print("--- 格式化後的偵測結果 ---")
        print(json.dumps(formatted_results, indent=2, ensure_ascii=False))
        print(f"\n總共偵測到 {len(detected_apps)} 種技術。")
    else:
        print("媽的，沒有偵測到任何技術！")

except ImportError:
    print("\n--- 錯誤 ---")
    print("媽的，找不到 `python-wappalyzer` 庫！")
    print("請先安裝它：`pip install python-wappalyzer`")
except httpx.RequestError as e:
    print("\n--- 錯誤 ---")
    print(f"媽的，HTTP 請求失敗！錯誤訊息: {e}")
except httpx.HTTPStatusError as e:
    print("\n--- 錯誤 ---")
    print(
        f"媽的，HTTP 請求返回非 2xx 狀態碼！狀態: {e.response.status_code}, URL: {e.request.url}"
    )
except Exception as e:
    print("\n--- 錯誤 ---")
    print(f"媽的，發生未知錯誤！錯誤訊息: {e}")

print("\n--- 測試結束 ---")
