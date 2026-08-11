# Decisions

## Active Decisions

- Use V1.3 project operating structure.
- Use Nuxt 4 with Node 24 for the web client.
- Pin TypeScript to 5.9 until the current Nuxt ESLint dependency chain supports TypeScript 7.
- Use Django 5.2 LTS in a uv-managed CPython 3.12 environment.
- Use SQLite by default for local development and a pooled Neon PostgreSQL `DATABASE_URL` in production.
- Use `rules-v3`: apply explicit hard filters, score only matching foods, rotate ties, build a family-round-robin 24-item pool, and log conditional softmax probabilities; defer GNN and pgvector.
- Treat multiple selections within one filter group as OR and non-empty filter groups as AND; an empty group means unrestricted.
- Preserve anonymous device-local use, but attach authenticated requests to a server-owned Django account identity for durable history.
- Use revocable DRF tokens for the first account slice; migrate to an HttpOnly secure-cookie flow before a broader public launch.
- Deploy the monorepo as separate Nuxt and Django Vercel projects connected to the same GitHub repository.
- Do not install Astryx React runtime into Nuxt; carry over its verified interaction and accessibility guidance.
