# Review Checklist

- [x] MVP scope is explicit and ML-heavy extensions are gated by evidence.
- [x] The main lever is a semantic keyboard-accessible button.
- [x] Loading, success, error, accept, and reroll states are represented.
- [x] Reduced-motion behavior is included.
- [x] API ownership and duplicate-feedback cases are tested.
- [x] Recommendation policy and candidate evidence are persisted.
- [x] Migrations and seed data are repeatable.
- [x] Lint, type, unit/API tests, and production build pass.
- [x] No secrets or private account data were used.
- [x] Registration, login, logout, password hashing/validation, and server-owned identity are tested.
- [x] Production settings require a persistent database, secret key, HTTPS, and explicit CORS origin.
- [x] GitHub Actions and a secret-free Vercel/Neon runbook are present.
- [x] Multi-select filters have explicit OR/AND semantics, validation, no-match recovery, and keyboard-accessible dialog controls.
- [ ] Live PostgreSQL path verified with Docker Desktop running.
- [ ] Manual browser and mobile usability reviewed.
- [x] Live Neon and Vercel account/recommendation smoke test completed for the prior production slice.
- [ ] Email verification, reset/deletion, operator privacy details, and HttpOnly-cookie hardening completed before inviting users.
