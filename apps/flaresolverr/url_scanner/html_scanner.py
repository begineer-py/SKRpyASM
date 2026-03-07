import subprocess
from logging import getLogger

logger = getLogger(__name__)


class XurlsScanner:
    def __init__(self, content: str) -> None:
        self.content = content  # 待掃描的 HTML 或文本內容
        self.url_lists = []

    def scan(self) -> list[str]:
        logger.info("開始使用 xurls 掃描內容中的鏈接")

        try:
            # -r 參數可以抓取更多「隱藏」或不規範的 URL
            command = ["xurls", "-r"]

            result = subprocess.run(
                command,
                input=self.content,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,
            )

            # xurls 輸出是純文字，一行一個 URL
            raw_urls = result.stdout.strip().split("\n")

            # 過濾掉空行並去重
            self.url_lists = sorted(
                list(set([u.strip() for u in raw_urls if u.strip()]))
            )

            logger.info(f"xurls 掃描完成，發現 {len(self.url_lists)} 個唯一鏈接")
            return self.url_lists

        except subprocess.CalledProcessError as e:
            logger.error(f"執行 xurls 時出錯: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"未知錯誤: {str(e)}")
            return []


# 測試代碼
if __name__ == "__main__":
    html_content = """
    <div>
        歡迎訪問 <a href="https://example.com">官網</a>
        後台地址：admin.internal.local/dashboard
        CDN地址：//static.test.com/js/main.js
    </div>
    """
    scanner = XurlsScanner(html_content)
    print(scanner.scan())
