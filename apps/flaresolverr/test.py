import requests
import logging
import sys


# 模擬你的配置
class FakeConfig:
    FLARESOLVERR_URL = "http://localhost:8191/v1"  # 請確認這是否為你的實際位址


Config = FakeConfig()
RANDOM_HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def downloader(js_url) -> str | None:
    # --- 階段 1：直接抓取 ---
    logger.info(f"嘗試直接抓取: {js_url}")
    try:
        resp = requests.get(js_url, timeout=5, headers=RANDOM_HEADER, verify=False)
        if resp.status_code == 200:
            logger.info("直接抓取成功！")
            return resp.text
        logger.warning(f"直接抓取失敗，Status Code: {resp.status_code}")
    except Exception as e:
        logger.info(f"Requests 發生異常: {e}")

    # --- 階段 2：FlareSolverr ---
    logger.info(f"準備派出 FlareSolverr 戰鬥: {js_url}")
    payload = {"cmd": "request.get", "url": js_url, "maxTimeout": 60000}

    try:
        logger.info(f"發送請求至 FlareSolverr: {Config.FLARESOLVERR_URL}")
        # 注意：這裡 timeout 設短一點以便測試連通性
        r = requests.post(Config.FLARESOLVERR_URL, json=payload, timeout=70)
        logger.info(f"FlareSolverr 響應代碼: {r.status_code}")

        solver_resp = r.json()
        if solver_resp.get("status") == "ok":
            content = solver_resp["solution"]["response"]
            logger.info(f"FlareSolverr 抓取成功，內容長度: {len(content)}")
            return content
        else:
            logger.error(f"FlareSolverr 回報錯誤: {solver_resp.get('message')}")
            return None
    except requests.exceptions.ConnectionError:
        logger.error(
            f"❌ 無法連線到 FlareSolverr (位址: {Config.FLARESOLVERR_URL})。請檢查 Docker 是否啟動。"
        )
        return None
    except Exception as e:
        logger.error(f"❌ FlareSolverr 調用發生未預期錯誤: {type(e).__name__} - {e}")
        return None


if __name__ == "__main__":
    # 測試目標 1: 蘋果資產 (通常會擋直接請求)
    test_url = "https://apps.apple.com/assets/index~DSzBP59nFl.js"

    # 測試目標 2: 一般 URL (應該直接成功)
    # test_url = "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"

    result = downloader(test_url)
    if result:
        print("\n=== 最終結果 ===")
        print(f"成功取得內容，前 100 字元: {result[:100]}...")
    else:
        print("\n=== 最終結果 ===")
        print("失敗：未能取得內容。")
