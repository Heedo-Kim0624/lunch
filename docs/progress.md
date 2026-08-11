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

The local application now includes a second complete slice for email registration, login, logout, account-owned recommendation history, production-safe Django settings, GitHub Actions, and a Vercel + Neon deployment runbook. The full gate passes with 18 backend and 5 frontend tests. GitHub publication and live Vercel/Neon verification are the remaining external steps.

## 2026-08-11 — Account and deployment slice

- Added Django user registration, password validation/hashing, token login, current-user lookup, logout, and endpoint throttles.
- Bound authenticated recommendations and feedback to the server-verified account identity.
- Added accessible Nuxt registration, login, account navigation, logout, and an MVP privacy notice.
- Added `DATABASE_URL` support, mandatory production secret validation, HTTPS/HSTS settings, explicit CORS, and Vercel host discovery.
- Added a two-project Vercel + Neon deployment guide and GitHub Actions verification.
- Kept machine-local AgentOS/JARVIS metadata out of the public repository.
- Verified 18 backend tests, 5 frontend tests, Ruff, ESLint, Django checks, migration drift, TypeScript, and the Nuxt production build.
- Fixed the first Linux CI run's platform-specific npm lockfile gap by making the required Emscripten runtime helpers explicit; clean-install validation now passes locally.

## Known follow-ups

- Start Docker Desktop before validating the optional PostgreSQL path end to end.
- Add Playwright coverage after the interaction and visual direction survive initial manual testing.
- Measure actual acceptance, reroll, and repeat rates before considering collaborative or graph-based models.
- Add email verification, password reset, account deletion, and an operator contact before inviting real users.
- Replace the local-storage API token with an HttpOnly secure-cookie flow before a broader public launch.
