from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from core.models import Subdomain, URLResult, TechStack, URLScan, NucleiScan


class Command(BaseCommand):
    help = "Deduplicate Subdomain records with the same name by merging relations and deleting duplicates."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only report duplicates without modifying data.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Optional limit for number of duplicate name groups to process (0 = no limit).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options["limit"]

        dup_names_qs = (
            Subdomain.objects.values("name").annotate(c=Count("id")).filter(c__gt=1)
        )
        total_groups = dup_names_qs.count()
        if limit and limit > 0:
            dup_names_qs = dup_names_qs[:limit]

        self.stdout.write(
            self.style.WARNING(
                f"Found {total_groups} duplicate name groups. Processing {dup_names_qs.count()} groups..."
            )
        )

        processed = 0
        merged_subs = 0

        for row in dup_names_qs:
            name = row["name"]
            subs = list(Subdomain.objects.filter(name=name).order_by("id"))
            keep = subs[0]
            dups = subs[1:]

            self.stdout.write(self.style.NOTICE(f"Merging duplicates for name: {name}"))

            if dry_run:
                self.stdout.write(
                    f"  Would keep ID {keep.id}, remove {[d.id for d in dups]} (count={len(subs)})"
                )
                processed += 1
                merged_subs += len(dups)
                continue

            with transaction.atomic():
                # Merge M2M: Seeds
                for dup in dups:
                    keep.which_seed.add(*dup.which_seed.all())

                # Merge M2M: IPs
                for dup in dups:
                    keep.ips.add(*dup.ips.all())

                # Merge M2M: discovered_by_scans
                for dup in dups:
                    keep.discovered_by_scans.add(*dup.discovered_by_scans.all())

                # M2M: URLResult.related_subdomains
                for dup in dups:
                    related_urls = URLResult.objects.filter(related_subdomains=dup)
                    for url in related_urls:
                        url.related_subdomains.add(keep)
                        url.related_subdomains.remove(dup)

                # FKs: TechStack.subdomain
                for dup in dups:
                    TechStack.objects.filter(subdomain=dup).update(subdomain=keep)

                # FKs: URLScan.target_subdomain
                for dup in dups:
                    URLScan.objects.filter(target_subdomain=dup).update(
                        target_subdomain=keep
                    )

                # FKs: NucleiScan.subdomain_asset
                for dup in dups:
                    NucleiScan.objects.filter(subdomain_asset=dup).update(
                        subdomain_asset=keep
                    )

                # Finally delete duplicates
                for dup in dups:
                    dup.delete()

            processed += 1
            merged_subs += len(dups)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Merged {len(dups)} records into Subdomain ID {keep.id} for name '{name}'"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Processed {processed} name groups, removed {merged_subs} duplicate Subdomain rows."
            )
        )
