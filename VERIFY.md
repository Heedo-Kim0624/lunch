# Verification

## Result

State: **PASS** for local SQLite and the deployed Neon/Vercel Multi search and direct-entry flow.

## 2026-08-18 Multi search and direct-entry local verification

- [x] Production catalog search returned HTTP 200 for `라면` with the exact web CORS origin; runtime logs showed user-session 404 requests to the API base path, motivating centralized URL construction.
- [x] Slash-safe API URL, retry, and stale-response guards are covered by frontend tests.
- [x] Direct entry works without a search result and serializes as `{custom_name}`; exact catalog matches serialize or resolve as the curated `Food`.
- [x] Equal normalized direct names from two participants produce two votes and can win the host draw.
- [x] Custom entries remain in `MultiRoomCustomFood`; no global `Food` row is created.
- [x] Invalid characters, duplicate direct names, and catalog/direct duplicates are rejected.
- [x] Migration `0006_multiroom_leading_choice_keys_and_more` applied to local SQLite.
- [x] Full verifier: 70 backend tests, 16 frontend tests, Ruff, ESLint, Django checks, migration drift, TypeScript, and Nuxt production build passed.
- [x] PR #5 passed both GitHub Actions jobs and merged to `main` as `0c14577`.
- [x] Neon migration `0006_multiroom_leading_choice_keys_and_more` applied successfully.
- [x] API deployment `dpl_B86L3SDwtVA6FzwyAYDEjWVbuGfo` and web deployment `dpl_CcWUmGJaz1CHznU9D5gWMbjt1XbG` reached Ready on the existing production aliases.
- [x] Live API smoke: two participants submitted whitespace variants of one direct menu, the normalized leader received two votes, and the host draw returned the custom winner with `id=null` and `is_custom=true`.
- [x] Live catalog search for `라면` returned three results, and the deployed `/multi/TESTCODE` route returned HTTP 200 with the new direct-add and search/direct-input copy in its production bundles.
- [x] The disposable smoke room and its two choices, two participants, and custom-food row were deleted; follow-up room lookup returned HTTP 404.
- [ ] Live browser click/keyboard smoke; the in-app browser runtime reported no available browser instance.

## 2026-08-12 Multi-room local verification

- [x] `powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1`
  - Ruff, ESLint, Django system check, and migration drift check: pass
  - Backend pytest: 67 passed
  - Frontend Vitest: 14 passed
  - Nuxt TypeScript and production build: pass
- [x] Migration `0005_multiroom_multiroomparticipant_multiroomchoice_and_more` applied to local SQLite.
- [x] Two-person API smoke: create room, nickname-only guest join, both submit lists, shared leader becomes drawable, host draw returns the two-vote winner.
- [x] Smoke cleanup removed four choices, two participants, and one room.
- [x] Tests cover token digest storage, public choice privacy, nickname uniqueness, host-only draw, post-draw lock, tied reroll, no-overlap lock, active-food search, and unique-winner completion.
- [x] Room/list mutations lock the room row inside transactions so join, submit, and draw rules are evaluated against one serialized state on PostgreSQL.
- [x] PostgreSQL compatibility regression proves the locked room query does not outer-join the nullable result-food relation.
- [x] Participant tokens are returned only at join/create time, sent through `X-Multi-Token`, and persisted only as SHA-256 digests.
- [x] Production migration, Vercel deployment, live two-person smoke, and cleanup.

## 2026-08-12 Multi-room production verification

- [x] Neon migration `0005_multiroom_multiroomparticipant_multiroomchoice_and_more`: applied.
- [x] PR #2 and PostgreSQL fix PR #3: checks passed and merged; final `main` run `31571682495` passed.
- [x] API deployment `dpl_ES9mevFyFqCE45eRaTXbFZ12ejBx`: Ready and aliased to `https://lunch-api-mocha.vercel.app`.
- [x] Web deployment `dpl_3iZCB9PsuEgCd9JGxqfNxo81NrjS`: Ready and aliased to `https://lunch-web-ten.vercel.app`.
- [x] Live unique-winner flow: two nickname-only participants, both ready, shared food drawable, winner returned with two votes.
- [x] Live tied-leader flow: two leaders at two votes, reroll enabled, second draw excluded the immediate previous result.
- [x] Live no-overlap flow: all ready with `max_votes=1`, lever state false, draw returned HTTP 409 `no_overlap`.
- [x] Public web: `/` and `/multi` returned HTTP 200, Single/Multi links rendered, no `/graph` navigation link rendered, and Chrome loaded the Korean Multi lobby title and visible flow copy.
- [x] All four disposable production rooms were deleted with cascading participant/choice cleanup; each room code subsequently returned HTTP 404.

## Automated checks

- [x] AgentOS preflight and `.agentos/PREFLIGHT.md` reviewed.
- [x] Secret boundary maintained; no `.env` or private account data read or stored.
- [x] `powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1`
  - Ruff: pass
  - ESLint: pass
  - Django system check: pass
  - Django migration drift check: pass (`No changes detected`)
  - Nuxt TypeScript check: pass
  - Backend pytest: 57 passed
  - Frontend Vitest: 10 passed
  - Nuxt production build: pass
- [x] In-process Django client smoke test:
  - health: HTTP 200
  - recommendation: HTTP 201, policy `rules-v4`
  - feedback: HTTP 201, event `ACCEPTED`
  - temporary smoke-test records removed afterward
- [x] `docker compose config --quiet`: pass.

## Review checks

- [x] Recommendation events are linked to the exact exposure.
- [x] Duplicate feedback is idempotent.
- [x] Feedback ownership is checked against the anonymous or authenticated server-owned identity.
- [x] Shared collaboration uses only authenticated `account-*` histories; anonymous device IDs personalize only themselves.
- [x] Unauthenticated requests cannot submit the reserved `account-*` identity prefix, while authenticated requests replace all supplied IDs with the server-owned account identity.
- [x] Five distinct accounts are required per food pair, repeated events do not inflate support, and public counts are lower-bound buckets rather than exact values.
- [x] A 365-day source window, 90-day decay, cosine popularity correction, confidence shrinkage, and negative net histories are covered by tests.
- [x] Explicitly disliked foods are removed before hybrid scoring and filtering can return the normal no-match recovery path.
- [x] The public graph contains no identity field/value, stays within 48 nodes and 120 edges, and exposes content-only relationships before collaboration qualifies.
- [x] `audit_recommendation_graph` passes locally with 0 account profiles, 0 qualified collaborative edges, 48 nodes, 65 content edges, and `identity_data_exposed=false`.
- [x] A cold-cache local graph request returned HTTP 200 in 96.8 ms with two database queries; subsequent responses use a five-minute cache.
- [x] Recommendation reasons are derived from actual score factors.
- [x] Seed catalog contains exactly 1,000 unique menus, 1,000 unique item-specific descriptions, and all eight attributes bounded to 0–1.
- [x] Individual profiles produce 918 distinct attribute combinations; cold scores identify 115 genuinely cold or chilled dishes.
- [x] Edge-case assertions cover 바쿠테 broth/light/familiarity, 카오만가이 spice, 물냉면 temperature, 마라탕 spice/light, 닭가슴살샐러드 lightness, and 피시앤칩스 preparation.
- [x] A cold-start recommendation explicitly says that no selection history exists and does not claim to avoid prior choices.
- [x] All 1,000 seed menus expose only reviewed zero-or-more `rice`, `bread`, and `noodle` memberships; distribution is 531, 122, and 196 memberships respectively.
- [x] Unit and API tests prove same-group OR, cross-group AND, empty-group unrestricted behavior, cuisine grouping, invalid-value rejection, and explicit no-match handling.
- [x] The complete 72-case temperature/staple/cuisine/spice matrix is audited; 41 meaningful intersections are nonempty and 31 semantic impossibilities use explicit no-match handling.
- [x] Local seeded HTTP smoke returned a hot, spicy, Japanese noodle under combined filters and returned HTTP 400 `no_matching_foods` for an impossible combination; temporary records were removed.
- [x] The filter dialog uses native checkboxes, visible selection state, focus trapping, Escape/backdrop close, and trigger-focus restoration.
- [x] Two consecutive seed runs finish with 1,000 active menus and no duplicates; the second reports `0 created, 0 updated, 1000 unchanged, 0 deactivated`.
- [x] A 60-request catalog smoke test returned 55 unique foods across 21 families; temporary sessions were removed.
- [x] Motion is disabled for `prefers-reduced-motion`.
- [x] GNN, pgvector, restaurant providers, payment, and location remain out of MVP scope.
- [x] Registration normalizes email, hashes passwords, validates password strength, rejects duplicates, and returns a revocable token.
- [x] Login, current-user lookup, and logout token invalidation are covered by API tests.
- [x] Authenticated recommendation identity is established by the server and ignores a spoofed anonymous ID.
- [x] Signup validation, visible labels, field errors, loading state, and a single primary submit action are implemented.
- [x] Production configuration rejects the local secret and non-persistent Vercel SQLite configuration.
- [x] GitHub Actions reproduces the backend and frontend quality gates without secrets.
- [x] Neon Production migrations completed for content types, users, tokens, and recommendations.
- [x] Production seed verified at exactly 1,000 active foods; the idempotent follow-up reported `0 created, 0 updated, 1000 unchanged, 0 deactivated`.
- [x] Production `audit_foods` returned 1,000 unique descriptions, 71 families, 918 distinct profiles, 115 cold dishes, and 233 spicy dishes.
- [x] Production 바쿠테 now mentions pork ribs and reports `broth=0.9`, `light=0.4`, `adventurous=0.7`, `cold=0.0`, and `familiar=0.4`.
- [x] Live cold-start recommendation returned the honest no-history reason and an item-specific description; its temporary session and exposure were removed afterward.
- [x] Production schema remains at migration `0004_food_staple_types`; no schema migration was required for the catalog-only expansion.
- [x] Production staple audit returned exactly 531 rice, 122 bread, and 196 noodle memberships across 1,000 active menus.
- [x] Live complete-filter smoke tests covered all six broad cuisine groups plus a same-group OR/cross-group AND case; every match returned `rules-v3` and a correctly classified staple.
- [x] Live impossible filter returned HTTP 400 with `no_matching_foods`; the deployed web returned HTTP 200 with the new `조건 고르기` trigger.
- [x] Seven temporary production filter sessions and exposures were deleted; follow-up session, exposure, and event counts were all zero.
- [x] GitHub Actions run `31474772129` passed for commit `f172381`.
- [x] Vercel Django API health returned HTTP 200 at `https://lunch-api-mocha.vercel.app/api/v1/health`.
- [x] Production signup page returned HTTP 200 and CORS returned the exact web origin.
- [x] Disposable production account completed register, current-user lookup, recommendation, `ACCEPTED` feedback, logout (HTTP 204), and login again.
- [x] Disposable user, token, recommendation session, exposure, and feedback were removed; follow-up counts were zero.
- [x] GitHub Actions run `31477492178` passed for commit `37f4adf` after the final seed optimization.
- [x] Vercel production deployment `dpl_23NshkXgdvR2PezN4oFjZpyaotuP` reached Ready and the API health endpoint returned HTTP 200.
- [x] GitHub Actions run `31479822210` passed both backend and frontend jobs for commit `8e927e9`.
- [x] PR #1 merged as `baf2645`; final `main` verification run `31480410515` passed both jobs.
- [x] Vercel API deployment `dpl_DF3ZYjhM77SgcvSRKyKBJL7hntGE` and web deployment `dpl_BapD4ritM1wqzmQ88dzYuahvmgwD` reached Ready and retained the public aliases.
- [x] Production graph audit found 45 eligible events from one account, no pair meeting the five-account privacy threshold, and therefore the expected `content_only` mode with 48 nodes, 65 edges, and no identity exposure.
- [x] Live graph API returned `rules-v4`, 48 nodes, 65 edges, `minimum_shared_selectors=5`, `identity_data_exposed=false`, and no account or anonymous identity field/value.
- [x] Live recommendation returned `rules-v4` with the collaborative score key; its temporary session and exposure were deleted afterward.
- [x] Live `/graph` returned HTTP 200 with the graph title and markup, and Agent Browser loaded the public page with the title `음식 취향 지도 · 점심 결정 기계`.

## Not yet verified

- [ ] Live PostgreSQL migration/test path: Docker Desktop's Linux engine was not running.
- [ ] Full manual keyboard interaction and visual review across multiple viewport sizes.
- [ ] Cross-browser and mobile-device behavior.

## Evidence

- Implementation: `frontend/`, `backend/`, `scripts/`
- Product and architecture: `docs/prd.md`, `docs/architecture.md`, `docs/design.md`
- Risk review: `review/risks.md`, `review/checklist.md`
- Prediction-error captures remain in the machine-local AgentOS raw-evidence store and are not published.
