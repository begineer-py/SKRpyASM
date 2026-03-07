import json
import logging
import subprocess
from typing import Dict, Any, List
from django.utils import timezone
from apps.core.models import NucleiScan
from .database import save_nuclei_result_to_db

logger = logging.getLogger(__name__)


def execute_nuclei_command(
    command: List[str],
    asset_map: Dict[str, int],
    asset_type: str,
    scan_record_ids: List[int],
):
    """
    封裝 Nuclei 執行邏輯，實現實時流處理與關鍵漏洞告警
    """
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

                # --- 1. 提取關鍵資訊 ---
                info = result.get("info", {})
                vuln_name = info.get("name", "Unknown")
                severity = info.get(
                    "severity", "info"
                ).upper()  # info, low, medium, high, critical
                template_id = result.get("template-id", "N/A")
                target_url = result.get("matched-at") or result.get("url") or "Unknown"

                # --- 2. 設定日誌等級與表情符號 ---
                # 根據嚴重程度決定顯示方式
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
                # 這樣你在 Celery log 裡就能立刻看到每一條漏洞
                logger.log(
                    log_level,
                    f"{log_prefix} Found Vulnerability: {vuln_name} | "
                    f"Template: {template_id} | Target: {target_url}",
                )

                # --- 4. 數據庫保存邏輯 ---
                target_key = target_url
                asset_id = asset_map.get(target_key)

                # 模糊匹配 (防止 URL 斜槓不一致)
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
