from django.core.management.base import BaseCommand
from django.db import transaction

from recommendations.models import Food
from recommendations.seed_data import ATTRIBUTE_NAMES, FOODS, LEGACY_NAME_ALIASES

__all__ = ["ATTRIBUTE_NAMES", "FOODS"]


class Command(BaseCommand):
    help = "Create or update the curated lunch food catalog."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        self._normalize_legacy_names()
        created = 0
        updated = 0
        for item in FOODS:
            _, was_created = Food.objects.update_or_create(
                canonical_name=item["canonical_name"],
                defaults={key: value for key, value in item.items() if key != "canonical_name"},
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded foods: {created} created, {updated} updated, {len(FOODS)} total"
            )
        )

    @staticmethod
    def _normalize_legacy_names() -> None:
        for legacy_name, canonical_name in LEGACY_NAME_ALIASES.items():
            legacy = Food.objects.filter(canonical_name=legacy_name).first()
            if legacy is None:
                continue
            if Food.objects.filter(canonical_name=canonical_name).exists():
                legacy.is_active = False
                legacy.save(update_fields=["is_active", "updated_at"])
                continue
            legacy.canonical_name = canonical_name
            legacy.save(update_fields=["canonical_name", "updated_at"])
