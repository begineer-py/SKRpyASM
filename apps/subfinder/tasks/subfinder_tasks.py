import logging
import subprocess
from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from apps.core.models.scans_record_modles import SubfinderScan
from c2_core.config.logging import log_function_call
from .utils import parse_subfinder_output, update_subdomain_assets

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
@log_function_call()
def start_subfinder(self, scan_id: int):
    """Start subfinder scanning task for a given scan ID."""
    scan = None
    try:
        scan = SubfinderScan.objects.select_related("which_seed").get(id=scan_id)
        seed = scan.which_seed
        logger.info(f"Subfinder 任務 (ID: {scan.id}) for Seed '{seed.value}' 已啟動。")

        scan.status = "RUNNING"
        scan.started_at = timezone.now()
        scan.save(update_fields=["status", "started_at"])

        # Construct subfinder command
        command = ["subfinder", "-d", seed.value, "-json", "-silent", "-all"]
        
        logger.info(
            f"準備執行 Subfinder 命令 for Scan ID {scan.id}: {' '.join(command)}"
        )
        
        # Execute subfinder command
        process = subprocess.run(command, capture_output=True, text=True, timeout=900)

        if process.returncode == 0:
            logger.info(f"Subfinder 掃描成功 for Scan ID {scan.id}。準備更新資產庫。")
            
            # Parse output and update assets
            raw_output = process.stdout.strip()
            current_subdomains_map = parse_subfinder_output(raw_output)
            
            if not current_subdomains_map:
                logger.warning("Subfinder 沒有輸出任何結果")
            
            # Update subdomain assets
            update_results = update_subdomain_assets(seed, current_subdomains_map, scan)
            
            scan.added_count = update_results["new_count"]
            scan.status = "COMPLETED"
            
            logger.info(
                f"資產庫更新完成 for Seed '{seed.value}'. "
                f"新增: {update_results['new_count']}, "
                f"更新: {update_results['reactivated_count']}, "
                f"失聯: {update_results['missing_count']}."
            )

            # Trigger next task in chain
            from .dns_tasks import resolve_dns_for_seed
            resolve_dns_for_seed.delay(seed_id=seed.id, subfinder_scan_id=scan.id)
            
        else:
            error_message = f"Subfinder command failed with exit code {process.returncode}. Stderr: {process.stderr[:1000]}"
            logger.error(error_message)
            scan.status = "FAILED"
            
    except ObjectDoesNotExist:
        logger.error(f"找不到 SubfinderScan 紀錄，ID: {scan_id}")
        return
    except Exception as e:
        logger.exception(f"Subfinder 任務 ID {scan_id} 發生錯誤: {e}")
        if scan:
            scan.status = "FAILED"
    finally:
        if scan:
            scan.completed_at = timezone.now()
            scan.save()
            logger.info(
                f"Subfinder 掃描任務 ID: {scan.id} 最終狀態已保存: {scan.status}"
            )
