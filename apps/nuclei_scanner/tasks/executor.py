import json
import logging
import subprocess
from typing import Dict, Any, List, Optional
from django.utils import timezone
from apps.core.models import NucleiScan
from .database import save_nuclei_result_to_db
from apps.api_keys.utils import get_active_api_keys, generate_nuclei_secrets
import os

logger = logging.getLogger(__name__)


def execute_nuclei_command(
    command: List[str],
    asset_map: Dict[str, int],
    asset_type: str,
    scan_record_ids: List[int],
    callback_step_id: Optional[int] = None,
):
    """
    封裝 Nuclei 執行邏輯，實現實時流處理與關鍵漏洞告警
    """
    # 獲取 API 金鑰並生成臨時配置文件
    api_keys = get_active_api_keys()
    secrets_file = generate_nuclei_secrets(api_keys)
    
    # 用於收集輸出的摘要 (前 50 行或關鍵發現)
    output_summary = []
    
    # 如果有金鑰，則將其加入命令中
    if secrets_file:
        command = command + ["-sf", secrets_file]
        logger.debug(f"已加入 Nuclei 秘密文件: {secrets_file}")

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )

        # 這裡會逐行讀取 Nuclei 的 JSON 輸出
        for line in iter(process.stdout.readline, ""):
            if not line:
                continue
            try:
                result = json.loads(line.strip())
                
                # 收集發現到摘要中
                if len(output_summary) < 50:
                    output_summary.append(line.strip())

                # --- 1. 提取關鍵資訊 ---
                info = result.get("info", {})
                vuln_name = info.get("name", "Unknown")
# ... (中間日誌邏輯不變)
                severity = info.get(
                    "severity", "info"
                ).upper()  # info, low, medium, high, critical
                template_id = result.get("template-id", "N/A")
                target_url = result.get("matched-at") or result.get("url") or "Unknown"

                # --- 2. 設定日誌等級與表情符號 ---
                if severity == "CRITICAL":
                    log_prefix = "🚨 [CRITICAL]"
                    log_level = logging.ERROR
                elif severity == "HIGH":
                    log_prefix = "🔥 [HIGH]"
                    log_level = logging.WARNING
                elif severity == "MEDIUM":
                    log_prefix = "🟡 [MEDIUM]"
                    log_level = logging.INFO
                elif severity == "LOW":
                    log_prefix = "🔵 [LOW]"
                    log_level = logging.INFO
                else:
                    log_prefix = "ℹ️ [INFO]"
                    log_level = logging.DEBUG

                # --- 3. 立即輸出日誌 ---
                logger.log(
                    log_level,
                    f"{log_prefix} Found Vulnerability: {vuln_name} | "
                    f"Template: {template_id} | Target: {target_url}",
                )

                # --- 4. 數據庫保存邏輯 ---
                target_key = target_url
                asset_id = asset_map.get(target_key)
                if not asset_id and target_key:
                    asset_id = next(
                        (v for k, v in asset_map.items() if target_key.startswith(k)),
                        None,
                    )

                if asset_id:
                    save_nuclei_result_to_db(
                        result,
                        asset_id=asset_id,
                        asset_type=asset_type,
                        scan_record_id=None,
                    )

            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"處理 Nuclei 單行結果時發生錯誤: {e}")

        process.wait()
        NucleiScan.objects.filter(id__in=scan_record_ids).update(
            status="COMPLETED", completed_at=timezone.now()
        )

    except Exception as e:
        logger.exception(f"{asset_type} Nuclei 掃描執行失敗: {e}")
        NucleiScan.objects.filter(id__in=scan_record_ids).update(
            status="FAILED", completed_at=timezone.now()
        )
    finally:
        # 清理臨時配置文件
        if 'secrets_file' in locals() and secrets_file and os.path.exists(secrets_file):
            os.remove(secrets_file)
            logger.debug(f"已清理 nuclei 臨時配置文件: {secrets_file}")
            
        summary_text = "\n".join(output_summary) if output_summary else "Nuclei 掃描已完成，但未發現明顯漏洞標籤。"
        return summary_text


# =============================================================================
# 通用批次掃描執行器
# =============================================================================

def _execute_nuclei_batch(
    asset_type: str, ids: List[int], custom_tags: Optional[List[str]] = None, task_self=None, callback_step_id: Optional[int] = None
) -> str:
    """
    【通用 Nuclei 執行助手】
    從工廠取得特定資產的目標提取方式與標籤，並組合標準化 Command 後執行。
    """
    from .asset_configs import get_nuclei_asset_registry

    registry = get_nuclei_asset_registry()
    if asset_type not in registry:
        raise ValueError(f"未知的資產類型 '{asset_type}' 用於 Nuclei 掃描。")

    cfg = registry[asset_type]

    # 1. 調用特定資產的資料庫讀取與目標提取邏輯
    asset_map, scan_record_ids, targets, final_tags_str = cfg.prepare_targets(
        ids, custom_tags
    )

    if not targets:
        logger.warning(f"[{cfg.asset_name}] 沒有需要掃描的目標。")
        return "Nuclei 掃描終止：沒有有效的掃描目標。"

    logger.info(f"[{cfg.asset_name}] 啟動 Nuclei 掃描 | 目標數: {len(asset_map)} | Tags: {final_tags_str} | Step: {callback_step_id}")

    # 2. 建構標準化核心命令
    command = (
        ["nice", "nuclei"]
        + targets
        + [
            "-tags", final_tags_str,
            "-as",        # 自動掃描模式
            "-j",         # JSON 輸出
            "-nc",        # No Color
            "-silent",    # 靜默模式
        ]
    )
    
    if asset_type == "url":
        command.extend(["-severity", "low,medium,high,critical"])

    # 3. 呼叫核心執行器
    return execute_nuclei_command(
        command=command,
        asset_map=asset_map,
        asset_type=cfg.asset_name,
        scan_record_ids=scan_record_ids,
        callback_step_id=callback_step_id,
    )
