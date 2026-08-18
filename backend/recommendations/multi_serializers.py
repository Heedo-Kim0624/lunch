import re
import unicodedata

from rest_framework import serializers

NICKNAME_PATTERN = re.compile(r"^[0-9A-Za-z가-힣 _-]+$")
DIRECT_MENU_PUNCTUATION = frozenset(" &+()/',.·_-")


def clean_nickname(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.strip().split())


def normalize_nickname(value: str) -> str:
    return clean_nickname(value).casefold()


def clean_direct_menu_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    cleaned = " ".join(normalized.strip().split())
    if not 1 <= len(cleaned) <= 40:
        raise serializers.ValidationError("직접 입력 메뉴는 1~40자로 적어 주세요.")
    if any(
        not unicodedata.category(character).startswith(("L", "N"))
        and character not in DIRECT_MENU_PUNCTUATION
        for character in cleaned
    ):
        raise serializers.ValidationError(
            "메뉴 이름에는 문자, 숫자, 공백과 일반적인 메뉴 구두점만 사용할 수 있어요."
        )
    return cleaned


def normalize_direct_menu_name(value: str) -> str:
    return clean_direct_menu_name(value).casefold()


class MultiNicknameSerializer(serializers.Serializer):
    nickname = serializers.CharField(min_length=2, max_length=20, trim_whitespace=True)

    def validate_nickname(self, value: str) -> str:
        cleaned = clean_nickname(value)
        if len(cleaned) < 2 or not NICKNAME_PATTERN.fullmatch(cleaned):
            raise serializers.ValidationError(
                "닉네임은 한글, 영문, 숫자, 공백, 밑줄과 하이픈으로 2~20자만 입력해 주세요."
            )
        return cleaned


class MultiChoiceItemSerializer(serializers.Serializer):
    food_id = serializers.IntegerField(min_value=1, required=False)
    custom_name = serializers.CharField(
        min_length=1,
        max_length=40,
        required=False,
        trim_whitespace=True,
    )

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        has_food = "food_id" in attrs
        has_custom = "custom_name" in attrs
        if has_food == has_custom:
            raise serializers.ValidationError(
                "카탈로그 음식 또는 직접 입력 메뉴 중 하나만 보내 주세요."
            )
        if has_custom:
            attrs["custom_name"] = clean_direct_menu_name(str(attrs["custom_name"]))
        return attrs


class MultiChoicesSerializer(serializers.Serializer):
    food_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
        max_length=12,
        allow_empty=False,
        required=False,
    )
    choices = serializers.ListField(
        child=MultiChoiceItemSerializer(),
        min_length=1,
        max_length=12,
        allow_empty=False,
        required=False,
    )

    def validate(self, attrs: dict[str, object]) -> dict[str, object]:
        has_food_ids = "food_ids" in attrs
        has_choices = "choices" in attrs
        if has_food_ids == has_choices:
            raise serializers.ValidationError("food_ids 또는 choices 중 하나만 보내 주세요.")

        choice_items = (
            [{"food_id": food_id} for food_id in attrs["food_ids"]]
            if has_food_ids
            else list(attrs["choices"])
        )
        unique_keys = {
            (
                f"food:{item['food_id']}"
                if "food_id" in item
                else f"custom:{normalize_direct_menu_name(str(item['custom_name']))}"
            )
            for item in choice_items
        }
        if len(unique_keys) != len(choice_items):
            raise serializers.ValidationError("같은 음식은 한 번만 선택할 수 있어요.")
        attrs["choices"] = choice_items
        return attrs


class FoodSearchSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, default="", max_length=40, trim_whitespace=True)
