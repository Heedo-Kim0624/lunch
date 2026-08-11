from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256

ATTRIBUTE_NAMES = (
    "spicy",
    "broth",
    "light",
    "protein",
    "adventurous",
    "cold",
    "familiar",
    "popularity",
)
STAPLE_TYPES = {"rice", "bread", "noodle"}

SPICY_TERMS = (
    "매운",
    "얼큰",
    "김치",
    "마라",
    "짬뽕",
    "떡볶이",
    "라즈지",
    "어향",
    "사천",
    "후난",
    "산초",
    "고추",
    "비콜",
    "빈달루",
    "체티나드",
    "베르베레",
    "도로그왓",
    "저크",
    "라브",
    "남톡",
    "카오소이",
    "아마트리치아나",
    "디아볼라",
)
VERY_SPICY_TERMS = ("마라", "라즈지", "수이주", "빈달루", "비콜", "매운")
MILD_TERMS = ("맑은", "간장", "백절", "죽", "오차즈케", "차즈케")
RICH_TERMS = (
    "튀김",
    "프라이",
    "가라아게",
    "커틀릿",
    "크림",
    "치즈",
    "버터",
    "카츠",
    "슈니첼",
    "딥디시",
    "웰링턴",
    "코르동블루",
)
LIGHT_TERMS = ("샐러드", "포케", "현미", "채소", "야채", "두부", "생선", "회정식")
BROTH_TERMS = (
    "탕면",
    "락사",
    "모힝가",
    "카오소이",
    "꾸웨이띠아오",
    "옌타포",
    "소토",
    "박소",
    "보코",
    "포솔레",
    "시니강",
    "부야베스",
)
HIGH_PROTEIN_TERMS = (
    "소고기",
    "돼지",
    "닭",
    "치킨",
    "오리",
    "양고기",
    "스테이크",
    "갈비",
    "연어",
    "참치",
    "장어",
    "새우",
    "문어",
    "낙지",
    "오징어",
    "생선",
    "대구",
    "고등어",
    "갈치",
    "굴",
    "게",
    "차슈",
    "포크",
    "비프",
)


def _lines(value: str) -> tuple[str, ...]:
    return tuple(line.strip() for line in value.strip().splitlines() if line.strip())


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)


def _focus(name: str, suffixes: tuple[str, ...]) -> str:
    for suffix in sorted(suffixes, key=len, reverse=True):
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return name


def _attributes(
    name: str,
    profile: tuple[float, ...],
    *,
    is_cold: bool,
    overrides: Mapping[str, float] | None,
) -> dict[str, float]:
    values = dict(zip(ATTRIBUTE_NAMES, profile, strict=True))
    digest = sha256(name.encode("utf-8")).digest()

    # Small stable adjustments avoid fake family-wide clones while preserving
    # the human-curated profile and semantic thresholds below.
    for offset, attribute in enumerate(("light", "adventurous", "familiar", "popularity")):
        values[attribute] += ((digest[offset] % 3) - 1) * 0.05

    if any(term in name for term in MILD_TERMS):
        values["spicy"] = min(values["spicy"], 0.2)
    if any(term in name for term in SPICY_TERMS):
        values["spicy"] = max(values["spicy"], 0.7)
    if any(term in name for term in VERY_SPICY_TERMS):
        values["spicy"] = max(values["spicy"], 0.85)
    if any(term in name for term in RICH_TERMS):
        values["light"] = min(values["light"], 0.3)
    if any(term in name for term in LIGHT_TERMS):
        values["light"] = max(values["light"], 0.7)
    if any(term in name for term in HIGH_PROTEIN_TERMS):
        values["protein"] = max(values["protein"], 0.7)
    if name.endswith(("탕", "국", "찌개", "전골", "나베", "수프")) or any(
        term in name for term in BROTH_TERMS
    ):
        values["broth"] = max(values["broth"], 0.75)
    if is_cold:
        values["cold"] = max(values["cold"], 0.75)
    if overrides:
        values.update(overrides)

    return {name: _clamp(value) for name, value in values.items()}


def _make_group(
    names: str,
    *,
    family: str,
    cuisine: str,
    meal_style: str,
    description: str,
    profile: tuple[float, ...],
    staple_types: tuple[str, ...] = (),
    suffixes: tuple[str, ...] = (),
    cold_names: tuple[str, ...] = (),
    all_cold: bool = False,
    staple_overrides: Mapping[str, tuple[str, ...]] | None = None,
    attribute_overrides: Mapping[str, Mapping[str, float]] | None = None,
) -> tuple[dict[str, object], ...]:
    if len(profile) != len(ATTRIBUTE_NAMES):
        raise ValueError(f"Expanded profile must contain eight values: {family}")
    if not set(staple_types) <= STAPLE_TYPES:
        raise ValueError(f"Invalid staple type in {family}")

    cold_set = set(cold_names)
    staples_by_name = staple_overrides or {}
    attributes_by_name = attribute_overrides or {}
    foods: list[dict[str, object]] = []
    for name in _lines(names):
        item_staples = staples_by_name.get(name, staple_types)
        if not set(item_staples) <= STAPLE_TYPES:
            raise ValueError(f"Invalid staple type for {name}")
        focus = _focus(name, suffixes)
        foods.append(
            {
                "canonical_name": name,
                "family": family,
                "cuisine": cuisine,
                "meal_style": meal_style,
                "staple_types": list(item_staples),
                "description": description.format(name=name, focus=focus),
                "attributes": _attributes(
                    name,
                    profile,
                    is_cold=all_cold or name in cold_set,
                    overrides=attributes_by_name.get(name),
                ),
                "is_lunch_suitable": True,
                "is_active": True,
            }
        )
    return tuple(foods)


KOREAN_FOODS = (
    *_make_group(
        """
        닭한마리
        연포탕
        낙곱새전골
        곱창전골
        두부전골
        불낙전골
        소고기버섯전골
        들깨버섯탕
        우렁된장찌개
        냉이된장찌개
        달래된장찌개
        강된장찌개
        해물순두부
        들깨순두부
        차돌순두부
        명란순두부
        대구매운탕
        우럭매운탕
        메기매운탕
        민물새우탕
        조기매운탕
        아귀탕
        복국
        재첩국
        다슬기국
        올갱이국
        홍합탕
        어묵탕
        소고기전골
        낙지전골
        """,
        family="향토 찌개·탕",
        cuisine="한식",
        meal_style="국물 식사",
        description="{focus} 재료를 넉넉한 국물에 끓여 밥과 함께 즐기는 {name}",
        profile=(0.35, 0.9, 0.4, 0.65, 0.3, 0.0, 0.78, 0.74),
        staple_types=("rice",),
        suffixes=("된장찌개", "순두부", "매운탕", "전골", "찌개", "탕", "국"),
    ),
    *_make_group(
        """
        내장국밥
        따로국밥
        선지국밥
        수구레국밥
        장어국밥
        오징어국밥
        김치콩나물국밥
        얼큰소고기국밥
        우거지국밥
        순두부국밥
        뼈다귀국밥
        황태국밥
        매생이국밥
        굴해장국
        북엇국
        시래깃국
        아욱국
        근대국
        토란국
        오징어무국
        """,
        family="국밥·해장국",
        cuisine="한식",
        meal_style="국물 식사",
        description="{focus} 건더기와 따뜻한 국물을 밥에 곁들여 속을 든든하게 채우는 {name}",
        profile=(0.3, 0.9, 0.45, 0.65, 0.25, 0.0, 0.85, 0.76),
        staple_types=("rice",),
        suffixes=("해장국", "국밥", "국"),
    ),
    *_make_group(
        """
        전복솥밥
        굴솥밥
        버섯솥밥
        소고기솥밥
        장어솥밥
        연어솥밥
        명란솥밥
        문어솥밥
        꼬막솥밥
        가리비솥밥
        대게살솥밥
        단호박솥밥
        고구마솥밥
        무솥밥
        시래기솥밥
        톳솥밥
        취나물솥밥
        표고버섯밥
        콩나물밥
        무밥
        가지밥
        부추비빔밥
        산채비빔밥
        새싹비빔밥
        장조림버터밥
        간장계란밥
        소보로덮밥
        소시지덮밥
        두부덮밥
        버섯덮밥
        """,
        family="솥밥·덮밥",
        cuisine="한식",
        meal_style="한 그릇",
        description="{focus}의 향과 식감을 밥에 고루 배게 해 한 그릇으로 완성한 {name}",
        profile=(0.2, 0.08, 0.55, 0.55, 0.28, 0.05, 0.82, 0.76),
        staple_types=("rice",),
        suffixes=("비빔밥", "솥밥", "덮밥", "버터밥", "밥"),
    ),
    *_make_group(
        """
        우렁쌈밥
        제육쌈밥
        오리쌈밥
        불고기쌈밥
        고등어쌈밥
        갈치쌈밥
        보리밥정식
        청국장보리밥
        산채정식
        나물정식
        두부정식
        순두부정식
        간장게장정식
        양념게장정식
        꼬막정식
        굴비정식
        보쌈정식
        족발정식
        제육정식
        불고기정식
        닭갈비정식
        오징어볶음정식
        낙지볶음정식
        생선구이정식
        백반정식
        """,
        family="쌈밥·한식 정식",
        cuisine="한식",
        meal_style="반찬 식사",
        description="{focus}을 중심으로 밥과 여러 반찬을 균형 있게 차려내는 {name}",
        profile=(0.35, 0.12, 0.45, 0.68, 0.2, 0.0, 0.88, 0.78),
        staple_types=("rice",),
        suffixes=("보리밥정식", "정식", "쌈밥", "보리밥"),
    ),
    *_make_group(
        """
        멸치국수
        고기국수
        고기비빔국수
        골뱅이비빔국수
        김치비빔국수
        들기름막국수
        명태회막국수
        동치미막국수
        들기름메밀국수
        비빔메밀국수
        온메밀국수
        육전냉면
        코다리냉면
        물밀면
        비빔밀면
        온면
        닭한마리칼국수
        매생이칼국수
        팥옹심이
        감자옹심이
        옹심이칼국수
        얼큰수제비
        해물수제비
        김치수제비
        감자수제비
        """,
        family="향토 면·옹심이",
        cuisine="한식",
        meal_style="면",
        description="{focus}의 맛을 면이나 반죽에 살려 육수 또는 양념과 즐기는 {name}",
        profile=(0.35, 0.48, 0.58, 0.4, 0.24, 0.1, 0.82, 0.75),
        staple_types=("noodle",),
        suffixes=(
            "비빔국수",
            "메밀국수",
            "막국수",
            "칼국수",
            "수제비",
            "옹심이",
            "냉면",
            "밀면",
            "국수",
            "면",
        ),
        cold_names=(
            "고기비빔국수",
            "골뱅이비빔국수",
            "김치비빔국수",
            "들기름막국수",
            "명태회막국수",
            "동치미막국수",
            "들기름메밀국수",
            "비빔메밀국수",
            "육전냉면",
            "코다리냉면",
            "물밀면",
            "비빔밀면",
        ),
    ),
    *_make_group(
        """
        치즈라볶이
        매운라볶이
        마라떡볶이
        크림떡볶이
        차돌떡볶이
        통오징어떡볶이
        기름떡볶이
        궁중떡볶이
        쌀떡볶이
        밀떡볶이
        야채김밥
        매운어묵김밥
        소고기김밥
        계란김밥
        묵은지김밥
        키토김밥
        비빔만두
        군만두
        물만두
        떡꼬치
        """,
        family="분식 확장",
        cuisine="한식",
        meal_style="간편식",
        description="{name} 특유의 재료와 양념을 간편하게 즐길 수 있게 구성한 분식 메뉴",
        profile=(0.52, 0.16, 0.3, 0.4, 0.12, 0.0, 0.9, 0.8),
        staple_overrides={
            "치즈라볶이": ("noodle",),
            "매운라볶이": ("noodle",),
            "야채김밥": ("rice",),
            "매운어묵김밥": ("rice",),
            "소고기김밥": ("rice",),
            "계란김밥": ("rice",),
            "묵은지김밥": ("rice",),
        },
    ),
    *_make_group(
        """
        해물파전
        김치전
        감자전
        부추전
        녹두전
        동그랑땡
        육전
        굴전
        동태전
        두부전
        배추전
        메밀전
        꼬치전
        모둠전
        """,
        family="전·부침",
        cuisine="한식",
        meal_style="공유 식사",
        description="{focus} 재료를 반죽이나 달걀옷과 노릇하게 부쳐낸 {name}",
        profile=(0.22, 0.02, 0.34, 0.52, 0.2, 0.0, 0.84, 0.68),
        suffixes=("파전", "전"),
    ),
    *_make_group(
        """
        전복죽
        소고기죽
        야채죽
        참치죽
        닭죽
        낙지김치죽
        불낙죽
        버섯굴죽
        삼계죽
        단호박죽
        팥죽
        흑임자죽
        새우죽
        게살죽
        매생이굴죽
        """,
        family="죽",
        cuisine="한식",
        meal_style="가벼운 한 그릇",
        description="{focus}을 잘게 손질해 쌀과 부드럽게 끓여낸 따뜻한 {name}",
        profile=(0.1, 0.45, 0.68, 0.45, 0.16, 0.0, 0.86, 0.68),
        staple_types=("rice",),
        suffixes=("죽",),
    ),
    *_make_group(
        """
        갈치조림
        고등어조림
        코다리조림
        가자미조림
        병어조림
        아귀찜
        해물찜
        꽃게찜
        꼬막무침
        골뱅이무침
        오징어숙회
        문어숙회
        낙지볶음
        주꾸미볶음
        갑오징어볶음
        """,
        family="생선·해산물 식사",
        cuisine="한식",
        meal_style="반찬 식사",
        description="{focus}의 식감을 살려 조리하고 밥과 먹기 좋은 양념을 더한 {name}",
        profile=(0.48, 0.14, 0.42, 0.76, 0.3, 0.0, 0.78, 0.72),
        staple_types=("rice",),
        suffixes=("조림", "무침", "숙회", "볶음", "찜"),
    ),
    *_make_group(
        """
        닭불고기
        닭목살구이
        닭발볶음
        돼지두루치기
        김치두루치기
        소고기두루치기
        매운갈비찜
        소갈비찜
        돼지갈비찜
        수육정식
        오징어보쌈
        낙지보쌈
        """,
        family="고기 구이·찜",
        cuisine="한식",
        meal_style="반찬 식사",
        description="{focus}을 구우거나 볶고 양념을 충분히 배게 해 밥과 차린 {name}",
        profile=(0.46, 0.1, 0.3, 0.85, 0.24, 0.0, 0.82, 0.76),
        staple_types=("rice",),
        suffixes=("두루치기", "불고기", "목살구이", "갈비찜", "정식", "보쌈", "볶음", "찜"),
    ),
)


JAPANESE_FOODS = (
    *_make_group(
        """
        부타동
        카이센동
        네기토로동
        아나고동
        스테키동
        야키토리동
        가라아게동
        사바동
        명란아보카도동
        소보로동
        돈테키정식
        사바시오야키정식
        연어구이정식
        호케구이정식
        치킨난반정식
        가라아게정식
        쇼가야키정식
        규카츠정식
        함박정식
        에비후라이정식
        """,
        family="일식 덮밥·정식 확장",
        cuisine="일식",
        meal_style="한 그릇",
        description="{focus}을 일본식 소스와 조리해 밥 또는 정식 반찬으로 구성한 {name}",
        profile=(0.2, 0.08, 0.4, 0.72, 0.36, 0.05, 0.68, 0.7),
        staple_types=("rice",),
        suffixes=("시오야키정식", "구이정식", "난반정식", "후라이정식", "정식", "동"),
        cold_names=("카이센동", "네기토로동"),
    ),
    *_make_group(
        """
        타누키우동
        카케우동
        와카메우동
        카마타마우동
        나베야키우동
        야키우동
        자루우동
        히야시우동
        냉우동
        오로시소바
        자루소바
        카모소바
        텐자루소바
        니신소바
        마제소바
        아부라소바
        히야시추카
        나가사키짬뽕
        """,
        family="우동·소바 확장",
        cuisine="일식",
        meal_style="면",
        description="{focus}의 육수나 소스를 면에 맞춰 조합한 일본식 {name}",
        profile=(0.24, 0.5, 0.56, 0.42, 0.38, 0.08, 0.65, 0.68),
        staple_types=("noodle",),
        suffixes=("우동", "소바", "추카", "짬뽕"),
        cold_names=(
            "자루우동",
            "히야시우동",
            "냉우동",
            "오로시소바",
            "자루소바",
            "텐자루소바",
            "히야시추카",
        ),
    ),
    *_make_group(
        """
        광어초밥
        도미초밥
        장어초밥
        새우초밥
        계란초밥
        문어초밥
        관자초밥
        고등어초밥
        성게알초밥
        연어알초밥
        참치회정식
        연어회정식
        광어회정식
        사시미정식
        치라시스시
        """,
        family="초밥·사시미 확장",
        cuisine="일식",
        meal_style="가벼운 한 그릇",
        description="{focus}을 신선하게 손질해 초밥이나 회 구성으로 담아낸 {name}",
        profile=(0.08, 0.02, 0.7, 0.66, 0.48, 0.75, 0.58, 0.66),
        staple_types=("rice",),
        suffixes=("회정식", "초밥", "정식", "스시"),
        all_cold=True,
    ),
    *_make_group(
        """
        돈가스카레
        치킨카레
        함박카레
        새우튀김카레
        야채카레
        드라이카레
        오므라이스
        하야시오므라이스
        카레오므라이스
        명란오므라이스
        """,
        family="일식 카레·오므라이스",
        cuisine="일식",
        meal_style="한 그릇",
        description="{focus} 재료를 일본식 카레나 부드러운 달걀밥과 조합한 {name}",
        profile=(0.18, 0.08, 0.38, 0.6, 0.34, 0.0, 0.7, 0.72),
        staple_types=("rice",),
        suffixes=("오므라이스", "카레"),
    ),
    *_make_group(
        """
        스키야키
        일본식샤브샤브
        모츠나베
        요세나베
        밀푀유나베
        창코나베
        오뎅나베
        부타쇼가야키
        사바미소니
        부타카쿠니
        야키토리정식
        데리야키치킨정식
        데리야키연어정식
        호르몬야키
        징기스칸
        """,
        family="일식 나베·구이",
        cuisine="일식",
        meal_style="국물·반찬 식사",
        description="{name} 특유의 일본식 간장·된장 양념과 조리법으로 따뜻하게 차린 메뉴",
        profile=(0.2, 0.42, 0.38, 0.72, 0.45, 0.0, 0.58, 0.65),
        staple_types=("rice",),
        staple_overrides={"일본식샤브샤브": ("rice", "noodle")},
    ),
    *_make_group(
        """
        타마고산도
        가츠산도
        후르츠산도
        야키소바빵
        멘치카츠산도
        에비카츠산도
        """,
        family="일식 산도",
        cuisine="일식",
        meal_style="간편식",
        description="{focus} 속재료를 부드러운 식빵 사이에 채워 간편하게 먹는 {name}",
        profile=(0.12, 0.02, 0.36, 0.55, 0.4, 0.15, 0.62, 0.66),
        staple_types=("bread",),
        suffixes=("산도", "빵"),
        cold_names=("타마고산도", "후르츠산도"),
    ),
    *_make_group(
        """
        오니기리정식
        명란오니기리
        연어오니기리
        참치마요오니기리
        오차즈케
        연어차즈케
        명란차즈케
        """,
        family="오니기리·차즈케",
        cuisine="일식",
        meal_style="간편식",
        description="{focus}을 밥에 넣거나 차를 부어 담백하게 마무리한 {name}",
        profile=(0.08, 0.35, 0.62, 0.5, 0.36, 0.05, 0.66, 0.62),
        staple_types=("rice",),
        suffixes=("오니기리정식", "오니기리", "차즈케", "정식"),
    ),
)


CHINESE_FOODS = (
    *_make_group(
        """
        차슈덮밥
        동파육덮밥
        어향가지덮밥
        토마토계란덮밥
        청경채소고기덮밥
        깐풍새우덮밥
        유린육덮밥
        몽골리안비프덮밥
        사천닭고기덮밥
        팔보채덮밥
        양저우볶음밥
        차슈볶음밥
        XO볶음밥
        마늘볶음밥
        파인애플볶음밥
        해물볶음밥
        소고기볶음밥
        피망소고기덮밥
        """,
        family="중화 덮밥·볶음밥 확장",
        cuisine="중식",
        meal_style="한 그릇",
        description="{focus} 재료를 센 불에 볶아 밥과 함께 감칠맛 있게 담아낸 {name}",
        profile=(0.4, 0.06, 0.34, 0.64, 0.45, 0.0, 0.6, 0.68),
        staple_types=("rice",),
        suffixes=("볶음밥", "덮밥"),
    ),
    *_make_group(
        """
        사천짜장면
        유니짜장
        물짜장
        고추짜장
        해물쟁반짜장
        굴짬뽕
        차돌짬뽕
        고기짬뽕
        크림짬뽕
        마라짬뽕
        산라탕면
        도삭면
        마라비빔면
        중국식냉면
        상하이볶음면
        완탕면
        차슈탕면
        계란볶음면
        """,
        family="중화면 확장",
        cuisine="중식",
        meal_style="면",
        description="{focus}의 소스나 육수를 탄력 있는 면과 조합해 풍미를 살린 {name}",
        profile=(0.48, 0.42, 0.32, 0.52, 0.5, 0.0, 0.58, 0.68),
        staple_types=("noodle",),
        suffixes=("쟁반짜장", "비빔면", "볶음면", "짬뽕", "짜장면", "짜장", "탕면", "면"),
        cold_names=("마라비빔면", "중국식냉면"),
    ),
    *_make_group(
        """
        홍유만두
        새우완탕
        부추물만두
        게살샤오롱바오
        """,
        family="중식 만두·완탕",
        cuisine="중식",
        meal_style="간편식",
        description="{focus} 소를 얇은 피에 감싸 찌거나 삶아 육즙을 살린 {name}",
        profile=(0.3, 0.2, 0.42, 0.58, 0.52, 0.0, 0.52, 0.62),
        suffixes=("샤오롱바오", "물만두", "만두", "완탕"),
    ),
    *_make_group(
        """
        수이주위
        수이주러우피엔
        라즈지
        위샹러우쓰
        어향가지
        회과육
        마파가지
        고추기름소고기
        사천식생선찜
        사천식두부볶음
        마라롱샤
        마라닭날개
        후난식돼지고기볶음
        후난식생선찜
        농가소초육
        산초소고기볶음
        """,
        family="사천·후난 요리",
        cuisine="중식",
        meal_style="반찬 식사",
        description="{name} 특유의 고추·산초 향과 볶음 또는 찜 조리법을 밥과 즐기는 중식 메뉴",
        profile=(0.82, 0.18, 0.24, 0.72, 0.68, 0.0, 0.4, 0.58),
        staple_types=("rice",),
    ),
    *_make_group(
        """
        차슈
        크리스피포크
        백절계
        간장치킨
        소금새우
        XO소스관자볶음
        광둥식찐생선
        흑후추소고기
        레몬치킨
        새우두부찜
        청경채굴소스볶음
        광둥식오리구이
        """,
        family="광둥식 구이·찜",
        cuisine="중식",
        meal_style="반찬 식사",
        description="{name}의 재료를 광둥식으로 굽거나 쪄 깔끔한 감칠맛을 낸 밥반찬 메뉴",
        profile=(0.22, 0.08, 0.4, 0.76, 0.55, 0.0, 0.48, 0.62),
        staple_types=("rice",),
    ),
    *_make_group(
        """
        양꼬치정식
        경장육슬
        지삼선
        쯔란양고기
        대반계
        꿍바오지딩
        토마토소고기탕
        양고기탕
        """,
        family="중국 북방 요리",
        cuisine="중식",
        meal_style="반찬 식사",
        description="{name}에 향신료와 북방식 조리법을 더해 밥과 든든하게 먹는 메뉴",
        profile=(0.46, 0.2, 0.3, 0.76, 0.7, 0.0, 0.38, 0.55),
        staple_types=("rice",),
        staple_overrides={"경장육슬": ("bread",)},
    ),
    *_make_group(
        """
        산시유포면
        란저우비빔면
        """,
        family="중국 북방 면",
        cuisine="중식",
        meal_style="면",
        description="{focus} 지역의 향신 기름과 쫄깃한 면 식감을 중심으로 만든 {name}",
        profile=(0.55, 0.22, 0.38, 0.5, 0.72, 0.0, 0.34, 0.52),
        staple_types=("noodle",),
        suffixes=("비빔면", "면"),
    ),
    *_make_group(
        """
        우육탕면
        대만식비빔면
        홍콩식완탕면
        """,
        family="대만·홍콩 면",
        cuisine="중식",
        meal_style="면",
        description="{name}의 현지식 육수나 소스를 면과 조합한 대만·홍콩식 메뉴",
        profile=(0.38, 0.5, 0.4, 0.58, 0.62, 0.0, 0.42, 0.58),
        staple_types=("noodle",),
        cold_names=("대만식비빔면",),
    ),
    *_make_group(
        """
        루러우판
        지파이덮밥
        대만식소시지덮밥
        홍콩식로스트덕라이스
        """,
        family="대만·홍콩 밥",
        cuisine="중식",
        meal_style="한 그릇",
        description="{name}의 고기와 소스를 밥 위에 올려 현지식 한 그릇으로 낸 메뉴",
        profile=(0.3, 0.08, 0.32, 0.7, 0.58, 0.0, 0.45, 0.62),
        staple_types=("rice",),
    ),
    *_make_group(
        """
        마카오식포크찹번
        홍콩식에그샌드위치
        대만식샌드위치
        """,
        family="중화권 샌드위치",
        cuisine="중식",
        meal_style="간편식",
        description="{name}의 속재료를 빵 사이에 채워 현지식으로 간편하게 먹는 메뉴",
        profile=(0.18, 0.02, 0.38, 0.58, 0.62, 0.12, 0.44, 0.58),
        staple_types=("bread",),
    ),
)


WESTERN_FOODS = (
    *_make_group(
        """
        아마트리치아나
        푸타네스카
        카치오에페페
        트러플크림파스타
        명란크림파스타
        새우로제파스타
        치킨알프레도
        페투치네알프레도
        라비올리
        토르텔리니
        뇨키
        바질크림뇨키
        토마토뇨키
        라자냐볼로네제
        카넬로니
        오레키에테
        링귀네봉골레
        해산물링귀네
        버섯탈리아텔레
        라구파파르델레
        """,
        family="이탈리아 면·뇨키 확장",
        cuisine="이탈리아식",
        meal_style="면",
        description=(
            "{name}에 맞는 면이나 반죽과 소스를 조합해 "
            "풍미를 선명하게 살린 이탈리아식 메뉴"
        ),
        profile=(0.18, 0.04, 0.34, 0.5, 0.42, 0.0, 0.62, 0.68),
        staple_types=("noodle",),
    ),
    *_make_group(
        """
        콰트로포르마지피자
        디아볼라피자
        프로슈토피자
        버섯트러플피자
        쉬림프피자
        고구마피자
        베이컨체더피자
        화이트피자
        시카고딥디시피자
        칼초네
        포카치아샌드
        이탈리안플랫브레드
        """,
        family="피자·플랫브레드 확장",
        cuisine="이탈리아식",
        meal_style="공유 식사",
        description="{focus} 토핑이나 속재료를 발효 반죽과 구워 고소하게 완성한 {name}",
        profile=(0.22, 0.01, 0.24, 0.5, 0.36, 0.0, 0.7, 0.72),
        staple_types=("bread",),
        suffixes=("플랫브레드", "피자", "샌드"),
    ),
    *_make_group(
        """
        베이컨버거
        더블치즈버거
        머쉬룸버거
        불고기치즈버거
        핫치킨버거
        피쉬버거
        풀드포크버거
        비건버거
        루벤샌드위치
        필리치즈스테이크
        파스트라미샌드위치
        터키클럽샌드위치
        치킨페스토파니니
        카프레제파니니
        참치멜트
        햄치즈크루아상
        로스트비프샌드위치
        미트볼서브
        """,
        family="버거·샌드위치 확장",
        cuisine="서양식",
        meal_style="간편식",
        description="{name}의 속재료와 소스를 빵 사이에 풍성하게 채운 서양식 간편 메뉴",
        profile=(0.2, 0.01, 0.28, 0.68, 0.38, 0.05, 0.72, 0.75),
        staple_types=("bread",),
    ),
    *_make_group(
        """
        니스와즈샐러드
        카프레제샐러드
        쿠스쿠스샐러드
        퀴노아샐러드
        렌틸샐러드
        새우아보카도샐러드
        스테이크샐러드
        구운채소샐러드
        케일치킨샐러드
        오르조샐러드
        지중해식곡물볼
        치킨퀴노아볼
        연어곡물볼
        로스트비프볼
        """,
        family="서양식 샐러드·곡물볼",
        cuisine="서양식",
        meal_style="가벼운 한 그릇",
        description="{name}의 채소·곡물·단백질을 산뜻한 드레싱과 균형 있게 담은 메뉴",
        profile=(0.12, 0.01, 0.78, 0.58, 0.38, 0.7, 0.58, 0.62),
        all_cold=True,
        staple_overrides={"오르조샐러드": ("noodle",)},
    ),
    *_make_group(
        """
        비프웰링턴
        치킨코르동블루
        포크슈니첼
        치킨슈니첼
        송아지커틀릿
        로스트치킨
        로스트포크
        비프브리스킷
        풀드포크플레이트
        그릴드연어
        레몬버터대구
        허브구이농어
        양갈비스테이크
        포크찹스테이크
        미트로프
        소시지매시
        치킨팟파이
        셰퍼드파이
        """,
        family="서양식 메인 확장",
        cuisine="서양식",
        meal_style="플레이트",
        description="{name}의 주재료를 굽거나 오븐에 익혀 소스와 곁들인 서양식 메인 요리",
        profile=(0.14, 0.06, 0.28, 0.82, 0.42, 0.0, 0.58, 0.65),
    ),
    *_make_group(
        """
        뵈프부르기뇽
        코코뱅
        라따뚜이
        키슈로렌
        크로크무슈
        크로크마담
        프렌치어니언수프
        부야베스
        오리콩피
        스테이크프리트
        갈레트
        잠봉크레프
        """,
        family="프랑스 요리",
        cuisine="프랑스식",
        meal_style="플레이트",
        description=(
            "{name}의 전통 재료와 조리법을 살려 "
            "소스와 식감을 정교하게 구성한 프랑스식 메뉴"
        ),
        profile=(0.12, 0.22, 0.38, 0.66, 0.62, 0.0, 0.38, 0.58),
        staple_overrides={
            "키슈로렌": ("bread",),
            "크로크무슈": ("bread",),
            "크로크마담": ("bread",),
            "갈레트": ("bread",),
            "잠봉크레프": ("bread",),
        },
    ),
    *_make_group(
        """
        해산물빠에야
        먹물빠에야
        치킨빠에야
        발렌시아빠에야
        감바스알아히요
        스페니시오믈렛
        알본디가스
        뽈뽀아라가예가
        바스크치킨
        초리조감자볶음
        스페인식문어샐러드
        보카디요
        """,
        family="스페인 요리",
        cuisine="스페인식",
        meal_style="한 그릇·플레이트",
        description="{name}의 쌀·해산물·육류를 올리브유와 향신료로 선명하게 조리한 스페인식 메뉴",
        profile=(0.24, 0.08, 0.4, 0.66, 0.65, 0.0, 0.38, 0.58),
        staple_overrides={
            "해산물빠에야": ("rice",),
            "먹물빠에야": ("rice",),
            "치킨빠에야": ("rice",),
            "발렌시아빠에야": ("rice",),
            "보카디요": ("bread",),
        },
        cold_names=("스페인식문어샐러드",),
    ),
)


SOUTHEAST_ASIAN_FOODS = (
    *_make_group(
        """
        반깐꾸어
        분리우
        분목
        까오러우
        미꽝
        후띠우
        보코
        보룩락
        짜조
        고이꾸온
        껌가
        껌땀
        반꾸온
        반봇록
        """,
        family="베트남 요리 확장",
        cuisine="베트남식",
        meal_style="면·한 그릇",
        description="{name}의 쌀면·허브·고기 재료를 베트남식 육수나 소스와 조화시킨 메뉴",
        profile=(0.3, 0.38, 0.62, 0.58, 0.58, 0.08, 0.45, 0.6),
        staple_overrides={
            "반깐꾸어": ("noodle",),
            "분리우": ("noodle",),
            "분목": ("noodle",),
            "까오러우": ("noodle",),
            "미꽝": ("noodle",),
            "후띠우": ("noodle",),
            "보코": ("bread",),
            "보룩락": ("rice",),
            "껌가": ("rice",),
            "껌땀": ("rice",),
        },
        cold_names=("고이꾸온",),
    ),
    *_make_group(
        """
        카오소이
        꾸웨이띠아오
        옌타포
        랏나
        팟운센
        쏨땀
        라브무
        남톡무
        카오카무
        카오무댕
        카오클룩까피
        무삥과찹쌀밥
        호이라이팟
        뿌팟퐁커리덮밥
        """,
        family="태국 요리 확장",
        cuisine="태국식",
        meal_style="면·한 그릇",
        description="{name}에 태국식 허브와 새콤·달콤·매콤한 양념을 균형 있게 더한 메뉴",
        profile=(0.62, 0.26, 0.48, 0.58, 0.68, 0.04, 0.38, 0.58),
        staple_overrides={
            "카오소이": ("noodle",),
            "꾸웨이띠아오": ("noodle",),
            "옌타포": ("noodle",),
            "랏나": ("noodle",),
            "팟운센": ("noodle",),
            "카오카무": ("rice",),
            "카오무댕": ("rice",),
            "카오클룩까피": ("rice",),
            "무삥과찹쌀밥": ("rice",),
            "뿌팟퐁커리덮밥": ("rice",),
        },
        cold_names=("쏨땀", "라브무", "남톡무"),
    ),
    *_make_group(
        """
        아얌고렝
        아얌바카르
        소토아얌
        소토베타위
        가도가도
        소또미
        나시우둑
        나시짬뿌르
        나시파당
        이칸바카르
        박소
        """,
        family="인도네시아 요리",
        cuisine="인도네시아식",
        meal_style="한 그릇",
        description="{name}의 닭·생선·채소에 인도네시아식 향신료와 진한 소스를 더한 메뉴",
        profile=(0.48, 0.28, 0.44, 0.62, 0.72, 0.02, 0.3, 0.52),
        staple_overrides={
            "아얌고렝": ("rice",),
            "아얌바카르": ("rice",),
            "소토아얌": ("rice",),
            "소토베타위": ("rice",),
            "소또미": ("noodle",),
            "나시우둑": ("rice",),
            "나시짬뿌르": ("rice",),
            "나시파당": ("rice",),
            "이칸바카르": ("rice",),
        },
        cold_names=("가도가도",),
    ),
    *_make_group(
        """
        호키엔미
        차퀘이테오
        완탄미
        미시암
        미레부스
        나시르막
        나시칸다르
        치킨사테
        피시헤드커리
        카야토스트세트
        로티차나이
        페낭아삼락사
        """,
        family="말레이시아·싱가포르 요리",
        cuisine="말레이시아식",
        meal_style="면·한 그릇",
        description="{name}에 말레이·중화·인도계 향신료와 코코넛 풍미를 조합한 메뉴",
        profile=(0.5, 0.3, 0.4, 0.58, 0.72, 0.02, 0.3, 0.54),
        staple_overrides={
            "호키엔미": ("noodle",),
            "차퀘이테오": ("noodle",),
            "완탄미": ("noodle",),
            "미시암": ("noodle",),
            "미레부스": ("noodle",),
            "나시르막": ("rice",),
            "나시칸다르": ("rice",),
            "치킨사테": ("rice",),
            "피시헤드커리": ("rice",),
            "카야토스트세트": ("bread",),
            "로티차나이": ("bread",),
            "페낭아삼락사": ("noodle",),
        },
    ),
    *_make_group(
        """
        치킨아도보
        포크아도보
        시니강
        카레카레
        비콜익스프레스
        레촌카왈리
        판싯칸톤
        판싯비혼
        아로스칼도
        탑실로그
        """,
        family="필리핀 요리",
        cuisine="필리핀식",
        meal_style="한 그릇",
        description="{name}의 고기·면·밥을 새콤짭짤한 필리핀식 양념으로 조리한 메뉴",
        profile=(0.38, 0.3, 0.4, 0.68, 0.75, 0.0, 0.25, 0.5),
        staple_types=("rice",),
        staple_overrides={"판싯칸톤": ("noodle",), "판싯비혼": ("noodle",)},
    ),
    *_make_group(
        """
        모힝가
        샨누들
        오노카욱쉐
        라프토
        라오스카오삐약센
        라프무
        캄보디아쌀국수
        아목트레이
        """,
        family="미얀마·라오스·캄보디아 요리",
        cuisine="동남아식",
        meal_style="면·한 그릇",
        description="{name}의 쌀면·허브·생선 또는 고기를 현지식 향신료로 완성한 동남아 메뉴",
        profile=(0.45, 0.36, 0.52, 0.58, 0.8, 0.03, 0.2, 0.46),
        staple_overrides={
            "모힝가": ("noodle",),
            "샨누들": ("noodle",),
            "오노카욱쉐": ("noodle",),
            "라오스카오삐약센": ("noodle",),
            "캄보디아쌀국수": ("noodle",),
            "아목트레이": ("rice",),
        },
        cold_names=("라프토", "라프무"),
    ),
)


OTHER_FOODS = (
    *_make_group(
        """
        로간조쉬
        코르마커리
        빈달루치킨
        체티나드치킨
        고안피시커리
        차나마살라
        알루고비
        말라이코프타
        파니르티카마살라
        달마크니
        라지마커리
        마살라도사
        라바도사
        우타팜
        이들리삼바
        """,
        family="인도 요리 확장",
        cuisine="인도식",
        meal_style="커리·한 그릇",
        description="{name}에 인도식 향신료와 채소·고기·콩을 층층이 조합한 메뉴",
        profile=(0.58, 0.2, 0.42, 0.6, 0.74, 0.0, 0.32, 0.55),
        staple_types=("rice",),
        staple_overrides={
            "마살라도사": ("bread",),
            "라바도사": ("bread",),
            "우타팜": ("bread",),
            "이들리삼바": (),
        },
    ),
    *_make_group(
        """
        스리랑카치킨커리
        코투로티
        호퍼와커리
        """,
        family="스리랑카 요리",
        cuisine="스리랑카식",
        meal_style="커리·한 그릇",
        description="{name}에 코코넛과 향신료, 로티를 활용해 진한 풍미를 낸 스리랑카식 메뉴",
        profile=(0.62, 0.18, 0.38, 0.62, 0.82, 0.0, 0.2, 0.48),
        staple_overrides={
            "스리랑카치킨커리": ("rice",),
            "코투로티": ("bread",),
            "호퍼와커리": ("bread",),
        },
    ),
    *_make_group(
        """
        치킨쉬시케밥
        아다나케밥
        이스켄데르케밥
        되네르케밥
        터키식미트볼
        이맘바이을드
        므나멘
        라흐마준
        피데
        무자다라
        마클루바
        만사프
        치킨카브사
        양고기카브사
        팔라펠랩
        샤와르마라이스
        """,
        family="중동·터키 요리 확장",
        cuisine="중동식",
        meal_style="플레이트",
        description="{name}의 고기·콩·채소를 중동식 향신료와 빵 또는 밥에 곁들인 메뉴",
        profile=(0.35, 0.08, 0.48, 0.7, 0.72, 0.0, 0.3, 0.54),
        staple_overrides={
            "치킨쉬시케밥": ("rice", "bread"),
            "아다나케밥": ("rice", "bread"),
            "이스켄데르케밥": ("bread",),
            "되네르케밥": ("bread",),
            "라흐마준": ("bread",),
            "피데": ("bread",),
            "무자다라": ("rice",),
            "마클루바": ("rice",),
            "만사프": ("rice",),
            "치킨카브사": ("rice",),
            "양고기카브사": ("rice",),
            "팔라펠랩": ("bread",),
            "샤와르마라이스": ("rice",),
        },
    ),
    *_make_group(
        """
        알파스토르타코
        카르니타스타코
        비리아타코
        새우타코
        바르바코아타코
        치미창가
        브렉퍼스트부리토
        치킨엔칠라다
        비프엔칠라다
        몰레치킨
        포솔레
        소파데토르티야
        아로스콘폴로
        카르네아사다
        칠라킬레스
        우에보스란체로스
        타말
        멕시칸토르타
        """,
        family="멕시코 요리 확장",
        cuisine="멕시코식",
        meal_style="한 그릇·간편식",
        description="{name}의 고기·콩·살사·옥수수 반죽을 멕시코식으로 조합한 메뉴",
        profile=(0.52, 0.08, 0.38, 0.68, 0.68, 0.0, 0.42, 0.62),
        staple_overrides={
            "알파스토르타코": ("bread",),
            "카르니타스타코": ("bread",),
            "비리아타코": ("bread",),
            "새우타코": ("bread",),
            "바르바코아타코": ("bread",),
            "치미창가": ("bread",),
            "브렉퍼스트부리토": ("rice", "bread"),
            "치킨엔칠라다": ("bread",),
            "비프엔칠라다": ("bread",),
            "아로스콘폴로": ("rice",),
            "카르네아사다": ("bread",),
            "멕시칸토르타": ("bread",),
        },
    ),
    *_make_group(
        """
        불고기타코
        김치퀘사디아
        제육부리토
        닭갈비부리토볼
        연어아보카도포케
        참치아보카도포케
        새우포케
        소고기포케
        두부현미볼
        닭가슴살현미볼
        연어현미볼
        매운참치라이스볼
        데리야키치킨볼
        지중해식치킨볼
        """,
        family="퓨전 타코·포케·볼",
        cuisine="퓨전",
        meal_style="가벼운 한 그릇",
        description="{name}의 한식·아시아식 재료를 타코·포케·라이스볼 형태로 재구성한 퓨전 메뉴",
        profile=(0.38, 0.02, 0.62, 0.66, 0.58, 0.18, 0.55, 0.65),
        staple_types=("rice",),
        staple_overrides={
            "불고기타코": ("bread",),
            "김치퀘사디아": ("bread",),
            "제육부리토": ("rice", "bread"),
        },
        cold_names=(
            "연어아보카도포케",
            "참치아보카도포케",
            "새우포케",
            "소고기포케",
            "두부현미볼",
            "닭가슴살현미볼",
            "연어현미볼",
        ),
    ),
    *_make_group(
        """
        플로프
        라그만
        만티
        샤슬릭
        보르시
        비프스트로가노프
        치킨키이우
        굴라시
        피에로기
        우즈베크삼사
        """,
        family="중앙아시아·동유럽 요리",
        cuisine="중앙아시아식",
        meal_style="한 그릇·플레이트",
        description="{name}의 곡물·고기·반죽을 중앙아시아와 동유럽식 향신료로 든든하게 조리한 메뉴",
        profile=(0.28, 0.28, 0.34, 0.7, 0.8, 0.0, 0.18, 0.46),
        staple_overrides={
            "플로프": ("rice",),
            "라그만": ("noodle",),
            "비프스트로가노프": ("rice",),
            "굴라시": ("rice",),
            "우즈베크삼사": ("bread",),
        },
    ),
    *_make_group(
        """
        모로코치킨타진
        양고기타진
        쿠스쿠스치킨
        졸로프라이스
        치킨야사
        에티오피아도로그왓
        베르베레치킨
        남아공보보티
        이집트코샤리
        튀니지식샥슈카
        """,
        family="아프리카 요리",
        cuisine="아프리카식",
        meal_style="한 그릇·플레이트",
        description="{name}의 곡물·고기·콩에 북아프리카와 사하라 이남의 향신료를 더한 메뉴",
        profile=(0.52, 0.22, 0.42, 0.66, 0.86, 0.0, 0.14, 0.42),
        staple_overrides={
            "졸로프라이스": ("rice",),
            "치킨야사": ("rice",),
            "에티오피아도로그왓": ("bread",),
            "베르베레치킨": ("bread",),
            "남아공보보티": ("rice",),
            "이집트코샤리": ("rice", "noodle"),
            "튀니지식샥슈카": ("bread",),
        },
    ),
    *_make_group(
        """
        쿠바노샌드위치
        쿠바식로스트포크
        로파비에하
        페루식로모살타도
        아히데가이나
        페루식세비체
        브라질식페이조아다
        모케카
        자메이카저크치킨
        자메이카커리치킨
        아르헨티나밀라네사
        엠파나다
        """,
        family="라틴아메리카·카리브 요리",
        cuisine="라틴아메리카식",
        meal_style="한 그릇·플레이트",
        description="{name}의 고기·해산물·콩을 라틴아메리카와 카리브식 소스로 조리한 메뉴",
        profile=(0.42, 0.2, 0.4, 0.72, 0.8, 0.0, 0.2, 0.5),
        staple_types=("rice",),
        staple_overrides={
            "쿠바노샌드위치": ("bread",),
            "아르헨티나밀라네사": (),
            "엠파나다": ("bread",),
        },
        cold_names=("페루식세비체",),
    ),
)


EXPANDED_FOODS: tuple[dict[str, object], ...] = (
    *KOREAN_FOODS,
    *JAPANESE_FOODS,
    *CHINESE_FOODS,
    *WESTERN_FOODS,
    *SOUTHEAST_ASIAN_FOODS,
    *OTHER_FOODS,
)
