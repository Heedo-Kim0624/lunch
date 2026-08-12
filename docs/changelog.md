# Changelog

## 2026-08-12

- Added left-side `Single` and `Multi` navigation and removed the taste-map button from primary navigation.
- Added nickname-only shared rooms, participant reels, share links, food-list dialogs, readiness polling, and host-only drawing.
- Added deterministic top-vote eligibility, tied-leader rerolls, no-overlap locking, 24-hour expiry, hashed participant tokens, and transactional concurrency controls.
- Added migration `0005`, ten backend room/API tests, and four frontend presentation-rule tests.
- Kept the PostgreSQL room lock on the room table only so a nullable result-food relationship never enters the `FOR UPDATE` query; added a regression test for the generated join shape.
- Deployed the Neon migration and both Vercel projects, then passed live unique-winner, tied-reroll, no-overlap, browser-page, and smoke-data cleanup checks.

## 2026-08-11

- Project initialized with JARVIS V1.3 scaffold.
- Added a 342-menu personalized recommendation flow with persistent feedback.
- Added email registration, login, logout, account-owned history, and accessible account UI.
- Added Vercel + Neon production configuration, deployment documentation, and GitHub Actions.
- Added multi-select temperature, staple, cuisine, and spice filters backed by reviewed 342-menu staple classifications and the versioned `rules-v3` policy.
- Expanded the catalog to exactly 1,000 menus with unique descriptions, 71 families, 21 precise cuisine labels, and 918 distinct attribute profiles.
- Added a fail-fast database catalog audit covering every curated field and all 72 full filter combinations.
- Replaced per-row seeding with transaction-safe bulk create/update so the 1,000-row catalog can be promoted efficiently to remote PostgreSQL.
- Added the `rules-v4` hybrid recommendation baseline with privacy-thresholded item-item collaborative filtering, popularity correction, and explicit dislike exclusion.
- Added a cached public food relationship graph, accessible Nuxt visualization, and a reproducible privacy/source audit command.
