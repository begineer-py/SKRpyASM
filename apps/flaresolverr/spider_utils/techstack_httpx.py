import subprocess
import logging
import shlex
from c2_core.config.logging import log_function_call

logger = logging.getLogger(__name__)


@log_function_call()
def _run_cmd(url, headless=False):
    """
    執行 Docker 命令 (Raw Shell Mode)
    嚴格使用驗證成功的 Shell 指令結構，不做 Python 列表轉換。
    """

    # 1. 處理 URL 安全轉義 (防止 URL 內的特殊字符炸掉 Shell)
    safe_url = shlex.quote(url)

    # 2. 構建原始 Shell 字串
    # 這裡直接寫死你驗證成功的那個指令結構，包含 -system-chrome
    # 注意：我們直接在字串中 f-string 插入 safe_url，而不是用 list append
    cmd_string = (
        "docker run --rm projectdiscovery/httpx \\\n"
        f"  -u {safe_url} \\\n"
        "  -json \\\n"
        "  -json \\\n"
        "  -hash md5 \\\n"
        "  -tech-detect \\\n"
        "  -status-code \\\n"
        "  -title -cl -ct -location -rt -server -system-chrome \\\n"
        "  -timeout 20 \\\n"
        "  -silent"
        "  -irr"
        "  -follow-redirects"
    )

    try:
        # [DEBUG] 在日誌中印出原始指令，方便直接複製回終端機 Debug
        logger.info(f"Httpx Shell CMD:\n{cmd_string}")

        # 3. 使用 shell=True 執行
        # executable="/bin/bash" 確保像你在終端機一樣處理換行符
        result = subprocess.run(
            cmd_string,
            shell=True,
            capture_output=True,
            text=True,
            executable="/bin/bash",
        )

        # 4. 錯誤處理與結果回傳
        if result.returncode != 0:
            logger.error(f"Httpx 執行錯誤! ReturnCode: {result.returncode}")
            if result.stderr:
                logger.error(f"Httpx Stderr: {result.stderr.strip()}")
            return None

        stdout = result.stdout.strip()

        # 關鍵：如果無輸出，印出 stderr 幫助診斷
        if not stdout:
            logger.warning(f"Httpx 執行無輸出: {url}")
            if result.stderr:
                logger.debug(f"Httpx Stderr: {result.stderr.strip()}")
            return None

        return stdout

    except Exception as e:
        logger.error(f"Docker execution failed: {e}")
        return None


@log_function_call()
def send_httpx_request(url):

    return _run_cmd(url, headless=False)


@log_function_call()
def send_httpx_request_chrome(url):
    return _run_cmd(url, headless=True)
