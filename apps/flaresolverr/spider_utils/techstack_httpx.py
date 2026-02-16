import subprocess
import logging
from c2_core.config.logging import log_function_call

logger = logging.getLogger(__name__)


def _run_cmd(url, headless=False):
    # 1. 改用 List 方式構建指令，不要用字串拼，這才是專業的
    cmd = [
        "docker",
        "run",
        "--rm",
        "projectdiscovery/httpx",
        "-u",
        url,
        "-json",
        "-hash",
        "md5",
        "-tech-detect",
        "-status-code",
        "-title",
        "-cl",
        "-ct",
        "-location",
        "-rt",
        "-server",
        "-timeout",
        "30",
        "-silent",
        "-irr",
        "-follow-redirects",
    ]

    # 2. 只有在 headless 且確信 Docker 鏡像支持時才加 (但官方鏡像通常不支持)
    if headless:
        # 如果你真的要用 chrome，你得自己 build 一個有 chrome 的 docker 鏡像
        # 暫時先註解掉，或是確認你的鏡像真的有 chrome
        # cmd.extend(["-system-chrome", "-jsc", "window.scrollTo(0, document.body.scrollHeight);"])
        logger.warning("警告：官方 httpx 鏡像不支持 -system-chrome，自動降級。")

    try:
        # 使用 List 模式，不需 shell=True，更安全、更快
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=40)

        if result.returncode != 0:
            # 這裡把 stderr 印出來，你就能看到 httpx 到底在罵什麼
            logger.error(
                f"Httpx 報錯啦！ Code: {result.returncode}, Error: {result.stderr}"
            )
            return None

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        logger.error(f"Httpx 執行超時: {url}")
        return None
    except Exception as e:
        logger.error(f"Docker 炸了: {e}")
        return None


@log_function_call()
def send_httpx_request(url):
    return _run_cmd(url, headless=False)


@log_function_call()
def send_httpx_request_chrome(url):
    return _run_cmd(url, headless=True)
