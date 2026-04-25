from ninja import Schema
from datetime import datetime
from typing import Optional, List, Union  # 操！Union 用起來，類型才精準


class PortSchema(Schema):
    port_number: int
    protocol: str
    state: str
    service_name: Optional[str] = None
    service_version: Optional[str] = None
    last_seen: datetime


# 用於觸發掃描的請求體
class NmapScanTriggerSchema(Schema):
    # 操！明確指定要打哪個 IP
    ip: str
    seed_ids: List[int]  # <--- 變更這裡：改成整數列表
    # 操！創建 IP 資產時，需要知道它屬於哪個根目標
    # 讓前端決定掃描策略，後端只負責執行
    scan_rate: int = 4
    scan_timeout_minute: int = 20
    # 操！端口可以是列表，也可以是 'all' 或 'top-1000' 這樣的字串
    scan_ports: Union[List[int], str] = "top-1000"
    scan_service_version: bool = True  # -sV
    scan_os: bool = False  # -O
    callback_step_id: Optional[int] = None


# 掃描任務的完整響應
class NmapScanSchema(Schema):
    id: int
    ip_id: int
    ip_address: list[str]  # 操！直接返回 IP 地址，前端不用再查一次
    scan_type: str
    nmap_args: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None  # 允許為空，預設為 None
    completed_at: Optional[datetime] = None  # 允許為空，預設為 None
    error_message: Optional[str] = None  # 錯誤訊息通常也是空的


class ErrorSchema(Schema):
    message: str
