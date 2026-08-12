# Review Checklist

## Single / Multi shared room

- [x] Taste-map navigation action is removed and Single/Multi mode links remain keyboard accessible.
- [x] Guests join by nickname without an account, while room code and participant authorization token remain separate.
- [x] Only token digests are stored; public room payloads contain no token or another participant's food list.
- [x] Each participant submits 1–12 distinct active lunch foods and adds one visible readiness reel.
- [x] The host lever requires two participants, everyone ready, and at least one food with two distinct votes.
- [x] No-overlap rooms stay locked with explicit copy and an API `no_overlap` conflict.
- [x] Unique top foods become final; tied top foods support non-repeating immediate rerolls.
- [x] Joining and choice edits lock after the first draw.
- [x] Room mutations use transactions and row locking; reads are bounded and throttled for polling.

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
- [x] Collaborative affinity enforces authenticated sources, five-user support, deduplicated selectors, popularity correction, time decay, and explicit dislike exclusion.
- [x] The public graph contains food-only aggregate data, applies payload limits, and has SVG keyboard navigation plus a text alternative.
- [ ] Live PostgreSQL path verified with Docker Desktop running.
- [ ] Manual browser and mobile usability reviewed.
- [x] Live Neon and Vercel account/recommendation smoke test completed for the prior production slice.
- [ ] Email verification, reset/deletion, operator privacy details, and HttpOnly-cookie hardening completed before inviting users.
