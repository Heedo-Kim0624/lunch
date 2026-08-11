# Progress

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
- Verified idempotent local seeding with `0 created, 1000 updated, 0 deactivated` on the second run.

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
