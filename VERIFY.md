# Verification

## Result

State: **PASS** for local SQLite and live Vercel + Neon production.

## Automated checks

- [x] AgentOS preflight and `.agentos/PREFLIGHT.md` reviewed.
- [x] Secret boundary maintained; no `.env` or private account data read or stored.
- [x] `powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1`
  - Ruff: pass
  - ESLint: pass
  - Django system check: pass
  - Django migration drift check: pass (`No changes detected`)
  - Nuxt TypeScript check: pass
  - Backend pytest: 43 passed
  - Frontend Vitest: 8 passed
  - Nuxt production build: pass
- [x] In-process Django client smoke test:
  - health: HTTP 200
  - recommendation: HTTP 201, policy `rules-v3`
  - feedback: HTTP 201, event `ACCEPTED`
  - temporary smoke-test records removed afterward
- [x] `docker compose config --quiet`: pass.

## Review checks

- [x] Recommendation events are linked to the exact exposure.
- [x] Duplicate feedback is idempotent.
- [x] Feedback ownership is checked against the anonymous or authenticated server-owned identity.
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

## Not yet verified

- [ ] Live PostgreSQL migration/test path: Docker Desktop's Linux engine was not running.
- [ ] Manual browser visual and keyboard pass: local servers launched and API smoke passed, but the available browser-control runtime reported no browser backend; UI evidence remains build-, type-, and unit-test-based.
- [ ] Cross-browser and mobile-device behavior.

## Evidence

- Implementation: `frontend/`, `backend/`, `scripts/`
- Product and architecture: `docs/prd.md`, `docs/architecture.md`, `docs/design.md`
- Risk review: `review/risks.md`, `review/checklist.md`
- Prediction-error captures remain in the machine-local AgentOS raw-evidence store and are not published.
