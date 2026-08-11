import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Food",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("canonical_name", models.CharField(max_length=120, unique=True)),
                ("family", models.CharField(db_index=True, max_length=120)),
                ("description", models.TextField(blank=True)),
                ("cuisine", models.CharField(default="한식", max_length=80)),
                ("meal_style", models.CharField(default="식사", max_length=80)),
                ("attributes", models.JSONField(default=dict)),
                ("is_lunch_suitable", models.BooleanField(db_index=True, default=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["canonical_name"]},
        ),
        migrations.CreateModel(
            name="RecommendationSession",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("anonymous_id", models.CharField(db_index=True, max_length=64)),
                ("context", models.JSONField(default=dict)),
                ("policy_version", models.CharField(max_length=40)),
                ("candidate_count", models.PositiveIntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name="RecommendationExposure",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("rank", models.PositiveSmallIntegerField(default=1)),
                ("total_score", models.FloatField()),
                ("score_breakdown", models.JSONField(default=dict)),
                ("selection_probability", models.FloatField()),
                ("reason", models.CharField(max_length=240)),
                ("shown_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "food",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="exposures",
                        to="recommendations.food",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exposures",
                        to="recommendations.recommendationsession",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserFoodEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("anonymous_id", models.CharField(db_index=True, max_length=64)),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("ACCEPTED", "Accepted"),
                            ("ATE", "Ate"),
                            ("REJECTED", "Rejected"),
                            ("REROLLED", "Rerolled"),
                            ("FAVORITED", "Favorited"),
                            ("DISLIKED", "Disliked"),
                        ],
                        db_index=True,
                        max_length=16,
                    ),
                ),
                ("event_time", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("context", models.JSONField(default=dict)),
                (
                    "exposure",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="events",
                        to="recommendations.recommendationexposure",
                    ),
                ),
                (
                    "food",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="user_events",
                        to="recommendations.food",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="userfoodevent",
            index=models.Index(
                fields=["anonymous_id", "-event_time"],
                name="recommendat_anonymo_b09921_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="userfoodevent",
            index=models.Index(
                fields=["anonymous_id", "food", "-event_time"],
                name="recommendat_anonymo_3b2ba4_idx",
            ),
        ),
    ]

