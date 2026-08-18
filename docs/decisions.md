# Decisions

## Active Decisions

- Use V1.3 project operating structure.
- Use Nuxt 4 with Node 24 for the web client.
- Pin TypeScript to 5.9 until the current Nuxt ESLint dependency chain supports TypeScript 7.
- Use Django 5.2 LTS in a uv-managed CPython 3.12 environment.
- Use SQLite by default for local development and a pooled Neon PostgreSQL `DATABASE_URL` in production.
- Use `rules-v4`: preserve hard filters and family-diverse softmax sampling, then mix explainable content preference with privacy-thresholded item-item collaborative affinity; defer GNN and pgvector.
- Derive shared affinities only from authenticated account events within 365 days, require five distinct co-selectors, apply cosine popularity correction and confidence shrinkage, and cache aggregates for five minutes.
- Keep the public graph food-only: show content edges immediately, show collaborative edges only above the privacy threshold, and never serialize account identities or individual histories.
- Treat multiple selections within one filter group as OR and non-empty filter groups as AND; an empty group means unrestricted.
- Preserve anonymous device-local use, but attach authenticated requests to a server-owned Django account identity for durable history.
- Use revocable DRF tokens for the first account slice; migrate to an HttpOnly secure-cookie flow before a broader public launch.
- Deploy the monorepo as separate Nuxt and Django Vercel projects connected to the same GitHub repository.
- Do not install Astryx React runtime into Nuxt; carry over its verified interaction and accessibility guidance.
- Use REST polling every three seconds for Multi rooms so the existing Vercel serverless deployment needs no persistent WebSocket process.
- Treat the room code as a locator and a separately generated participant token as authorization; store only the SHA-256 token digest and never place the token in the share URL.
- Count at most one vote per participant per food, require at least two votes for any draw, select only among top-vote foods, and permit rerolls only while multiple top leaders remain.
- Freeze joining and list edits after the first draw so every participant sees a result derived from one stable set of submitted lists.
- Keep typed Multi menus room-scoped instead of creating global `Food` rows; normalize equal names for voting and resolve exact catalog names back to their curated food.
