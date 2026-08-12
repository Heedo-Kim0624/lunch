from __future__ import annotations

import hashlib
import secrets
from collections import Counter
from dataclasses import dataclass
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Count, QuerySet
from django.utils import timezone

from recommendations.models import (
    Food,
    MultiRoom,
    MultiRoomChoice,
    MultiRoomParticipant,
)
from recommendations.multi_serializers import normalize_nickname

ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ROOM_CODE_LENGTH = 10
ROOM_LIFETIME = timedelta(hours=24)
MAX_ROOM_PARTICIPANTS = 20


@dataclass(frozen=True)
class MultiRoomDomainError(Exception):
    code: str
    detail: str
    status_code: int


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_participant_token() -> str:
    return secrets.token_urlsafe(32)


def _new_room_code() -> str:
    return "".join(secrets.choice(ROOM_CODE_ALPHABET) for _ in range(ROOM_CODE_LENGTH))


def _active_room(code: str, *, lock: bool = False) -> MultiRoom:
    queryset = MultiRoom.objects.all()
    if lock:
        queryset = queryset.select_for_update()
    else:
        queryset = queryset.select_related("result_food")
    try:
        room = queryset.get(code=code.upper())
    except MultiRoom.DoesNotExist as error:
        raise MultiRoomDomainError("room_not_found", "공유방을 찾을 수 없어요.", 404) from error
    if room.expires_at <= timezone.now():
        raise MultiRoomDomainError("room_expired", "이 공유방은 만료됐어요.", 410)
    return room


def _participant_for_token(room: MultiRoom, token: str | None) -> MultiRoomParticipant | None:
    if not token:
        return None
    return room.participants.filter(token_digest=token_digest(token)).first()


def require_participant(room: MultiRoom, token: str | None) -> MultiRoomParticipant:
    participant = _participant_for_token(room, token)
    if participant is None:
        raise MultiRoomDomainError(
            "invalid_participant_token", "이 방의 참가자 권한을 확인할 수 없어요.", 403
        )
    return participant


def _vote_rows(room: MultiRoom) -> list[dict[str, int]]:
    return list(
        MultiRoomChoice.objects.filter(
            participant__room=room,
            participant__is_ready=True,
            food__is_active=True,
            food__is_lunch_suitable=True,
        )
        .values("food_id")
        .annotate(votes=Count("participant_id", distinct=True))
        .order_by("food_id")
    )


def _leaders(room: MultiRoom, *, all_ready: bool) -> tuple[list[dict[str, object]], int]:
    if not all_ready:
        return [], 0
    rows = _vote_rows(room)
    max_votes = max((row["votes"] for row in rows), default=0)
    if max_votes < 2:
        return [], max_votes
    leader_ids = [row["food_id"] for row in rows if row["votes"] == max_votes]
    foods = Food.objects.in_bulk(leader_ids)
    return [
        {"id": food_id, "name": foods[food_id].canonical_name, "votes": max_votes}
        for food_id in leader_ids
        if food_id in foods
    ], max_votes


def room_payload(room: MultiRoom, token: str | None = None) -> dict[str, object]:
    participants = list(room.participants.annotate(choice_count=Count("choices")))
    participant_count = len(participants)
    all_ready = participant_count >= 2 and all(person.is_ready for person in participants)
    leaders, max_votes = _leaders(room, all_ready=all_ready)
    can_reroll = room.status == MultiRoom.Status.DRAWN and len(leaders) > 1
    can_draw = (
        all_ready
        and max_votes >= 2
        and (room.status == MultiRoom.Status.WAITING or can_reroll)
    )

    if participant_count < 2:
        blocked_reason = "waiting_for_participants"
    elif not all_ready:
        blocked_reason = "waiting_for_choices"
    elif max_votes < 2:
        blocked_reason = "no_overlap"
    elif room.status == MultiRoom.Status.DRAWN and not can_reroll:
        blocked_reason = "decision_complete"
    else:
        blocked_reason = None

    current_participant = _participant_for_token(room, token)
    result = None
    if room.result_food_id and room.result_food is not None:
        result = {
            "food": {
                "id": room.result_food_id,
                "name": room.result_food.canonical_name,
                "family": room.result_food.family,
                "description": room.result_food.description,
            },
            "votes": room.result_votes,
            "draw_count": room.draw_count,
        }

    return {
        "code": room.code,
        "status": room.status,
        "expires_at": room.expires_at.isoformat(),
        "participant_count": participant_count,
        "participants": [
            {
                "id": person.id,
                "nickname": person.nickname,
                "is_host": person.is_host,
                "is_ready": person.is_ready,
                "choice_count": person.choice_count,
            }
            for person in participants
        ],
        "self": (
            {
                "id": current_participant.id,
                "is_host": current_participant.is_host,
                "is_ready": current_participant.is_ready,
                "choices": [
                    {
                        "id": choice.food_id,
                        "name": choice.food.canonical_name,
                        "family": choice.food.family,
                        "cuisine": choice.food.cuisine,
                    }
                    for choice in current_participant.choices.select_related("food").all()
                ],
            }
            if current_participant
            else None
        ),
        "all_ready": all_ready,
        "can_draw": can_draw,
        "can_reroll": can_reroll,
        "blocked_reason": blocked_reason,
        "leaders": leaders,
        "max_votes": max_votes,
        "result": result,
    }


def create_room(nickname: str) -> tuple[MultiRoom, MultiRoomParticipant, str]:
    for _ in range(8):
        try:
            with transaction.atomic():
                room = MultiRoom.objects.create(
                    code=_new_room_code(), expires_at=timezone.now() + ROOM_LIFETIME
                )
                token = create_participant_token()
                participant = MultiRoomParticipant.objects.create(
                    room=room,
                    nickname=nickname,
                    normalized_nickname=normalize_nickname(nickname),
                    token_digest=token_digest(token),
                    is_host=True,
                )
            return room, participant, token
        except IntegrityError:
            continue
    raise MultiRoomDomainError(
        "room_code_unavailable", "공유방 코드를 만들지 못했어요.", 503
    )


@transaction.atomic
def join_room(code: str, nickname: str) -> tuple[MultiRoom, MultiRoomParticipant, str]:
    room = _active_room(code, lock=True)
    if room.status != MultiRoom.Status.WAITING:
        raise MultiRoomDomainError("room_locked", "이미 추첨을 시작한 방이에요.", 409)
    if room.participants.count() >= MAX_ROOM_PARTICIPANTS:
        raise MultiRoomDomainError("room_full", "이 방은 참가 인원이 가득 찼어요.", 409)
    normalized = normalize_nickname(nickname)
    if room.participants.filter(normalized_nickname=normalized).exists():
        raise MultiRoomDomainError("nickname_taken", "이미 사용 중인 닉네임이에요.", 400)

    token = create_participant_token()
    participant = MultiRoomParticipant.objects.create(
        room=room,
        nickname=nickname,
        normalized_nickname=normalized,
        token_digest=token_digest(token),
    )
    return room, participant, token


@transaction.atomic
def submit_choices(code: str, token: str | None, food_ids: list[int]) -> MultiRoom:
    room = _active_room(code, lock=True)
    if room.status != MultiRoom.Status.WAITING:
        raise MultiRoomDomainError("room_locked", "추첨을 시작해 목록을 바꿀 수 없어요.", 409)
    participant = require_participant(room, token)
    participant = MultiRoomParticipant.objects.select_for_update().get(id=participant.id)
    foods_by_id = Food.objects.filter(
            id__in=food_ids,
            is_active=True,
            is_lunch_suitable=True,
        ).in_bulk()
    if len(foods_by_id) != len(food_ids):
        raise MultiRoomDomainError(
            "invalid_foods", "선택할 수 없는 음식이 포함되어 있어요.", 400
        )

    participant.choices.all().delete()
    MultiRoomChoice.objects.bulk_create(
        [
            MultiRoomChoice(participant=participant, food=foods_by_id[food_id])
            for food_id in food_ids
        ]
    )
    participant.is_ready = True
    participant.save(update_fields=["is_ready", "updated_at"])
    return room


@transaction.atomic
def draw_room(code: str, token: str | None) -> MultiRoom:
    room = _active_room(code, lock=True)
    participant = require_participant(room, token)
    if not participant.is_host:
        raise MultiRoomDomainError("host_only", "방장만 레버를 당길 수 있어요.", 403)

    participants = list(room.participants.all())
    if len(participants) < 2:
        raise MultiRoomDomainError(
            "waiting_for_participants", "두 명 이상 모여야 추첨할 수 있어요.", 409
        )
    if not all(person.is_ready for person in participants):
        raise MultiRoomDomainError(
            "waiting_for_choices", "모든 참가자가 목록을 완료해야 해요.", 409
        )

    votes = Counter(
        MultiRoomChoice.objects.filter(participant__room=room).values_list(
            "food_id", flat=True
        )
    )
    max_votes = max(votes.values(), default=0)
    if max_votes < 2:
        raise MultiRoomDomainError(
            "no_overlap", "서로 겹치는 메뉴가 없어 레버를 당길 수 없어요.", 409
        )
    leaders = sorted(food_id for food_id, count in votes.items() if count == max_votes)
    if room.status == MultiRoom.Status.DRAWN and len(leaders) == 1:
        raise MultiRoomDomainError(
            "decision_complete", "단독 최다 메뉴로 이미 결정됐어요.", 409
        )
    selectable = leaders
    if room.result_food_id in leaders and len(leaders) > 1:
        selectable = [food_id for food_id in leaders if food_id != room.result_food_id]
    selected_id = secrets.choice(selectable)

    room.status = MultiRoom.Status.DRAWN
    room.result_food_id = selected_id
    room.result_votes = max_votes
    room.leading_food_ids = leaders
    room.draw_count += 1
    room.drawn_at = timezone.now()
    room.save(
        update_fields=[
            "status",
            "result_food",
            "result_votes",
            "leading_food_ids",
            "draw_count",
            "drawn_at",
            "updated_at",
        ]
    )
    room.result_food = Food.objects.get(id=selected_id)
    return room


def read_room(code: str) -> MultiRoom:
    return _active_room(code)


def search_foods(query: str) -> QuerySet[Food]:
    foods = Food.objects.filter(is_active=True, is_lunch_suitable=True)
    if query:
        foods = foods.filter(canonical_name__icontains=query)
    return foods.order_by("canonical_name")[:30]
