"""
apps/scanners/base_task.py

掃描任務生命週期管理器 (Scanner Lifecycle Manager)

將所有掃描器共用的 PENDING → RUNNING → COMPLETED / FAILED 狀態機
封裝進一個 Context Manager，各掃描任務只需 `with ScannerLifecycle(record, logger):` 即可。

使用範例::

    @shared_task(bind=True)
    def perform_nmap_scan(self, scan_id: int, ip: str):
        scan = NmapScan.objects.get(id=scan_id)
        with ScannerLifecycle(scan, logger) as lc:
            process = subprocess.run(...)
            lc.set_output(process.stdout)
            parse_and_save_nmap_results(scan, process.stdout, ip)
        # 離開 with 時，狀態自動寫入 COMPLETED（或 FAILED）及 completed_at
"""

from __future__ import annotations

import logging
from typing import Optional, Any

from django.utils import timezone

logger = logging.getLogger(__name__)


class ScannerLifecycle:
    """
    掃描任務生命週期 Context Manager。

    進入 with 區塊時：
        - 設定 scan_record.status = "RUNNING"
        - 設定 scan_record.started_at = now()
        - 儲存變更

    正常退出時：
        - 設定 scan_record.status = "COMPLETED"
        - 設定 scan_record.completed_at = now()
        - 儲存變更

    例外退出時：
        - 設定 scan_record.status = "FAILED"
        - 設定 scan_record.error_message = str(exception)
        - 設定 scan_record.completed_at = now()
        - 儲存變更
        - **不抑制例外**（繼續向上拋出）

    Attributes:
        record:  任何帶有 status / started_at / completed_at / error_message 欄位的 Django Model。
        log:     Logger 實例，用於輸出狀態轉換資訊。
        _output_field: (可選) 要把 raw output 存入的欄位名稱，預設 None（不存）。
        _output_value: set_output() 所設定的值。
        _save_fields:  (可選) 覆寫最終 save() 的 update_fields。若為 None，則全欄位存。
    """

    def __init__(
        self,
        record: Any,
        log: logging.Logger = logger,
        output_field: Optional[str] = None,
        save_fields: Optional[list[str]] = None,
    ) -> None:
        self.record = record
        self.log = log
        self._output_field = output_field
        self._output_value: Optional[str] = None
        self._save_fields = save_fields
        self._success = False

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def set_output(self, raw_output: str) -> None:
        """
        暫存原始輸出，結束時若有設定 output_field 則自動寫入 record。
        """
        self._output_value = raw_output

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------

    def __enter__(self) -> "ScannerLifecycle":
        record = self.record
        record.status = "RUNNING"
        record.started_at = timezone.now()
        # 只更新必要欄位，避免意外覆蓋其他資料
        record.save(update_fields=["status", "started_at"])
        self.log.info(
            f"[ScannerLifecycle] {record.__class__.__name__} ID={record.pk} — 狀態更新為 RUNNING"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        record = self.record

        if exc_type is None:
            # ── 正常完成 ─────────────────────────────────────────────
            record.status = "COMPLETED"
            self._success = True
            self.log.info(
                f"[ScannerLifecycle] {record.__class__.__name__} ID={record.pk} — 狀態更新為 COMPLETED"
            )
        else:
            # ── 例外發生 ─────────────────────────────────────────────
            record.status = "FAILED"
            error_msg = str(exc_val)[:2000]  # 截斷超長錯誤訊息
            if hasattr(record, "error_message"):
                record.error_message = error_msg
            self.log.error(
                f"[ScannerLifecycle] {record.__class__.__name__} ID={record.pk} — "
                f"例外: {exc_type.__name__}: {error_msg}"
            )

        record.completed_at = timezone.now()

        # ── 存入 raw output（如有需要）────────────────────────────────
        if self._output_field and self._output_value is not None:
            setattr(record, self._output_field, self._output_value)

        # ── 決定 save 的欄位 ────────────────────────────────────────
        save_kwargs: dict = {}
        if self._save_fields is not None:
            # 使用者若有指定 update_fields，就直接用；確保必要欄位在裡面
            base_fields = {"status", "completed_at"}
            if hasattr(record, "error_message") and not self._success:
                base_fields.add("error_message")
            if self._output_field and self._output_value is not None:
                base_fields.add(self._output_field)
            save_kwargs["update_fields"] = list(base_fields | set(self._save_fields))
        else:
            # 全欄位儲存（保持向後相容）
            pass

        try:
            record.save(**save_kwargs)
        except Exception as save_err:
            self.log.exception(
                f"[ScannerLifecycle] 儲存最終狀態失敗 for "
                f"{record.__class__.__name__} ID={record.pk}: {save_err}"
            )

        # 不抑制原始例外，讓 Celery / 呼叫者決定重試策略
        return False
