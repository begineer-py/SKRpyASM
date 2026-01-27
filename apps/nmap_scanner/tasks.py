import logging
import subprocess
import shlex
import xml.etree.ElementTree as ET
from datetime import datetime

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

# 操！把模型都叫過來
from apps.core.models import NmapScan, Port, IP

logger = logging.getLogger(__name__)


# 操！這就是我們的 nmap 突擊隊
@shared_task(bind=True, name="nmap_scanner.tasks.perform_nmap_scan")
def perform_nmap_scan(self, scan_id: int, ip_address: str, nmap_args: str):
    """
    執行 Nmap 掃描，解析結果，並將情報存入資料庫。
    這是一個獨立的、可以失敗和重試的作戰單元。
    """
    logger.info(
        f"任務 [{self.request.id}] 領取命令：開始處理 NmapScan ID: {scan_id} for IP: {ip_address}"
    )

    scan_record = None
    try:
        # 操！第一件事，從資料庫把任務命令書拿出來。
        scan_record = NmapScan.objects.get(id=scan_id)

        # 如果任務不是 PENDING，說明有問題，直接滾蛋
        if scan_record.status != "PENDING":
            logger.warning(
                f"Scan ID {scan_id} 狀態為 {scan_record.status}，非 PENDING。任務終止。"
            )
            return f"Scan ID {scan_id} not in PENDING state."

        # 立即更新狀態為 RUNNING，讓前台知道我們在幹活了。
        scan_record.status = "RUNNING"
        scan_record.started_at = timezone.now()  # 操！用帶時區的時間
        scan_record.save()

        # 準備執行命令。用 shlex.split 保證參數安全，防止命令注入。
        # 操！目標 IP 必須是最後一個參數。
        command = f"nmap {nmap_args} {ip_address}"
        logger.info(f"準備執行命令: {command}")

        # 執行命令，設置超時（比如30分鐘），捕獲標準輸出和錯誤
        # 注意：nmap -oX - 會把XML輸出到stdout
        process = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes timeout
        )

        # 檢查 nmap 是否成功執行
        if process.returncode != 0:
            error_msg = (
                f"Nmap 執行失敗，返回碼: {process.returncode}. Stderr: {process.stderr}"
            )
            raise RuntimeError(error_msg)

        xml_output = process.stdout
        # 操！必須把原始輸出存下來，方便日後查水錶
        scan_record.nmap_output = xml_output
        scan_record.save(update_fields=["nmap_output"])

        logger.info(f"NmapScan ID {scan_id} 執行完畢，準備解析 XML 結果。")

        # 操！這裡是重頭戲：把 nmap 的 XML 報告變成我們資料庫裡的情報。
        # 直接把 ip_address 字串傳進去，讓解析器自己去查 IP 對象
        parse_and_save_nmap_results(scan_record, xml_output, ip_address)

        # 如果能走到這裡，說明一切順利
        scan_record.status = "COMPLETED"
        logger.info(f"NmapScan ID {scan_id} 成功完成。")

    except NmapScan.DoesNotExist:
        logger.error(
            f"操！任務 [{self.request.id}] 找不到 NmapScan 記錄，ID: {scan_id}"
        )
        return
    except subprocess.TimeoutExpired:
        logger.error(f"NmapScan ID {scan_id} 執行超時。")
        if scan_record:
            scan_record.status = "FAILED"
            scan_record.error_message = "Nmap command timed out after 30 minutes."
            scan_record.save()
    except Exception as e:
        logger.exception(f"處理 NmapScan ID {scan_id} 時發生未知錯誤: {e}")
        if scan_record:
            scan_record.status = "FAILED"
            scan_record.error_message = f"An unexpected error occurred: {str(e)}"
            scan_record.save()
    finally:
        # 操！無論成敗，都必須有始有終。更新最終狀態和完成時間。
        if scan_record and scan_record.status != "PENDING":  # 避免覆蓋狀態
            # 只有當還沒記錄完成時間時才更新，或者強制更新
            if not scan_record.completed_at:
                scan_record.completed_at = timezone.now()
                scan_record.save()

        if scan_record:
            logger.info(f"NmapScan ID {scan_id} 最終狀態: {scan_record.status}")


def parse_and_save_nmap_results(
    scan_record: NmapScan, xml_output: str, ip_address: str
):
    """
    解析 nmap XML 輸出並更新 Port 資產庫。
    """
    try:
        # 1. 獲取 IP 對象
        ip_obj = IP.objects.filter(Q(ipv4=ip_address) | Q(ipv6=ip_address)).first()

        if not ip_obj:
            logger.error(f"解析失敗：資料庫找不到 IP {ip_address}")
            return

        root = ET.fromstring(xml_output)

        with transaction.atomic():
            for host in root.findall("host"):
                ports_element = host.find("ports")
                if ports_element is None:
                    continue

                for port_element in ports_element.findall("port"):
                    try:
                        port_number = int(port_element.get("portid"))
                        protocol = port_element.get("protocol")

                        state_element = port_element.find("state")
                        state = (
                            state_element.get("state")
                            if state_element is not None
                            else "unknown"
                        )

                        service_element = port_element.find("service")
                        service_name = (
                            service_element.get("name")
                            if service_element is not None
                            else None
                        )
                        service_version = (
                            service_element.get("version")
                            if service_element is not None
                            else None
                        )

                        # 操！這裡修正了：
                        # 1. 使用正確的欄位名 (last_scan_id, last_scan_type)
                        # 2. 接收 update_or_create 返回的 port_obj 來處理 M2M
                        port_obj, created = Port.objects.update_or_create(
                            ip=ip_obj,
                            port_number=port_number,
                            protocol=protocol,
                            defaults={
                                "state": state,
                                "service_name": service_name,
                                "service_version": service_version,
                                # 修正：對應你的模型定義
                                "last_scan_id": scan_record.id,
                                "last_scan_type": "NmapScan",  # 或者 scan_record.scan_type (如果有定義)
                                "last_seen": timezone.now(),
                            },
                        )

                        # 3. 處理 M2M 關係 (這步必須在物件建立後做)
                        port_obj.discovered_by_scans.add(scan_record)

                    except Exception as loop_e:
                        logger.warning(f"解析單個端口時出錯 (跳過): {loop_e}")
                        continue

        logger.info(f"IP {ip_address} 的端口數據已更新。")

    except Exception as e:
        logger.exception(f"解析 XML 或存儲數據時出錯: {e}")
        raise
