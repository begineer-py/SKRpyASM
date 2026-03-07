import subprocess
import json
from logging import getLogger

logger = getLogger(__name__)


class jsluice:
    def __init__(self, cleaned_js: str) -> None:
        # 假設 cleaned_js 是 JS 檔案的內容字串
        self.cleaned_js = cleaned_js
        self.url_lists = []

    def js_files_scan(self) -> list[str]:
        logger.info("準備開始掃描 JS 文件內容")

        try:
            # 使用 input 參數將內容餵給 jsluice
            # 指令只需要 ['jsluice', 'urls', '/dev/stdin']
            command = ["jsluice", "urls", "/dev/stdin"]

            result = subprocess.run(
                command,
                input=self.cleaned_js,  # 直接將內容傳入 stdin
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=True,  # 如果指令執行失敗會拋出異常
            )

            # jsluice 的輸出是每一行一個 JSON 物件
            lines = result.stdout.strip().split("\n")

            for line in lines:
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    url = data.get("url")
                    if url:
                        self.url_lists.append(url)
                except json.JSONDecodeError:
                    logger.error(f"無法解析 JSON 行: {line}")

            # 去重（可選）
            self.url_lists = list(set(self.url_lists))

            logger.info(f"掃描完成，發現 {len(self.url_lists)} 個 URL")
            return self.url_lists

        except subprocess.CalledProcessError as e:
            logger.error(f"執行 jsluice 時出錯: {e.stderr}")
            return []
        except Exception as e:
            logger.error(f"發生未知錯誤: {str(e)}")
            return []


def run_test():
    print("--- [戰術測試] jsluice URL 提取測試 ---")

    # 1. 構建複雜的測試 JS 內容
    test_js_content = """
    // 1. 絕對路徑
    const remoteApi = "https://api.internal.target.com/v1/auth";
    const cdnUrl = "https://static.target.com/assets/main.js";
    
    // 2. 相對路徑
    var loginEndpoint = "/login?redirect=true";
    let uploadPath = "/api/v2/user/upload/profile.php";
    
    // 3. 混淆在代碼中的路徑
    $.ajax({
        url: "/debug/config.json",
        method: "GET"
    });

    // 4. 外部無關路徑 (應在後續邏輯中被過濾)
    const google = "https://www.google-analytics.com/collect";
    """

    # 2. 檢查環境中是否有 jsluice
    import shutil

    if not shutil.which("jsluice"):
        print(
            "[!] 錯誤: 系統路徑中未發現 'jsluice' 二進制文件，請先安裝 (go install github.com/BishopFox/jsluice@latest)"
        )
        return

    # 3. 執行掃描
    scanner = xurls(test_js_content)
    extracted_urls = scanner.js_files_scan()

    # 4. 驗證結果
    expected_samples = [
        "https://api.internal.target.com/v1/auth",
        "/login?redirect=true",
        "/debug/config.json",
        "/api/v2/user/upload/profile.php",
    ]

    print(f"[*] 掃描完成。提取到 {len(extracted_urls)} 個 URL。")

    success_count = 0
    for sample in expected_samples:
        if sample in extracted_urls:
            print(f"[✅] 成功提取: {sample}")
            success_count += 1
        else:
            print(f"[❌] 未能提取: {sample}")

    print(f"\n[*] 測試結果: {success_count}/{len(expected_samples)} 通過")

    # 5. 打印所有提取到的內容供人工校驗
    print("\n--- 所有提取結果 ---")
    for u in sorted(extracted_urls):
        print(f"  > {u}")


if __name__ == "__main__":
    run_test()
