from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Register all required Celery Beat periodic tasks in the database."

    def handle(self, *args, **options):
        try:
            from apps.scheduler.beat_registry import ensure_core_schedules

            result = ensure_core_schedules()
            for line in result["details"]:
                # 每行已含 "created:" / "updated:" 前綴
                self.stdout.write(f"✅ {line}")

            self.stdout.write(self.style.SUCCESS(
                f"\n🚀 All Celery Beat schedules registered: "
                f"{result['created']} created, {result['updated']} updated, "
                f"{result['skipped']} skipped. "
                f"Run `celery -A c2_core.celery:app beat -l info` to start the scheduler."
            ))

        except ImportError:
            self.stderr.write(self.style.ERROR(
                "django_celery_beat is not installed. "
                "Run: pip install django-celery-beat"
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {e}"))
