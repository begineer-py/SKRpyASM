import logging
from celery import shared_task
from apps.core.models import IP, Subdomain, URLResult, Overview

logger = logging.getLogger(__name__)


@shared_task(name="scheduler.tasks.cleanup_orphaned_assets")
def cleanup_orphaned_assets():
    """Periodic cleanup of orphaned assets (not linked to any Target)."""
    summary = {
        "ips": IP.objects.filter(target__isnull=True).delete()[0],
        "subdomains": Subdomain.objects.filter(target__isnull=True).delete()[0],
        "url_results": URLResult.objects.filter(target__isnull=True).delete()[0],
        "overviews": Overview.objects.filter(target__isnull=True).delete()[0],
    }
    if any(summary.values()):
        logger.info(f"[Cleanup] Removed orphaned assets: {summary}")
    return summary
