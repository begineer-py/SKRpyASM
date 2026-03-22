"""
apps/subfinder/tasks/common.py

子域名發現通用執行流程

負責處理 Subfinder 與 Amass 的共通生命週期：
記錄檢索 -> 狀態更新 -> 命令執行 -> 解析輸出 -> 資產同步 -> 銜接下一環節。
"""

import os
import logging
import subprocess
from django.utils import timezone
from .utils import update_subdomain_assets
from apps.api_keys.utils import get_active_api_keys

logger = logging.getLogger(__name__)


from typing import Optional

def _run_subdomain_enum(tool_key: str, scan_id: int, callback_step_id: Optional[int] = None):
    """
    【通用子域名發現任務核心】
    
    Args:
        tool_key: 'subfinder' | 'amass'
        scan_id: 對應掃描模型的 ID
        callback_step_id: 回調用的 Step ID (可選)
    """
    from .enum_configs import get_enum_tool_registry

    registry = get_enum_tool_registry()
    if tool_key not in registry:
        logger.error(f"未知的工具型別: {tool_key}")
        return

    cfg = registry[tool_key]
    Model = cfg.scan_model
    scan = None
    config_file = None
    output_file = None

    try:
        # 1. 抓取掃描紀錄
        scan = Model.objects.select_related("which_seed").get(id=scan_id)
        seed = scan.which_seed
        logger.info(f"[{cfg.tool_name}] 任務 (ID: {scan.id}) for Seed '{seed.value}' 已啟動。")

        # 2. 更新狀態為 RUNNING
        scan.status = "RUNNING"
        scan.started_at = timezone.now()
        scan.save(update_fields=["status", "started_at"])

        # 3. 獲取 API 金鑰並生成臨時配置
        api_keys = get_active_api_keys()
        config_file = cfg.get_config_func(api_keys)

        # 如果是 Amass，需要定義中間輸出的 JSON 檔
        if tool_key == "amass":
            output_file = f"/tmp/amass_out_{scan_id}.json"

        # 4. 構建並執行命令
        command = cfg.build_command(seed.value, config_file, output_file)
        logger.info(f"[{cfg.tool_name}] 準備執行命令: {' '.join(command)}")

        process = subprocess.run(command, capture_output=True, text=True, timeout=cfg.timeout)

        if process.returncode == 0:
            logger.info(f"[{cfg.tool_name}] 掃描成功。準備更新資產庫。")

            # 5. 獲取原始輸出內容
            raw_output = ""
            if tool_key == "amass":
                if os.path.exists(output_file):
                    with open(output_file, "r") as f:
                        raw_output = f.read().strip()
                else:
                    logger.warning(f"[{cfg.tool_name}] Amass 掃描結束但找不到輸出檔案: {output_file}")
            else:
                # Subfinder 直接從 stdout 拿
                raw_output = process.stdout.strip()

            # 6. 解析與更新
            current_subdomains_map = cfg.parser_func(raw_output)
            if not current_subdomains_map:
                logger.warning(f"[{cfg.tool_name}] 掃描沒有輸出任何結果")

            update_results = update_subdomain_assets(seed, current_subdomains_map, scan)

            scan.added_count = update_results["new_count"]
            scan.status = "COMPLETED"

            logger.info(
                f"[{cfg.tool_name}] 資產庫更新完成 for Seed '{seed.value}'. "
                f"新增: {update_results['new_count']}, 更新: {update_results['reactivated_count']}."
            )

            # 7. 觸發下一個環節 (DNS 解析)
            from .dns_tasks import resolve_dns_for_seed
            resolve_dns_for_seed.delay(
                seed_id=seed.id, 
                subfinder_scan_id=scan.id if tool_key == "subfinder" else None, 
                source=tool_key,
                callback_step_id=callback_step_id
            )

        else:
            stderr = process.stderr[:1000]
            logger.error(f"[{cfg.tool_name}] 命令失敗，返回碼 {process.returncode}. Stderr: {stderr}")
            scan.status = "FAILED"

    except Model.DoesNotExist:
        logger.error(f"找不到 {cfg.tool_name}Scan 紀錄，ID: {scan_id}")
        return
    except subprocess.TimeoutExpired:
        logger.error(f"[{cfg.tool_name}] 掃描執行超時。")
        if scan:
            scan.status = "FAILED"
    except Exception as e:
        logger.exception(f"[{cfg.tool_name}] 任務 ID {scan_id} 發生錯誤: {e}")
        if scan:
            scan.status = "FAILED"
    finally:
        # 清理
        if config_file and os.path.exists(config_file):
            os.remove(config_file)
        if output_file and os.path.exists(output_file):
            os.remove(output_file)

        if scan:
            scan.completed_at = timezone.now()
            scan.save()
