# Progress

## 2026-08-18 — Multi production search runtime repair

- Traced the reported search failure to repeated production `GET /api/v1` 404s while the catalog endpoint itself remained healthy.
- Confirmed the deployed Nuxt runtime config contained a trailing CRLF in `apiBase`; query serialization truncated the intended `/foods` path at that boundary.
- Made the Multi URL helper trim surrounding whitespace and CRLF before joining paths and added an exact regression test for the deployed value shape.
- Added token-gated room-aware search so current room custom choices appear beside catalog matches without exposing participant identity or vote counts; removed choices no longer appear.
- Added project-scoped Vercel alias CORS coverage and passed the full local gate with 74 backend tests, 16 frontend tests, lint, type checking, migration drift checking, and the Nuxt production build.

## 2026-08-18 — Multi search recovery and direct menu entry

- Reproduced a user-visible food-search failure and confirmed the catalog API itself still returned HTTP 200 with the production web CORS origin.
- Replaced ad-hoc Multi endpoint concatenation with a slash-safe URL helper, added one retry, and prevented stale search failures from overwriting the latest result.
- Added an always-available direct-entry action and Enter-key flow to the food chooser, including clear recovery copy when search is unavailable.
- Added room-scoped custom foods with normalized overlap voting, exact catalog-name resolution, bounded validation, and no curated-catalog pollution.
- Preserved the legacy `food_ids` write contract while adding mixed `{food_id}` / `{custom_name}` submissions.
- Applied migration `0006` locally and passed the full gate with 70 backend tests, 16 frontend tests, lint, type checking, migration drift checking, and the Nuxt production build.
- Passed both GitHub Actions jobs on PR #5 and merged the fix to `main` as `0c14577`.
- Applied migration `0006` to Neon, deployed API `dpl_B86L3SDwtVA6FzwyAYDEjWVbuGfo`, and deployed web `dpl_CcWUmGJaz1CHznU9D5gWMbjt1XbG` to the existing production aliases.
- Verified a live two-person direct-entry flow: whitespace-normalized names combined into a two-vote custom leader and the host draw returned that winner.
- Confirmed live catalog search and the deployed direct-add UI bundle, then deleted the disposable room and verified HTTP 404.
- Browser click automation remained unavailable because the in-app browser runtime exposed no browser instance; automated interaction, API, build, and deployed-bundle checks passed.

## 2026-08-12 — Shared Multi lunch room

- Replaced the taste-map navigation action with left-side `Single` and `Multi` mode tabs while retaining the existing single-person recommendation flow.
- Added 24-hour share rooms that allow account-free nickname joining and create one visual reel per participant.
- Added searchable 1–12 item food lists, readiness state, three-second room polling, share-link copy, and responsive dialog/machine layouts.
- Counted each participant at most once per food and limited the draw pool to the highest-vote foods.
- Made unique leaders final, allowed tied leaders to be redrawn without an immediate repeat, and disabled the lever when every submitted food has only one vote.
- Restricted drawing to the host, locked joining and list edits after the first draw, and stored only SHA-256 participant-token digests in the database.
- Added transactional room mutations, row locking, endpoint throttles, nickname validation, bounded room/list sizes, and public-state privacy tests.
- Passed the complete local gate with 67 backend tests, 14 frontend tests, Ruff, ESLint, Django checks, migration drift checks, TypeScript, and the Nuxt production build.
- Applied migration `0005` locally and completed an end-to-end two-person room smoke test; all disposable room rows were removed afterward.
- Passed PR #2 and PR #3 checks and merged both to `main`; final `main` Actions run `31571682495` passed.
- Applied migration `0005` to Neon and fixed a PostgreSQL-only nullable outer-join lock failure found by the first live guest-join smoke test.
- Deployed API `dpl_ES9mevFyFqCE45eRaTXbFZ12ejBx` and web `dpl_3iZCB9PsuEgCd9JGxqfNxo81NrjS` to their existing production aliases.
- Verified live unique-winner, tied-reroll, and no-overlap flows, confirmed the public Multi page in Chrome, and removed every disposable production room.

## 2026-08-11 — First vertical slice complete

- Initialized the JARVIS V1.3 workspace harness and project documentation.
- Defined the MVP as an anonymous, one-action personalized lunch recommender.
- Implemented a Nuxt 4 lever UI with accessible controls and reduced-motion behavior.
- Implemented a Django REST API with a versioned `rules-v2` scoring policy, logged exploration probability, diverse candidate snapshots, and idempotent feedback.
- Expanded the catalog to 342 unique menus across 23 food families and 12 cuisine labels.
- Added complete bounded attributes, transactional idempotent seeding, and legacy-name normalization.
- Added SQLite zero-setup development and optional PostgreSQL 17 via Docker Compose.
- Added backend and frontend tests, linting, type checks, migration drift checks, and the Nuxt production build gate.
- Verified the complete gate: 12 backend tests, 3 frontend tests, lint, type checks, migrations, and production build all pass.
- Verified recommendation and feedback persistence through an in-process Django HTTP smoke test.
- Verified 60 cold-start requests produced 55 unique foods from 21 food families while every session retained all 342 eligible foods and a 24-item, 23-family candidate snapshot.

## Current state

The application is live on Vercel with a Neon free PostgreSQL database. The full local gate and GitHub Actions pass, and the disposable production account smoke test covered registration through repeat login.

## 2026-08-11 — Account and deployment slice

- Added Django user registration, password validation/hashing, token login, current-user lookup, logout, and endpoint throttles.
- Bound authenticated recommendations and feedback to the server-verified account identity.
- Added accessible Nuxt registration, login, account navigation, logout, and an MVP privacy notice.
- Added `DATABASE_URL` support, mandatory production secret validation, HTTPS/HSTS settings, explicit CORS, and Vercel host discovery.
- Added a two-project Vercel + Neon deployment guide and GitHub Actions verification.
- Kept machine-local AgentOS/JARVIS metadata out of the public repository.
- Verified 18 backend tests, 5 frontend tests, Ruff, ESLint, Django checks, migration drift, TypeScript, and the Nuxt production build.
- Fixed the first Linux CI run's platform-specific npm lockfile gap by making the required Emscripten runtime helpers explicit; clean-install validation now passes locally.
- Published the public GitHub repository and passed both GitHub Actions jobs.
- Provisioned Neon `lunch-db` in Singapore, applied all migrations, and verified 342 active foods.
- Deployed the Django API to `lunch-api-mocha.vercel.app` and Nuxt web app to `lunch-web-ten.vercel.app`.
- Verified production signup, CORS, current user, recommendation, feedback, logout, and repeat login, then removed all disposable smoke data.

## Known follow-ups

- Start Docker Desktop before validating the optional PostgreSQL path end to end.
- Add Playwright coverage after the interaction and visual direction survive initial manual testing.
- Measure actual acceptance, reroll, and repeat rates before considering collaborative or graph-based models.
- Add email verification, password reset, account deletion, and an operator contact before inviting real users.
- Replace the local-storage API token with an HttpOnly secure-cookie flow before a broader public launch.

## 2026-08-11 — 1,000-menu catalog expansion

- Added 658 individually named lunch menus while retaining the original 342 reviewed rows, producing exactly 1,000 active catalog entries.
- Rebalanced the six user-facing cuisine groups to Korean 350, Chinese 120, Western 150, Japanese 130, Southeast Asian 100, and Other 150.
- Verified 1,000 unique descriptions, 71 food families, 21 precise cuisine labels, 918 distinct eight-attribute profiles, 115 cold dishes, and 233 spicy dishes.
- Verified staple memberships of rice 531, bread 122, and noodle 196; menus may have multiple staples or none.
- Added a database audit command that detects missing, extra, or drifted rows and runs all 72 full temperature/staple/cuisine/spice filter combinations.
- Confirmed 41 meaningful full combinations return candidates and 31 semantically empty combinations follow the explicit no-match path.
- Verified idempotent local seeding with `0 created, 0 updated, 1000 unchanged, 0 deactivated` on the second run.
- Switched the seed command to batched create/update operations after the first remote run exposed per-row network round trips at the new scale.
- Deployed the compatible API mapping to Vercel and promoted the exact 1,000-row catalog to Neon.
- Passed the production catalog audit with 1,000 descriptions, 71 families, 918 profiles, and the same 41/31 split across 72 full filter combinations.
- Passed seven live matching filter requests across all six cuisine groups and OR/AND selection, plus the HTTP 400 `no_matching_foods` path.
- Removed all temporary live-smoke sessions and exposures and confirmed zero matching records remained.

## 2026-08-11 — Hybrid collaborative recommendation graph

- Upgraded the recommendation policy to `rules-v4` with a 15% item-item collaborative term while keeping hard filters, attribute preference, context, novelty, popularity, repetition protection, and family diversity.
- Limited shared learning to authenticated account events from the last 365 days and required five distinct co-selectors before activating an affinity.
- Added 90-day event decay, per-user food aggregation, cosine popularity correction, confidence shrinkage, and hard exclusion of explicitly disliked foods.
- Added a cached `GET /api/v1/recommendation-graph` response with up to 48 food nodes and 120 content, collaborative, or hybrid edges without any identity fields or exact selector counts.
- Added a keyboard-accessible `/graph` visualization, text alternative, node inspector, relationship legend, responsive layout, and reduced-motion compatibility using the existing local machine design system.
- Added a reproducible graph audit covering source window, payload bounds, support threshold, similarity bounds, and identity non-disclosure.
- Passed the full local gate with 57 backend tests, 10 frontend tests, lint, type checking, migration drift checking, and the Nuxt production build.
- Passed PR checks, merged PR #1 as `baf2645`, and passed final `main` Actions run `31480410515`.
- Deployed `rules-v4` to the Vercel API and the food graph to the Vercel web application.
- Verified the Neon graph audit with 45 eligible events from one account; collaborative edges correctly remain disabled until five distinct authenticated accounts overlap.
- Verified the public graph and recommendation contracts, health endpoint, browser page load, and cleanup of the temporary production smoke session.

## 2026-08-11 — Per-food catalog quality pass

- Replaced 23 repeated family descriptions with 342 unique, item-specific food descriptions.
- Recalibrated all eight recommendation attributes per item, including explicit cold-dish handling and Korean-audience familiarity/adventurousness.
- Increased the catalog from 23 repeated attribute profiles to 294 distinct profiles while retaining bounded 0–1 values.
- Corrected known semantic failures such as 바쿠테, 카오만가이, 팟씨유, 수제비, 마라탕, 아사이볼, and 피시앤칩스.
- Added coverage, uniqueness, distribution, and edge-case regression checks.
- Replaced the misleading first-use reason with an explicit cold-start explanation based on popularity and menu diversity.
- Verified 19 backend tests, 5 frontend tests, Ruff, ESLint, Django checks, migration drift, TypeScript, and the Nuxt production build.
- Updated all 342 Neon rows in place and confirmed 342 distinct descriptions, 294 distinct profiles, zero blanks, and 47 explicitly cold dishes in production.
- Deployed the API, passed a live cold-start recommendation smoke test, and removed its temporary session and exposure.

## 2026-08-11 — Multi-filter recommendation slice

- Added reviewed zero-or-more rice, bread, and noodle classifications to all 342 menus: 172 rice, 41 bread, and 79 noodle memberships, including multi-staple dishes.
- Added `rules-v3` hard filtering for temperature, staple, cuisine group, and spice before scoring and diverse-pool construction.
- Defined same-group selections as OR, cross-group selections as AND, and empty groups as unrestricted.
- Added a machine-label-triggered multi-select dialog with native checkboxes, active-count badge, reset/apply actions, focus trap, Escape/backdrop close, and trigger-focus return.
- Passed local API smoke checks for a matching combined filter and the explicit `no_matching_foods` error path; temporary records were removed.
- Verified the full gate: 33 backend tests, 8 frontend tests, Ruff, ESLint, Django checks, migration drift, TypeScript, and the Nuxt production build all pass.
- Browser automation was unavailable in the current runtime, so manual visual, cross-browser, and physical mobile checks remain open.
- Pushed commit `f172381`, passed GitHub Actions run `31474772129`, and deployed both Vercel production projects.
- Applied migration `0004`, updated all 342 Neon rows, and verified production membership counts of 172 rice, 41 bread, and 79 noodle.
- Passed live combined-filter, no-match, and web-trigger smoke checks; database values matched the requested filters and all temporary smoke data was removed.
