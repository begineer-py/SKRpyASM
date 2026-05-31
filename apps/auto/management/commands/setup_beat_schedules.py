from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Register all required Celery Beat periodic tasks in the database."

    def handle(self, *args, **options):
        try:
            from django_celery_beat.models import PeriodicTask, IntervalSchedule

            # 建立 30 分鐘排程 (資料預處理)
            preprocess_schedule, _ = IntervalSchedule.objects.get_or_create(
                every=30,
                period=IntervalSchedule.MINUTES,
            )

            # 建立 15 分鐘排程 (自動執行計畫)
            execute_schedule, _ = IntervalSchedule.objects.get_or_create(
                every=15,
                period=IntervalSchedule.MINUTES,
            )

            # 建立/更新 preprocess_data 任務
            preprocess_task, created = PeriodicTask.objects.update_or_create(
                name="[Auto] Data Pre-processing (Initial AI Analysis)",
                defaults={
                    "task": "apps.auto.tasks.preprocess_data",
                    "interval": preprocess_schedule,
                    "enabled": True,
                },
            )
            status = "✅ Created" if created else "🔄 Updated"
            self.stdout.write(f"{status}: preprocess_data → every 30 minutes")

            # 建立/更新 auto_execute_plan 任務
            execute_task, created = PeriodicTask.objects.update_or_create(
                name="[Auto] Autonomous Plan Execution (Layer 3 AutomationAgent)",
                defaults={
                    "task": "apps.auto.tasks.auto_execute_plan",
                    "interval": execute_schedule,
                    "enabled": True,
                },
            )
            status = "✅ Created" if created else "🔄 Updated"
            self.stdout.write(f"{status}: auto_execute_plan → every 15 minutes")

            # ─── 技能驗證任務 (每 30 分鐘) ───
            verify_task, created = PeriodicTask.objects.update_or_create(
                name="[Auto] Skill Verification (Periodic Testing)",
                defaults={
                    "task": "apps.auto.tasks.verify_skills_periodic",
                    "interval": preprocess_schedule,
                    "enabled": True,
                },
            )
            status = "✅ Created" if created else "🔄 Updated"
            self.stdout.write(f"{status}: verify_skills_periodic → every 30 minutes")

            # ─── 技能合併評估 (每 30 分鐘) ───
            merge_task, created = PeriodicTask.objects.update_or_create(
                name="[Auto] Skill Merge Evaluation",
                defaults={
                    "task": "apps.auto.tasks.evaluate_skill_merges",
                    "interval": preprocess_schedule,
                    "enabled": True,
                },
            )
            status = "✅ Created" if created else "🔄 Updated"
            self.stdout.write(f"{status}: evaluate_skill_merges → every 30 minutes")

            self.stdout.write(self.style.SUCCESS(
                "\n🚀 All Celery Beat schedules have been registered. "
                "Run `celery -A c2_core.celery:app beat -l info` to start the scheduler."
            ))

        except ImportError:
            self.stderr.write(self.style.ERROR(
                "django_celery_beat is not installed. "
                "Run: pip install django-celery-beat"
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {e}"))
