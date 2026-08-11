# Assumptions

- The product supports immediate anonymous use and optional email accounts for persistent history.
- Korean lunch dishes and a curated local seed set are sufficient for the first interaction test.
- `ACCEPTED` and `REROLLED` are the only feedback actions needed in the first visible UI, while the API supports future explicit events.
- Current context is optional; missing weather or temperature must not prevent a recommendation.
- SQLite is acceptable for zero-setup local development; deployed Vercel functions require Neon PostgreSQL.
