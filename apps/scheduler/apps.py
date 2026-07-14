import logging

from django.apps import AppConfig
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)


class SchedulerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.scheduler"

    def ready(self):
        # 連接 post_migrate signal — 每次 migrate 完成後自動 idempotent 註冊核心排程
        post_migrate.connect(self._ensure_core_schedules, sender=self)

    def _ensure_core_schedules(self, **kwargs):
        """post_migrate callback: 確保所有核心 Celery Beat 任務已註冊到 DB。

        失敗時只 log warning 不阻擋 migrate（容忍 django_celery_beat 尚未 migrate 的情境）。
        """
        try:
            from apps.scheduler.beat_registry import ensure_core_schedules

            result = ensure_core_schedules()
            logger.info(
                f"[SchedulerConfig] Core schedules: "
                f"{result['created']} created, {result['updated']} updated"
            )
        except Exception as e:
            logger.warning(
                f"[SchedulerConfig] Failed to ensure core schedules (likely first migrate): {e}"
            )
