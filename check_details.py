import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'c2_core.settings')
django.setup()

from apps.core.models import Overview, Step
from apps.core.models.analyze.AttackVector import CommandTemplate

overviews = Overview.objects.all().order_by('-id')[:2]
for o in overviews:
    print(f"Overview ID: {o.id}, Status: {o.status}, Risk: {o.risk_score}")
    print(f"Plan: {o.plan}")
    steps = Step.objects.filter(overview=o).order_by('-id')[:10]
    for s in steps:
        note = s.note_detail.content if hasattr(s, 'note_detail') else 'No note'
        print(f"  Step ID: {s.id}, Status: {s.status}, Note: {note}")

