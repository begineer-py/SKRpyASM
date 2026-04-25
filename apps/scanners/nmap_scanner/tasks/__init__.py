import logging
import subprocess
import shlex
import xml.etree.ElementTree as ET

from celery import shared_task
from django.db import transaction
from django.db.models import Q
from typing import Optional

from apps.core.models import NmapScan, Port, IP
from apps.core.utils import with_auto_callback
from apps.scanners.base_task import ScannerLifecycle

logger = logging.getLogger(__name__)


@shared_task(bind=True, name="nmap_scanner.tasks.perform_nmap_scan")
@with_auto_callback
def perform_nmap_scan(
    self,
    scan_id: int,
    ip_address: str,
    nmap_args: str,
    callback_step_id: Optional[int] = None,
):
    """
    執行 Nmap 掃描，解析結果，並將情報存入資料庫。
    使用 ScannerLifecycle 管理 PENDING → RUNNING → COMPLETED / FAILED 狀態機。
    """
    logger.info(
        f"任務 [{self.request.id}] 領取命令：開始處理 NmapScan ID: {scan_id} "
        f"for IP: {ip_address} (Step: {callback_step_id})"
    )

    try:
        scan_record = NmapScan.objects.get(id=scan_id)
    except NmapScan.DoesNotExist:
        logger.error(f"找不到 NmapScan 記錄，ID: {scan_id}")
        return f"Nmap 掃描中止：找不到 NmapScan ID {scan_id}"

    if scan_record.status != "PENDING":
        logger.warning(
            f"Scan ID {scan_id} 狀態為 {scan_record.status}，非 PENDING。任務終止。"
        )
        return f"Scan ID {scan_id} not in PENDING state."

    command = f"nmap {nmap_args} {ip_address}"
    logger.info(f"準備執行命令: {command}")

    with ScannerLifecycle(scan_record, logger, output_field="nmap_output") as lc:
        process = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minutes
        )

        if process.returncode != 0:
            raise RuntimeError(
                f"Nmap 執行失敗，返回碼: {process.returncode}. "
                f"Stderr: {process.stderr[:500]}"
            )

        xml_output = process.stdout
        lc.set_output(xml_output)  # 存入 nmap_output 欄位
        logger.info(f"NmapScan ID {scan_id} 執行完畢，準備解析 XML 結果。")
        parse_and_save_nmap_results(scan_record, xml_output, ip_address)

    logger.info(f"NmapScan ID {scan_id} 最終狀態: {scan_record.status}")
    return f"Nmap 掃描完成。IP: {ip_address}"


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
