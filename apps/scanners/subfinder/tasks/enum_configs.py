"""
apps/subfinder/tasks/enum_configs.py

Subdomain Enumeration 工廠配置 (EnumToolConfig)

集中管理不同子域名發現工具 (subfinder, amass) 的差異，
包括使用的模型、命令構建、API 金鑰處理與輸出解析。
"""

from dataclasses import dataclass
from typing import Callable, List, Dict, Type, Any
from django.db.models import Model


@dataclass
class EnumToolConfig:
    """
    子域名發現工具的配置

    Attributes:
        tool_name: 工具名稱 (用於日誌)
        scan_model: 對應的 Scan 模型 (如 SubfinderScan, AmassScan)
        get_config_func: 產生臨時配置文件的函式 (來自 apps.api_keys.utils)
        build_command: 回傳指令陣列的函式
        parser_func: 解析指令輸出的函式 (從 raw string 轉成 map)
        timeout: 執行超時 (秒)
    """
    tool_name: str
    scan_model: Type[Model]
    get_config_func: Callable[[Any], str]
    build_command: Callable[[str, str, str], List[str]]
    parser_func: Callable[[str], Dict[str, str]]
    timeout: int


# =============================================================================
# 各工具的特定實現邏輯
# =============================================================================

def _build_subfinder_command(seed_val: str, config_file: str, output_file: str = None) -> List[str]:
    # subfinder 直接輸出到 stdout (所以不需要 output_file 參數，或可忽略)
    return ["subfinder", "-d", seed_val, "-json", "-silent", "-all", "-pc", config_file]


def _build_amass_command(seed_val: str, config_file: str, output_file: str) -> List[str]:
    # amass 建議輸出到檔案, 因為其輸出較大且慢
    return ["amass", "enum", "-d", seed_val, "-json", output_file, "-config", config_file, "-passive", "-silent"]


# =============================================================================
# 懶加載 Registry
# =============================================================================

_enum_registry_cache: dict | None = None

def get_enum_tool_registry() -> dict:
    from apps.core.models import SubfinderScan, AmassScan
    from apps.api_keys.utils import generate_subfinder_config, generate_amass_config
    from .utils import parse_subfinder_output, parse_amass_output

    global _enum_registry_cache
    if _enum_registry_cache is None:
        _enum_registry_cache = {
            "subfinder": EnumToolConfig(
                tool_name="Subfinder",
                scan_model=SubfinderScan,
                get_config_func=generate_subfinder_config,
                build_command=_build_subfinder_command,
                parser_func=parse_subfinder_output,
                timeout=900,
            ),
            "amass": EnumToolConfig(
                tool_name="Amass",
                scan_model=AmassScan,
                get_config_func=generate_amass_config,
                build_command=_build_amass_command,
                parser_func=parse_amass_output,
                timeout=1800,
            ),
        }
    return _enum_registry_cache
