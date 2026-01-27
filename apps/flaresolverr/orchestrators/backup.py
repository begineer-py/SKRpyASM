# flaresolverr/orchestrators/recon_orchestrator.py
import os
import logging

# 操，注意这个 import 路径！
# 我们假设 MySpider 最终会搬到 flaresolverr/spider.py
# 但为了让你现在就能跑，我们先从上一级的 my_spider.py 导入
try:
    from ..my_spider import MySpider
except ImportError:
    # 如果上面的失败了（比如独立运行脚本时），尝试另一个路径
    # 这只是为了测试方便，最终要删掉
    try:
        from flaresolverr.my_spider import MySpider
    except Exception:
        from my_spider import MySpider

# 优先导入本地项目内的分析引擎，其次再尝试外部安装的包，最后提供一个假实现
try:
    # 本地实现（项目内）：flaresolverr/gf/hacker_gf/pygf.py
    from flaresolverr.gf.hacker_gf.pygf import PatternAnalyzer
except Exception:
    try:
        # 外部安装的包：hacker_gf
        from hacker_gf import PatternAnalyzer
    except Exception:
        # 双重失败，则提供一个假的全尸，让代码能跑起来，但不会分析
        logging.warning("操，hacker_gf 没安装且本地实现不可用！分析功能将不可用。")

        class PatternAnalyzer:
            def run_all_patterns(self, lines):
                return [{"pattern": "dummy", "matches": [], "count": 0}]


logger = logging.getLogger(__name__)


class ReconOrchestrator:
    """
    v1.0 指挥官：
    1. 负责协调 MySpider 和 PatternAnalyzer。
    2. 吃进一个 URL，吐出一个包含所有战果的字典。
    3. 自己不干脏活，只负责指挥和打包。
    """

    def __init__(self, url: str, method: str = "GET", cookie_string: str = ""):
        """
        作战前的情报简报。
        """
        self.url = url
        self.method = method
        self.cookie_string = cookie_string

        # 装备我们的士兵和分析师
        self.spider = MySpider(
            url=self.url,
            method=self.method,
            cookie_string=self.cookie_string,
            flaresolverr_url=os.getenv(
                "FLARESOLVERR_URL"
            ),  # 从环境变量里拿 Flaresolverr 地址
        )
        self.analyzer = PatternAnalyzer()

        logger.info(f"指挥官就位，目标锁定: {self.url}")

    def run(self) -> dict:
        """
        按下「开始作战」的红色按钮。
        这将执行完整的 爬取 -> 分析 流水线。
        """
        logger.info(f"作战开始: {self.url}")

        # --- 第一阶段：派遣先锋部队 (MySpider) ---
        response = self.spider.send()

        if not response:
            logger.error(f"作战失败: 先锋部队未能为 {self.url} 夺取任何情报。")
            return {
                "success": False,
                "url": self.url,
                "error": "Spider failed to get a response.",
                "spider_result": None,
                "analysis_result": None,
            }

        logger.info(
            f"先锋部队成功返回情报 for {self.url}, 状态码: {response.status_code}"
        )

        # --- 第二阶段：情报整理 (translate_into_json) ---
        # 无论情报内容如何，先把它标准化
        spider_json_report = self.spider.translate_into_json(response)

        # --- 第三阶段：送交情报分析室 (hacker_gf) ---
        response_text = spider_json_report.get("response_text", "")
        if response_text:
            lines = response_text.splitlines()
            analysis_findings = self.analyzer.run_all_patterns(lines)
            logger.info(
                f"情报分析完成 for {self.url}，发现 {len(analysis_findings)} 类潜在敏感信息。"
            )
        else:
            analysis_findings = []
            logger.warning(f"情报内容为空 for {self.url}，跳过分析。")

        # --- 第四阶段：打包最终战报 ---
        logger.info(f"作战成功结束 for {self.url}")
        return {
            "success": True,
            "url": self.url,
            "error": None,
            "spider_result": spider_json_report,
            "analysis_result": analysis_findings,
        }
