import logging
from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from apps.core.models import Overview, Step, IP, Subdomain, URLResult
from apps.analyze_ai.tasks.planning import propose_next_steps

logger = logging.getLogger(__name__)

@shared_task(name="scheduler.tasks.watchdog_stalled_overviews")
def watchdog_stalled_overviews():
    """
    Watchdog task to identify and recover stalled Overviews.
    1. Overviews in PLANNING for > 15 mins (AI planning might have failed).
    2. Overviews in EXECUTING with no active steps for > 30 mins.
    """
    now = timezone.now()
    summary = {"recovered_planning": 0, "recovered_executing": 0}

    # 1. Recover PLANNING overviews
    # If stuck in PLANNING for too long, it might mean the Celery task failed/lost
    stalled_planning = Overview.objects.filter(
        status="PLANNING",
        updated_at__lt=now - timedelta(minutes=15)
    )
    for ov in stalled_planning:
        logger.warning(f"[Watchdog] Overview#{ov.id} stalled in PLANNING. Re-triggering planning.")
        propose_next_steps.delay(ov.id)
        summary["recovered_planning"] += 1

    # 2. Recover EXECUTING overviews
    # If EXECUTING but no steps are RUNNING or PENDING, then it's finished but status didn't update, 
    # or it failed to trigger next steps.
    stalled_executing = Overview.objects.filter(
        status="EXECUTING",
        updated_at__lt=now - timedelta(minutes=30)
    )
    for ov in stalled_executing:
        # Check if there are any active steps
        active_steps_count = ov.steps.filter(status__in=["PENDING", "RUNNING", "WAITING_FOR_ASYNC"]).count()
        if active_steps_count == 0:
            logger.warning(f"[Watchdog] Overview#{ov.id} stalled in EXECUTING with no active steps. Re-triggering planning.")
            propose_next_steps.delay(ov.id)
            summary["recovered_executing"] += 1

    # 3. Sanitation: Delete orphaned assets
    # These are assets that lost their target (likely due to Target deletion not cascading to M2M correctly or missing FKs)
    summary["deleted_orphans"] = {
        "ips": IP.objects.filter(target__isnull=True).delete()[0],
        "subdomains": Subdomain.objects.filter(target__isnull=True).delete()[0],
        "url_results": URLResult.objects.filter(target__isnull=True).delete()[0],
        "overviews": Overview.objects.filter(target__isnull=True).delete()[0],
    }
    
    if any(summary["deleted_orphans"].values()):
        logger.info(f"[Watchdog] Cleaned up orphaned assets: {summary['deleted_orphans']}")

    return summary
