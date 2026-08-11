# Risks

## Product and data

- A reroll can mean dislike, unavailability, cost, distance, or mood. It therefore has only a weak negative weight.
- Seed-food attributes and rice/bread/noodle memberships are editorial estimates, not nutritional or restaurant-availability facts.
- Anonymous local identity does not synchronize; signed-in history does.
- Initial data is too sparse to justify collaborative filtering, GNNs, or claims of strong personalization.

## Engineering

- SQLite and the live Neon PostgreSQL runtime are verified; the optional Docker Desktop PostgreSQL development path is not.
- Automated browser E2E coverage is not configured yet.
- The browser token is stored in local storage and is exposed if an XSS flaw is introduced.
- Throttling uses Django's default per-instance cache and is only a basic abuse barrier on serverless instances.
- Node emits a non-failing upstream deprecation warning during the Nuxt build.

## Mitigations

- Preserve exact exposure and policy data for later evaluation.
- Keep policy changes versioned and reasons tied to real score factors.
- Treat dietary restrictions as future hard filters, never as soft preferences.
- Complete email verification, reset/deletion flows, privacy/operator details, and secure-cookie hardening before inviting real users.
