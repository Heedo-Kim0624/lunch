from __future__ import annotations

import hashlib
import secrets
from collections import Counter
from dataclasses import dataclass
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from recommendations.models import (
    Food,
    MultiRoom,
    MultiRoomChoice,
    MultiRoomCustomFood,
    MultiRoomParticipant,
)
from recommendations.multi_serializers import (
    normalize_direct_menu_name,
    normalize_nickname,
)

ROOM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ROOM_CODE_LENGTH = 10
ROOM_LIFETIME = timedelta(hours=24)
MAX_ROOM_PARTICIPANTS = 20


@dataclass(frozen=True)
class MultiRoomDomainError(Exception):
    code: str
    detail: str
    status_code: int


@dataclass(frozen=True)
class ChoiceVote:
    key: str
    name: str
    food_id: int | None
    custom_food_id: int | None
    votes: int

    @property
    def is_custom(self) -> bool:
        return self.custom_food_id is not None

    def payload(self) -> dict[str, object]:
        return {
            "id": self.food_id,
            "key": self.key,
            "name": self.name,
            "votes": self.votes,
            "is_custom": self.is_custom,
        }


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
        queryset = queryset.select_related("result_food", "result_custom_food")
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


def _choice_payload(choice: MultiRoomChoice) -> dict[str, object]:
    if choice.food_id and choice.food is not None:
        return {
            "id": choice.food_id,
            "key": f"food:{choice.food_id}",
            "name": choice.food.canonical_name,
            "family": choice.food.family,
            "cuisine": choice.food.cuisine,
            "is_custom": False,
        }
    if choice.custom_food_id and choice.custom_food is not None:
        return {
            "id": None,
            "key": f"custom:{choice.custom_food_id}",
            "name": choice.custom_food.name,
            "family": "직접 입력",
            "cuisine": "사용자 메뉴",
            "is_custom": True,
        }
    raise MultiRoomDomainError("invalid_choice", "올바르지 않은 음식 선택이에요.", 500)


def _vote_rows(room: MultiRoom) -> list[ChoiceVote]:
    choices = MultiRoomChoice.objects.filter(
        participant__room=room,
        participant__is_ready=True,
    ).select_related("food", "custom_food")
    votes: Counter[str] = Counter()
    sources: dict[str, tuple[str, int | None, int | None]] = {}
    for choice in choices:
        if choice.food_id and choice.food is not None:
            if not choice.food.is_active or not choice.food.is_lunch_suitable:
                continue
            key = f"food:{choice.food_id}"
            sources[key] = (choice.food.canonical_name, choice.food_id, None)
        elif choice.custom_food_id and choice.custom_food is not None:
            key = f"custom:{choice.custom_food_id}"
            sources[key] = (choice.custom_food.name, None, choice.custom_food_id)
        else:
            continue
        votes[key] += 1

    return [
        ChoiceVote(
            key=key,
            name=sources[key][0],
            food_id=sources[key][1],
            custom_food_id=sources[key][2],
            votes=count,
        )
        for key, count in sorted(votes.items())
    ]


def _leaders(room: MultiRoom, *, all_ready: bool) -> tuple[list[dict[str, object]], int]:
    if not all_ready:
        return [], 0
    rows = _vote_rows(room)
    max_votes = max((row.votes for row in rows), default=0)
    if max_votes < 2:
        return [], max_votes
    return [row.payload() for row in rows if row.votes == max_votes], max_votes


def room_payload(room: MultiRoom, token: str | None = None) -> dict[str, object]:
    participants = list(room.participants.annotate(choice_count=Count("choices")))
    participant_count = len(participants)
    all_ready = participant_count >= 2 and all(person.is_ready for person in participants)
    leaders, max_votes = _leaders(room, all_ready=all_ready)
    can_reroll = room.status == MultiRoom.Status.DRAWN and len(leaders) > 1
    can_draw = (
        all_ready and max_votes >= 2 and (room.status == MultiRoom.Status.WAITING or can_reroll)
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
                "key": f"food:{room.result_food_id}",
                "name": room.result_food.canonical_name,
                "family": room.result_food.family,
                "cuisine": room.result_food.cuisine,
                "description": room.result_food.description,
                "is_custom": False,
            },
            "votes": room.result_votes,
            "draw_count": room.draw_count,
        }
    elif room.result_custom_food_id and room.result_custom_food is not None:
        result = {
            "food": {
                "id": None,
                "key": f"custom:{room.result_custom_food_id}",
                "name": room.result_custom_food.name,
                "family": "직접 입력",
                "cuisine": "사용자 메뉴",
                "description": "참가자가 직접 입력해 함께 고른 메뉴예요.",
                "is_custom": True,
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
                    _choice_payload(choice)
                    for choice in current_participant.choices.select_related(
                        "food", "custom_food"
                    ).all()
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
    raise MultiRoomDomainError("room_code_unavailable", "공유방 코드를 만들지 못했어요.", 503)


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
def submit_choices(
    code: str,
    token: str | None,
    choice_items: list[dict[str, object]],
) -> MultiRoom:
    room = _active_room(code, lock=True)
    if room.status != MultiRoom.Status.WAITING:
        raise MultiRoomDomainError("room_locked", "추첨을 시작해 목록을 바꿀 수 없어요.", 409)
    participant = require_participant(room, token)
    participant = MultiRoomParticipant.objects.select_for_update().get(id=participant.id)
    food_ids = [int(item["food_id"]) for item in choice_items if "food_id" in item]
    foods_by_id = Food.objects.filter(
        id__in=food_ids,
        is_active=True,
        is_lunch_suitable=True,
    ).in_bulk()
    if len(foods_by_id) != len(food_ids):
        raise MultiRoomDomainError("invalid_foods", "선택할 수 없는 음식이 포함되어 있어요.", 400)

    direct_names = [str(item["custom_name"]) for item in choice_items if "custom_name" in item]
    catalog_query = Q()
    for direct_name in direct_names:
        catalog_query |= Q(canonical_name__iexact=direct_name)
    matching_catalog = (
        Food.objects.filter(is_active=True, is_lunch_suitable=True).filter(catalog_query).all()
        if direct_names
        else []
    )
    catalog_by_name = {
        normalize_direct_menu_name(food.canonical_name): food for food in matching_catalog
    }

    resolved: list[tuple[Food | None, MultiRoomCustomFood | None]] = []
    resolved_keys: set[str] = set()
    for item in choice_items:
        food: Food | None = None
        custom_food: MultiRoomCustomFood | None = None
        if "food_id" in item:
            food = foods_by_id[int(item["food_id"])]
            key = f"food:{food.id}"
        else:
            direct_name = str(item["custom_name"])
            normalized_name = normalize_direct_menu_name(direct_name)
            food = catalog_by_name.get(normalized_name)
            if food is not None:
                key = f"food:{food.id}"
            else:
                custom_food, _ = MultiRoomCustomFood.objects.get_or_create(
                    room=room,
                    normalized_name=normalized_name,
                    defaults={"name": direct_name},
                )
                key = f"custom:{custom_food.id}"
        if key in resolved_keys:
            raise MultiRoomDomainError(
                "duplicate_choices", "같은 음식은 한 번만 선택할 수 있어요.", 400
            )
        resolved_keys.add(key)
        resolved.append((food, custom_food))

    participant.choices.all().delete()
    MultiRoomChoice.objects.bulk_create(
        [
            MultiRoomChoice(
                participant=participant,
                food=food,
                custom_food=custom_food,
            )
            for food, custom_food in resolved
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

    vote_rows = _vote_rows(room)
    max_votes = max((row.votes for row in vote_rows), default=0)
    if max_votes < 2:
        raise MultiRoomDomainError(
            "no_overlap", "서로 겹치는 메뉴가 없어 레버를 당길 수 없어요.", 409
        )
    leaders = [row for row in vote_rows if row.votes == max_votes]
    if room.status == MultiRoom.Status.DRAWN and len(leaders) == 1:
        raise MultiRoomDomainError("decision_complete", "단독 최다 메뉴로 이미 결정됐어요.", 409)
    selectable = leaders
    previous_key = (
        f"food:{room.result_food_id}"
        if room.result_food_id
        else (f"custom:{room.result_custom_food_id}" if room.result_custom_food_id else None)
    )
    if previous_key and len(leaders) > 1:
        selectable = [leader for leader in leaders if leader.key != previous_key]
    selected = secrets.choice(selectable)

    room.status = MultiRoom.Status.DRAWN
    room.result_food_id = selected.food_id
    room.result_custom_food_id = selected.custom_food_id
    room.result_votes = max_votes
    room.leading_food_ids = [leader.food_id for leader in leaders if leader.food_id is not None]
    room.leading_choice_keys = [leader.key for leader in leaders]
    room.draw_count += 1
    room.drawn_at = timezone.now()
    room.save(
        update_fields=[
            "status",
            "result_food",
            "result_custom_food",
            "result_votes",
            "leading_food_ids",
            "leading_choice_keys",
            "draw_count",
            "drawn_at",
            "updated_at",
        ]
    )
    room.result_food = (
        Food.objects.get(id=selected.food_id) if selected.food_id is not None else None
    )
    room.result_custom_food = (
        MultiRoomCustomFood.objects.get(id=selected.custom_food_id)
        if selected.custom_food_id is not None
        else None
    )
    return room


def read_room(code: str) -> MultiRoom:
    return _active_room(code)


def search_foods(query: str) -> QuerySet[Food]:
    foods = Food.objects.filter(is_active=True, is_lunch_suitable=True)
    if query:
        foods = foods.filter(canonical_name__icontains=query)
    return foods.order_by("canonical_name")[:30]
