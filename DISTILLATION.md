# Distillation Plan

## Durable project knowledge

- The UI now has two primary modes: `Single` keeps personal recommendation, while `Multi` coordinates an account-free shared lunch decision through an expiring link.
- Multi votes are binary per participant and food. Only highest-vote foods enter the draw; a unique leader ends the room, tied leaders can be redrawn, and a room with no overlapping choice cannot draw.
- Multi participant capability tokens are browser-held and database-hashed. Room codes locate rooms but do not authorize participant or host actions.
- Multi uses three-second REST polling to stay within the current Vercel architecture; WebSockets remain a future scale/latency option.
- The product is a personalized decision engine presented as a single lever, not a random menu picker.
- The active policy is `rules-v4`: explicit hard filters, content attributes, authenticated-account item-item collaboration, context adjustments, repetition penalties, family-round-robin pooling, and bounded softmax exploration.
- Shared affinity requires five distinct authenticated accounts, uses a 365-day window with 90-day decay, corrects popularity through cosine normalization, and never trains from public anonymous IDs.
- The public relationship graph contains food nodes only. Content edges work at cold start; collaborative edges appear only above the privacy threshold.
- User filters use OR within a group and AND across non-empty groups; an empty group is unrestricted. Staple membership is explicit data, not a food-name substring guess.
- Every recommendation stores the policy version, candidate count, scored top-candidate snapshot, chosen exposure, score breakdown, and selection probability.
- Only observed user actions become learning signals; a reroll is weak negative evidence and non-exposed foods are never inferred as disliked.
- SQLite is the zero-setup default. PostgreSQL is an optional parity path, not an MVP dependency.
- Production uses a Neon pooled `DATABASE_URL`; Vercel must never fall back to SQLite.
- Authenticated recommendation history belongs to the server-verified account identity, while anonymous users retain device-local history.
- Passwords use Django validation and hashing. Browser tokens are revocable but remain an MVP local-storage tradeoff that requires HttpOnly-cookie hardening before broad launch.
- GNN and vector search require measured evidence that simpler baselines are inadequate.
- Large catalogs need diversity at candidate-pool construction time; adding rows alone does not make them reachable when only a globally ranked top set is sampled.

## Prediction-error memory

- Prefer an explicitly supported Python version for Django even when a newer system runtime is present.
- Run backend tools from the backend project context so `pyproject.toml` configuration is applied.
- Exclude virtual environments from static-analysis scope.
- Pin TypeScript to the version supported by the active Nuxt ESLint chain.
- Verify framework type dependencies such as `@types/node` during initial setup.
- When a live server cannot be launched by the environment, exercise the HTTP stack with the framework test client and record that browser validation is still pending.
- Validate Docker engine availability before attempting the PostgreSQL setup path.
- Include a migration-drift check in the normal type/check gate.
- Validate `npm ci` from a clean Linux runner: a lockfile refreshed on Windows with existing modules can omit cross-platform optional WASM packages, so make required runtime helpers explicit when the package manager reports them missing.

## Evidence boundary

No credentials, tokens, cookies, account pages, payment data, or private form values were captured. The project used official framework documentation, local source code, generated test output, and local AgentOS records only.

## Destination

- Project work log: the user's private Obsidian vault under `00_Inbox/Code/2026-08-11/`
- Detailed implementation truth: this repository's `README.md`, `docs/`, `VERIFY.md`, and source/tests
