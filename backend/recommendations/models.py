import uuid

from django.db import models
from django.db.models import Q


class Food(models.Model):
    canonical_name = models.CharField(max_length=120, unique=True)
    family = models.CharField(max_length=120, db_index=True)
    description = models.TextField(blank=True)
    cuisine = models.CharField(max_length=80, default="한식")
    meal_style = models.CharField(max_length=80, default="식사")
    staple_types = models.JSONField(default=list)
    attributes = models.JSONField(default=dict)
    is_lunch_suitable = models.BooleanField(default=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["canonical_name"]

    def __str__(self) -> str:
        return self.canonical_name


class RecommendationSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anonymous_id = models.CharField(max_length=64, db_index=True)
    context = models.JSONField(default=dict)
    policy_version = models.CharField(max_length=40)
    candidate_count = models.PositiveIntegerField()
    candidate_snapshot = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self) -> str:
        return f"{self.anonymous_id}:{self.policy_version}:{self.id}"


class RecommendationExposure(models.Model):
    session = models.ForeignKey(
        RecommendationSession,
        on_delete=models.CASCADE,
        related_name="exposures",
    )
    food = models.ForeignKey(Food, on_delete=models.PROTECT, related_name="exposures")
    rank = models.PositiveSmallIntegerField(default=1)
    total_score = models.FloatField()
    score_breakdown = models.JSONField(default=dict)
    selection_probability = models.FloatField()
    reason = models.CharField(max_length=240)
    shown_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self) -> str:
        return f"{self.session_id}:{self.food_id}"


class UserFoodEvent(models.Model):
    class EventType(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Accepted"
        ATE = "ATE", "Ate"
        REJECTED = "REJECTED", "Rejected"
        REROLLED = "REROLLED", "Rerolled"
        FAVORITED = "FAVORITED", "Favorited"
        DISLIKED = "DISLIKED", "Disliked"

    anonymous_id = models.CharField(max_length=64, db_index=True)
    food = models.ForeignKey(Food, on_delete=models.PROTECT, related_name="user_events")
    exposure = models.ForeignKey(
        RecommendationExposure,
        on_delete=models.PROTECT,
        related_name="events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=16, choices=EventType.choices, db_index=True)
    event_time = models.DateTimeField(auto_now_add=True, db_index=True)
    context = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=["anonymous_id", "-event_time"]),
            models.Index(fields=["anonymous_id", "food", "-event_time"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["exposure", "event_type"],
                condition=models.Q(exposure__isnull=False),
                name="unique_exposure_event_type",
            )
        ]

    def __str__(self) -> str:
        return f"{self.anonymous_id}:{self.event_type}:{self.food_id}"


class MultiRoom(models.Model):
    class Status(models.TextChoices):
        WAITING = "WAITING", "Waiting"
        DRAWN = "DRAWN", "Drawn"

    code = models.CharField(max_length=10, unique=True)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.WAITING,
        db_index=True,
    )
    result_food = models.ForeignKey(
        Food,
        on_delete=models.PROTECT,
        related_name="multi_room_results",
        null=True,
        blank=True,
    )
    result_votes = models.PositiveSmallIntegerField(default=0)
    leading_food_ids = models.JSONField(default=list)
    draw_count = models.PositiveIntegerField(default=0)
    drawn_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code


class MultiRoomParticipant(models.Model):
    room = models.ForeignKey(
        MultiRoom,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    nickname = models.CharField(max_length=20)
    normalized_nickname = models.CharField(max_length=20)
    token_digest = models.CharField(max_length=64, unique=True)
    is_host = models.BooleanField(default=False)
    is_ready = models.BooleanField(default=False, db_index=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["joined_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["room", "normalized_nickname"],
                name="unique_multi_room_nickname",
            ),
            models.UniqueConstraint(
                fields=["room"],
                condition=Q(is_host=True),
                name="unique_multi_room_host",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.room.code}:{self.nickname}"


class MultiRoomChoice(models.Model):
    participant = models.ForeignKey(
        MultiRoomParticipant,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    food = models.ForeignKey(
        Food,
        on_delete=models.PROTECT,
        related_name="multi_room_choices",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["participant", "food"],
                name="unique_multi_participant_food",
            )
        ]

    def __str__(self) -> str:
        return f"{self.participant_id}:{self.food_id}"
