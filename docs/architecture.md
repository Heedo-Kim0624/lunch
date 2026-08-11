# Architecture — First Vertical Slice

## High-level Design

```text
Nuxt 4 web client
  ├─ register / login / account state
  └─ multi-filter popup / lever / ticket / feedback
          │ HTTP JSON
          ▼
Django REST API
  ├─ token authentication
  ├─ recommendation orchestration
  ├─ content + context scoring
  ├─ repetition penalty
  └─ softmax exploration
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
→ weather/temperature context score
→ novelty and popularity
→ recent exact-food repetition penalty
→ randomized tie rotation
→ one candidate per food family before any family gets a second
→ 24-item diverse candidate pool
→ softmax sample within that pool
→ immutable session and exposure log
```

The initial score is explainable and versioned. Weights are policy defaults, not learned truth.

## API Contracts

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
  "policy_version": "rules-v3",
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

## Storage Decisions

- SQLite is the zero-setup local default.
- PostgreSQL is enabled through discrete local variables or one `DATABASE_URL`; production uses a Neon pooled connection.
- Critical queryable fields remain columns; evolving recommendation context and score explanations use `JSONField`.
- Recommendation exposure is immutable. Outcomes are appended as `UserFoodEvent` records.
- Each session stores the 24-item diverse candidate snapshot and conditional selection probabilities for later policy evaluation.
- A candidate snapshot includes food name, family, cuisine, staple types, rank, score, and probability so catalog behavior remains auditable.
- Repeated delivery of the same feedback type for one exposure is idempotent.
- Pairwise food similarities are not stored in the MVP.

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
- Production requires a non-default secret, HTTPS redirect, secure cookies, HSTS, and a persistent `DATABASE_URL`.

## Growth Path

1. Add dietary/allergen and availability hard filters.
2. Replace hand weights with a small calibrated ranker or contextual bandit.
3. Add PostgreSQL-backed aggregate features.
4. Evaluate collaborative filtering only after multi-user overlap exists.
5. Evaluate graph embeddings through an ablation against simpler baselines.

## Seed Catalog

- `recommendations/seed_data.py` contains 342 unique menus across 23 food families and 12 cuisine labels.
- Every menu carries all eight bounded recommendation attributes.
- Every menu has a reviewed zero-or-more `rice`, `bread`, and `noodle` classification; multi-staple dishes may belong to more than one.
- `seed_foods` updates existing rows transactionally and normalizes known legacy names without breaking referenced row IDs.
