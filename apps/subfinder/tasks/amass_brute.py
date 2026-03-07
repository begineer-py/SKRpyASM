import logging
import subprocess
import os
import json
from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

# 這裡假設你有一個 AmassScan 的模型，邏輯跟 SubfinderScan 一樣
from apps.core.models.scans_record_modles import AmassScan
from c2_core.config.logging import log_function_call

# 你可能需要一個專門解析 Amass JSON 的工具
from .utils import parse_amass_output, update_subdomain_assets

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
@log_function_call()
def start_amass_scan(self, scan_id: int, target_id: int = None):
    """啟動 Amass 掃描任務，這傢伙是重裝坦克。"""
    scan = None
    # 定義暫存檔案路徑，避免多個任務互相打架
    output_file = f"/tmp/amass_out_{scan_id}.json"

    try:
        # 1. 抓取掃描紀錄
        scan = AmassScan.objects.select_related("which_seed").get(id=scan_id)
        seed = scan.which_seed
        logger.info(f"Amass 任務 (ID: {scan.id}) 對於 Seed '{seed.value}' 正式開搞。")

        # 2. 更新狀態為 RUNNING
        scan.status = "RUNNING"
        scan.started_at = timezone.now()
        scan.save(update_fields=["status", "started_at"])

        # 3. 構建 Amass 命令
        # -passive: 先用被動模式，速度快且安全
        # -json: 剛才測試過，它會寫到檔案
        command = [
            "amass",
            "enum",
            "-d",
            seed.value,
            "-json",
            output_file,
            "-passive",  # 如果你想大殺特殺，可以把這行拿掉或換成 -brute
            "-silent",
        ]

        logger.info(f"準備執行 Amass 命令 (Scan ID {scan.id}): {' '.join(command)}")

        # 4. 執行指令 (Amass 很慢，超時設為 30 分鐘)
        process = subprocess.run(command, capture_output=True, text=True, timeout=1800)

        if process.returncode == 0 and os.path.exists(output_file):
            logger.info(f"Amass 掃描收工 (Scan ID {scan.id})。準備把資料塞進資料庫。")

            # 5. 讀取並解析輸出的 JSON 檔案
            with open(output_file, "r") as f:
                raw_output = f.read().strip()

            # 這裡你要自己寫一個 parse_amass_output，因為 Amass 的 JSON 格式跟 Subfinder 不一樣
            current_subdomains_map = parse_amass_output(raw_output)

            if not current_subdomains_map:
                logger.warning(f"Amass 忙了半天結果啥都沒撈到 (Scan ID {scan.id})")

            # 6. 更新資產庫 (沿用你的神級函數)
            update_results = update_subdomain_assets(seed, current_subdomains_map, scan)

            scan.added_count = update_results["new_count"]
            scan.status = "COMPLETED"

            logger.info(
                f"Amass 資產更新完畢 '{seed.value}'. "
                f"新發現: {update_results['new_count']}, "
                f"復活: {update_results['reactivated_count']}."
            )

            # 7. 觸發下一個任務 (DNS 解析)
            from .dns_tasks import resolve_dns_for_seed

            resolve_dns_for_seed.delay(seed_id=seed.id, scan_id=scan.id, source="amass")

        else:
            stderr = process.stderr[:1000]
            error_message = (
                f"Amass 命令掛了，Exit Code {process.returncode}. 錯誤訊息: {stderr}"
            )
            logger.error(error_message)
            scan.status = "FAILED"

    except ObjectDoesNotExist:
        logger.error(f"找不到 AmassScan 紀錄，ID: {scan_id}")
        return
    except subprocess.TimeoutExpired:
        logger.error(f"Amass 跑太久超時了 (ID: {scan_id})")
        if scan:
            scan.status = "TIMEOUT"
    except Exception as e:
        logger.exception(f"Amass 任務 ID {scan_id} 發生意外: {e}")
        if scan:
            scan.status = "FAILED"
    finally:
        # 清理暫存檔，不要留一堆垃圾在 /tmp
        if os.path.exists(output_file):
            os.remove(output_file)

        if scan:
            scan.completed_at = timezone.now()
            scan.save()
            logger.info(f"Amass 任務 ID: {scan.id} 最終狀態: {scan.status}")
