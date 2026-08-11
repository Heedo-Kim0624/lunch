import pytest

from recommendations.filters import cuisine_group, filter_foods
from recommendations.models import Food


@pytest.mark.django_db
def test_filter_foods_treats_same_group_as_or_and_different_groups_as_and() -> None:
    korean_rice = Food.objects.create(
        canonical_name="비빔밥",
        family="밥",
        cuisine="한식",
        staple_types=["rice"],
        attributes={"cold": 0.0, "spicy": 0.3},
    )
    japanese_noodle = Food.objects.create(
        canonical_name="탄탄멘",
        family="면",
        cuisine="일식",
        staple_types=["noodle"],
        attributes={"cold": 0.0, "spicy": 0.8},
    )
    cold_japanese_noodle = Food.objects.create(
        canonical_name="냉모밀",
        family="면",
        cuisine="일식",
        staple_types=["noodle"],
        attributes={"cold": 0.9, "spicy": 0.0},
    )

    matches = filter_foods(
        [korean_rice, japanese_noodle, cold_japanese_noodle],
        {
            "temperature": ["hot"],
            "staples": ["rice", "noodle"],
            "cuisines": ["korean", "japanese"],
            "spice": ["spicy", "mild"],
        },
    )

    assert matches == [korean_rice, japanese_noodle]


@pytest.mark.parametrize(
    ("cuisine", "expected"),
    [
        ("한식", "korean"),
        ("중식", "chinese"),
        ("일식", "japanese"),
        ("이탈리아식", "western"),
        ("서양식", "western"),
        ("프랑스식", "western"),
        ("스페인식", "western"),
        ("베트남식", "southeast_asian"),
        ("태국식", "southeast_asian"),
        ("동남아식", "southeast_asian"),
        ("인도네시아식", "southeast_asian"),
        ("말레이시아식", "southeast_asian"),
        ("필리핀식", "southeast_asian"),
        ("인도식", "other"),
        ("퓨전", "other"),
    ],
)
def test_cuisine_group_mapping(cuisine: str, expected: str) -> None:
    assert cuisine_group(cuisine) == expected
