# Changelog

## 2026-08-11

- Project initialized with JARVIS V1.3 scaffold.
- Added a 342-menu personalized recommendation flow with persistent feedback.
- Added email registration, login, logout, account-owned history, and accessible account UI.
- Added Vercel + Neon production configuration, deployment documentation, and GitHub Actions.
- Added multi-select temperature, staple, cuisine, and spice filters backed by reviewed 342-menu staple classifications and the versioned `rules-v3` policy.
- Expanded the catalog to exactly 1,000 menus with unique descriptions, 71 families, 21 precise cuisine labels, and 918 distinct attribute profiles.
- Added a fail-fast database catalog audit covering every curated field and all 72 full filter combinations.
- Replaced per-row seeding with transaction-safe bulk create/update so the 1,000-row catalog can be promoted efficiently to remote PostgreSQL.
