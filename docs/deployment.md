# Free Production Deployment — GitHub + Vercel + Neon

## Current production

- Web: `https://lunch-web-ten.vercel.app`
- API: `https://lunch-api-mocha.vercel.app`
- API health: `https://lunch-api-mocha.vercel.app/api/v1/health`
- Database: Neon free plan, Singapore region

The repository is a monorepo deployed as two Vercel projects. The frontend project uses `frontend/` as its Root Directory; the API project uses `backend/`. Vercel detects Nuxt and Django from those directories, so no custom routing file is required.

## 1. Create the Neon database

Create one free Neon project and copy its **pooled** PostgreSQL connection string. Keep it out of files, terminals with command history, screenshots, and GitHub. It becomes the backend's `DATABASE_URL` secret.

## 2. Import the GitHub repository twice in Vercel

Create these projects from the same GitHub repository:

| Project | Root Directory | Framework |
| --- | --- | --- |
| `lunch-web` | `frontend` | Nuxt (auto-detected) |
| `lunch-api` | `backend` | Django (auto-detected from `manage.py`) |

The backend needs these Production environment variables:

```text
DATABASE_URL=<Neon pooled connection string>
DJANGO_SECRET_KEY=<unique random secret>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=.vercel.app
CORS_ALLOWED_ORIGINS=https://<lunch-web-production-host>
```

The frontend needs:

```text
NUXT_PUBLIC_API_BASE=https://<lunch-api-production-host>/api/v1
```

Use the exact generated production hosts, including `https://` for CORS. Preview deployments need their own allowed frontend origin and a database branch before they should be used for writes.

## 3. Initialize the production database

After linking the local CLI to the backend Vercel project, run migrations and the idempotent menu seed without writing secrets to disk:

```powershell
Set-Location backend
vercel env run -e production -- uv run python manage.py migrate --noinput
vercel env run -e production -- uv run python manage.py seed_foods
Set-Location ..
```

`seed_foods` can be run again safely. Do not use SQLite on Vercel; its function filesystem is not persistent and the settings intentionally reject that configuration.

## 4. Verify production

Check the API health endpoint, then create a disposable account through the UI and verify login, recommendation, feedback, logout, and login again:

```text
https://<lunch-api-production-host>/api/v1/health
https://<lunch-web-production-host>/signup
```

Every push to `main` runs GitHub Actions and triggers both connected Vercel projects. Keep the Vercel and Neon projects on personal/non-commercial free plans unless the product becomes commercial or exceeds their quotas.

## Security checklist before inviting real users

- Replace the MVP privacy note with an operator identity, contact channel, retention period, and account-deletion process.
- Add email verification and password reset.
- Move browser authentication from a local-storage token to an HttpOnly secure cookie if the product becomes public-facing beyond a small test group.
- Monitor Vercel function logs and Neon storage/compute usage without logging credentials or password fields.
