from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from recommendations.models import Food
from recommendations.seed_data import ATTRIBUTE_NAMES, FOODS, LEGACY_NAME_ALIASES

__all__ = ["ATTRIBUTE_NAMES", "FOODS"]


class Command(BaseCommand):
    help = "Create or update the curated lunch food catalog."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        self._normalize_legacy_names()
        catalog_names = [str(item["canonical_name"]) for item in FOODS]
        deactivated = Food.objects.filter(is_active=True).exclude(
            canonical_name__in=catalog_names
        ).update(is_active=False)

        existing_by_name = {
            food.canonical_name: food
            for food in Food.objects.filter(canonical_name__in=catalog_names)
        }
        to_create: list[Food] = []
        to_update: list[Food] = []
        unchanged = 0
        update_fields = [
            "family",
            "description",
            "cuisine",
            "meal_style",
            "staple_types",
            "attributes",
            "is_lunch_suitable",
            "is_active",
            "updated_at",
        ]
        now = timezone.now()
        for item in FOODS:
            name = str(item["canonical_name"])
            defaults = {key: value for key, value in item.items() if key != "canonical_name"}
            food = existing_by_name.get(name)
            if food is None:
                to_create.append(Food(canonical_name=name, **defaults))
                continue
            if all(getattr(food, field) == value for field, value in defaults.items()):
                unchanged += 1
                continue
            for field, value in defaults.items():
                setattr(food, field, value)
            food.updated_at = now
            to_update.append(food)

        Food.objects.bulk_create(to_create, batch_size=250)
        Food.objects.bulk_update(to_update, update_fields, batch_size=250)
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded foods: {len(to_create)} created, {len(to_update)} updated, "
                f"{unchanged} unchanged, {deactivated} deactivated, {len(FOODS)} total"
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
