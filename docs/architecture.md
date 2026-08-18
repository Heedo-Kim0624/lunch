# Architecture — First Vertical Slice

## High-level Design

```text
Nuxt 4 web client
  ├─ Single / Multi mode tabs
  ├─ register / login / account state
  ├─ single filter popup / lever / ticket / feedback
  ├─ shared-room join / food chooser / participant reels / host lever
  └─ privacy-safe food relationship graph
          │ HTTP JSON
          ▼
Django REST API
  ├─ token authentication
  ├─ recommendation orchestration
  ├─ content + collaborative + context scoring
  ├─ repetition penalty
  ├─ softmax exploration
  └─ polling-compatible shared-room voting service
          │ Django ORM
          ▼
SQLite local default / Neon PostgreSQL production
  ├─ users + auth tokens
  ├─ foods
  ├─ recommendation sessions
  ├─ recommendation exposures
  └─ user food events
```

## Repository Layout

```text
frontend/                 Nuxt application
backend/                  Django project and recommendation domain
scripts/                  Windows setup and quality-gate entry points
docs/                     product, architecture, decisions, and progress
```

## Recommendation Pipeline

```text
active lunch foods
→ temperature + staple + cuisine + spice hard filters
→ preference score from decayed explicit events
→ item-item collaborative score from 5+ verified accounts
→ weather/temperature context score
→ novelty and popularity
→ recent exact-food repetition penalty
→ randomized tie rotation
→ one candidate per food family before any family gets a second
→ 24-item diverse candidate pool
→ softmax sample within that pool
→ immutable session and exposure log
```

The `rules-v4` score is explainable and versioned: 45% personal attribute preference, 15% collaborative affinity, 15% context, 10% novelty, and 15% popularity before repetition penalties. With no qualified shared history, the collaborative term stays neutral.

## API Contracts

### Shared lunch rooms

```text
GET  /api/v1/foods?q={query}
POST /api/v1/multi/rooms
POST /api/v1/multi/rooms/{code}/join
GET  /api/v1/multi/rooms/{code}
PUT  /api/v1/multi/rooms/{code}/choices
POST /api/v1/multi/rooms/{code}/draw
```

방 생성과 입장은 한 번만 표시되는 참가자 토큰을 반환한다. 이후 쓰기 요청은 `X-Multi-Token` 헤더를 사용하고 DB에는 SHA-256 해시만 저장한다. 방 코드는 엔트로피가 충분한 위치 식별자일 뿐 권한 비밀값은 아니다. 생성, 입장, 검색, 목록 저장과 추첨에는 각각 요청 제한을 적용한다.

Multi 선택은 큐레이션된 `Food` 또는 방 범위 `MultiRoomCustomFood` 중 하나를 참조한다. 직접 입력 이름은 NFKC·공백·대소문자를 정규화하고 방 안에서 공유해 같은 입력이 같은 투표 키를 사용하게 하며, 추천 카탈로그에는 섞지 않는다. 프런트엔드는 공통 URL 함수로 API 경로를 결합하고 오래된 검색 응답을 무시하며, 검색 실패 중에도 직접 추가를 유지한다.

방 조회는 참가자 닉네임, 방장·완료 상태, 선택 개수, 집계 최다 후보와 현재 추첨 결과를 반환하며 토큰은 직렬화하지 않는다. 첫 추첨 뒤에는 목록과 입장을 잠근다. 방장 추첨은 데이터베이스 트랜잭션과 행 잠금 안에서 완료 상태와 표 수를 다시 계산한다.

프런트엔드는 3초 간격으로 방 상태를 갱신한다. 영구 WebSocket 서버를 두지 않아 기존 Vercel + Neon 무료 구성을 유지한다.

### Register and authenticate

`POST /api/v1/auth/register` creates a Django user with a normalized lowercase email, a password hash, and a revocable API token. `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, and `POST /api/v1/auth/logout` complete the token lifecycle. Registration and login have separate request throttles.

Authenticated recommendation and feedback requests use the account identity established by the token. A supplied anonymous ID cannot override it.

### Create recommendation

`POST /api/v1/recommendations`

```json
{
  "anonymous_id": "local-device-id",
  "context": {
    "meal_type": "LUNCH",
    "weather": "RAIN",
    "temperature": 29
  },
  "filters": {
    "temperature": ["hot"],
    "staples": ["rice", "noodle"],
    "cuisines": ["korean", "japanese"],
    "spice": ["mild"]
  }
}
```

각 배열 안에서는 하나만 맞아도 통과(OR)하고, 값이 있는 배열끼리는 모두 맞아야 통과(AND)한다. 빈 배열은 해당 그룹을 제한하지 않는다. 필터 결과가 없으면 API는 `400`과 `no_matching_foods` 코드를 반환한다.

```json
{
  "recommendation_id": 1,
  "session_id": "uuid",
  "policy_version": "rules-v4",
  "food": {
    "id": 1,
    "name": "순두부찌개",
    "family": "찌개",
    "cuisine": "한식",
    "staple_types": ["rice"],
    "description": "매콤하고 따뜻한 두부 국물 요리"
  },
  "reason": "비 오는 날에 잘 맞는 따뜻한 국물 메뉴예요.",
  "score_breakdown": {
    "preference": 0.5,
    "collaborative": 0.5,
    "context": 0.8,
    "novelty": 1.0,
    "popularity": 0.8,
    "repetition_penalty": 0.0,
    "total": 0.66
  }
}
```

### Record feedback

`POST /api/v1/recommendations/{recommendation_id}/feedback`

```json
{
  "anonymous_id": "local-device-id",
  "event_type": "REROLLED"
}
```

The API rejects feedback when the anonymous ID does not own the exposure.

### Read the privacy-safe relationship graph

`GET /api/v1/recommendation-graph` returns at most 48 food nodes and 120 aggregate edges. Content edges use the seven preference attributes. Collaborative edges require at least five distinct authenticated accounts, a 365-day window, 90-day half-life, cosine normalization, and confidence shrinkage. Selector counts are released only as lower-bound buckets (5, 10, 25, and so on), and the response contains no account or anonymous identity.

## Storage Decisions

- SQLite is the zero-setup local default.
- PostgreSQL is enabled through discrete local variables or one `DATABASE_URL`; production uses a Neon pooled connection.
- Critical queryable fields remain columns; evolving recommendation context and score explanations use `JSONField`.
- Recommendation exposure is immutable. Outcomes are appended as `UserFoodEvent` records.
- Each session stores the 24-item diverse candidate snapshot and conditional selection probabilities for later policy evaluation.
- A candidate snapshot includes food name, family, cuisine, staple types, rank, score, and probability so catalog behavior remains auditable.
- Repeated delivery of the same feedback type for one exposure is idempotent.
- Pairwise similarities are calculated from current events and cached for five minutes; no graph database or identity-bearing graph table is stored.

## Frontend Decisions

- Nuxt 4 is used with the current even-numbered Node 24 runtime.
- Astryx was checked first. Its runtime examples are React components, so it is not installed into the Vue application.
- The implementation adopts the verified Astryx interaction guidance: one primary action, explicit labels, visible loading state, and accessible names.
- The skeuomorphic lever is a native `button`; visual drag gestures are not required to operate the product.
- The paper label at the top of the machine is a dialog trigger. Its native checkboxes support multiple selections, visible focus, Escape closing, focus trapping, and focus return.

## Security And Privacy

- Anonymous IDs are random device-local identifiers used only before login.
- Account passwords use Django's password hashers and validators; plaintext passwords are never stored.
- API tokens are revocable on logout. The MVP browser stores its token locally, which must move to an HttpOnly cookie before a broader public launch.
- No precise location, contact-list, or payment data is collected.
- CORS is limited to explicitly configured frontend origins.
- Feedback ownership is checked against the recommendation exposure.
- Cross-user collaboration accepts only `account-*` identities created by server-authenticated requests; public device IDs never train other users' recommendations.
- Public graph edges suppress collaborative support below five distinct accounts and never serialize identities.
- Production requires a non-default secret, HTTPS redirect, secure cookies, HSTS, and a persistent `DATABASE_URL`.

## Growth Path

1. Add dietary/allergen and availability hard filters.
2. Replace hand weights with a small calibrated ranker or contextual bandit.
3. Add PostgreSQL-backed aggregate features.
4. Measure the item-item collaborative baseline against content-only sessions.
5. Precompute affinities only when the 365-day event scan becomes a measured latency bottleneck.
6. Evaluate graph embeddings through an ablation against the current hybrid baseline.

## Seed Catalog

- `recommendations/seed_data.py` and `recommendations/expanded_catalog.py` contain exactly 1,000 unique menus across 71 food families and 21 precise cuisine labels.
- Every menu carries all eight bounded recommendation attributes.
- Every menu has a reviewed zero-or-more `rice`, `bread`, and `noodle` classification; multi-staple dishes may belong to more than one.
- `seed_foods` updates existing rows transactionally and normalizes known legacy names without breaking referenced row IDs.
- `audit_foods` compares every active database row with the curated source, checks description and attribute integrity, and executes the complete 72-case filter matrix.
