# c2_core/config/config.py

import os
import yaml
from pathlib import Path
import sys
import random


class Config:
    """
    動態配置情報中心。
    在模塊加載時，自動解析 docker-compose.yml 並設置所有服務 URL 和關鍵配置。
    """

    AI_SERVICE_URLS: dict = {}

    @staticmethod
    def _parse_all_configs() -> dict:
        """
        【升級版】核心解析函數。讀取 docker-compose.yml 並提取所有服務的 URL 和關鍵環境變量。
        """
        configs = {}
        try:
            base_dir = Path(__file__).resolve().parent.parent.parent
            # 假設 docker-compose.yml 在項目根目錄的 docker/ 文件夾下
            compose_path = base_dir / "docker" / "docker-compose.yml"

            if not compose_path.is_file():
                print(
                    f"[❌] 配置錯誤: 找不到 docker-compose.yml 文件於 {compose_path}",
                    file=sys.stderr,
                )
                return {}

            with open(compose_path, "r") as f:
                compose_data = yaml.safe_load(f)

            services = compose_data.get("services", {})

        except Exception as e:
            print(f"[❌] 配置錯誤: 解析 docker-compose.yml 失敗: {e}", file=sys.stderr)
            return {}

        ### 修正/重寫 ###
        def get_service_config(service_name: str) -> dict | None:
            """輔助函數，提取服務的端口和環境變量。"""
            service = services.get(service_name)
            if not service:
                return None

            config_data = {}
            # --- 健壯的端口解析邏輯 ---
            if service.get("ports"):
                # 只取第一個端口映射，這對大多數情況都適用
                port_mapping = service["ports"][0]
                # 格式是 "HOST_IP:HOST_PORT:CONTAINER_PORT" 或 "HOST_PORT:CONTAINER_PORT"
                # 我們只關心暴露給主機的部分
                parts = str(port_mapping).split(":")

                host_ip = "127.0.0.1"  # 默認 IP
                host_port = ""

                if len(parts) == 3:  # 格式: "127.0.0.1:8085:8080"
                    host_ip = parts[0]
                    host_port = parts[1]
                elif len(parts) == 2:  # 格式: "8085:8080"
                    host_port = parts[0]
                elif len(parts) == 1 and isinstance(
                    port_mapping, (int, str)
                ):  # 格式: 8080 (不常見，但兼容)
                    host_port = str(port_mapping)

                if host_port:
                    base_url = f"http://{host_ip}:{host_port}"
                    config_data["URL"] = base_url

            # 解析環境變量
            if service.get("environment"):
                # 支持列表和字典兩種格式的環境變量
                env_vars = service.get("environment")
                env_dict = {}
                if isinstance(env_vars, list):  # 格式: ["VAR=value", "VAR2=value2"]
                    for item in env_vars:
                        if "=" in item:
                            key, value = item.split("=", 1)
                            env_dict[key] = value
                elif isinstance(env_vars, dict):  # 格式: {VAR: value, VAR2: value2}
                    env_dict = env_vars
                config_data["ENV"] = env_dict

            return config_data

        # --- 逐個解析服務 ---
        service_map = {
            "postgres": "postgres",
            "redis": "redis",
            "hasura": "hasura",
            "nocodb": "nocodb",
            "flaresolverr": "flaresolverr",
            "flareproxygo": "flareproxygo",
            "nyaproxy_spider": "nyaproxy_spider",
        }

        for key, service_name in service_map.items():
            config = get_service_config(service_name)
            if config:  # 只有在成功解析後才加入
                configs[key] = config

        # 只有在成功解析了至少一個服務後才打印成功消息
        if configs:
            print(f"[✅] 動態配置加載完成: 成功解析 {len(configs)} 個服務。")
        return configs

    # --- 在類被加載時，立即執行解析並設置類屬性 ---
    _CONFIGS = _parse_all_configs()

    # 為外部調用提供更清晰的接口
    HASURA_URL = _CONFIGS.get("hasura", {}).get("URL")
    HASURA_ADMIN_SECRET = (
        _CONFIGS.get("hasura", {}).get("ENV", {}).get("HASURA_GRAPHQL_ADMIN_SECRET")
    )

    NYAPROXY_SPIDER_URL = _CONFIGS.get("nyaproxy_spider", {}).get("URL")
    FLARESOLVERR_URL = _CONFIGS.get("flaresolverr", {}).get("URL")  # 示例：添加新服務
    MODEL_PATH = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "apps",
        "flaresolverr",
        "gf",
        "hacker_gf",
        "json_decoder",
        "hacker_model_final_v2",
    )

    # ... 其他服務 URL 可以按需添加 ...apps/flaresolverr/gf/hacker_gf/json_decoder/hacker_model_final_v2


# 你可以在這裡直接打印來快速驗證
# print("Hasura URL:", Config.HASURA_URL)
# print("Hasura Secret:", Config.HASURA_ADMIN_SECRET)
# print("FlareSolverr URL:", Config.FLARESOLVERR_URL)
