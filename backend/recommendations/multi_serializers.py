import re
import unicodedata

from rest_framework import serializers

NICKNAME_PATTERN = re.compile(r"^[0-9A-Za-z가-힣 _-]+$")


def clean_nickname(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.strip().split())


def normalize_nickname(value: str) -> str:
    return clean_nickname(value).casefold()


class MultiNicknameSerializer(serializers.Serializer):
    nickname = serializers.CharField(min_length=2, max_length=20, trim_whitespace=True)

    def validate_nickname(self, value: str) -> str:
        cleaned = clean_nickname(value)
        if len(cleaned) < 2 or not NICKNAME_PATTERN.fullmatch(cleaned):
            raise serializers.ValidationError(
                "닉네임은 한글, 영문, 숫자, 공백, 밑줄과 하이픈으로 2~20자만 입력해 주세요."
            )
        return cleaned


class MultiChoicesSerializer(serializers.Serializer):
    food_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
        max_length=12,
        allow_empty=False,
    )

    def validate_food_ids(self, values: list[int]) -> list[int]:
        unique_values = list(dict.fromkeys(values))
        if len(unique_values) != len(values):
            raise serializers.ValidationError("같은 음식은 한 번만 선택할 수 있어요.")
        return unique_values


class FoodSearchSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, default="", max_length=40, trim_whitespace=True)
