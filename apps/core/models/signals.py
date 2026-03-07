# core/models/signals.py
# Automated signal handlers for model synchronization

from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .domain import Subdomain
from .network import IP


# 1. Subdomain -> Seed: 自動繼承 Target
@receiver(m2m_changed, sender=Subdomain.which_seed.through)
def sync_subdomain_target(sender, instance, action, **kwargs):
    """
    Automatically sync subdomain target when seed relationships change.
    When a subdomain is associated with a seed, inherit the seed's target.
    """
    if action == "post_add":
        if not instance.target_id:
            first_seed = instance.which_seed.first()
            if first_seed:
                # Use update to prevent triggering save() loop
                Subdomain.objects.filter(pk=instance.pk).update(
                    target=first_seed.target
                )


# 2. IP -> Seed: 自動繼承 Target
@receiver(m2m_changed, sender=IP.which_seed.through)
def sync_ip_target(sender, instance, action, **kwargs):
    """
    Automatically sync IP target when seed relationships change.
    When an IP is associated with a seed, inherit the seed's target.
    """
    if action == "post_add":
        if not instance.target_id:
            first_seed = instance.which_seed.first()
            if first_seed:
                IP.objects.filter(pk=instance.pk).update(target=first_seed.target)
