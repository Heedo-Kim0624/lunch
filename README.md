# Lunch Machine

레버를 한 번 당기면 음식 하나를 제안하고, 수락과 재추천 행동을 다음 추천에 반영하는 개인화 점심 추천기입니다.

현재 버전은 Nuxt 4 UI, Django REST API, 이메일 회원가입·로그인, 342개 점심 메뉴, 온도·종류·나라·맵기 다중 필터, 음식군 다양성을 보장하는 규칙 기반 `rules-v3` 추천 정책, 계정별 이벤트 로그를 포함합니다. GNN과 pgvector는 데이터가 필요성을 증명할 때까지 포함하지 않습니다.

- Live web: <https://lunch-web-ten.vercel.app>
- Live API health: <https://lunch-api-mocha.vercel.app/api/v1/health>
- GitHub: <https://github.com/Heedo-Kim0624/lunch>

## Stack

- Frontend: Nuxt 4, Vue, TypeScript, Vitest, ESLint
- Backend: Django 5.2 LTS, Django REST Framework, pytest, Ruff
- Database: SQLite zero-setup local default, PostgreSQL 17 / Neon production
- Deployment: GitHub Actions, Vercel (frontend + API), Neon Postgres
- Runtime: Node 24, uv-managed CPython 3.12

## Quick Start

PowerShell에서 다음을 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

터미널 두 개에서 서버를 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-backend.ps1
```

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-frontend.ps1
```

브라우저에서 `http://127.0.0.1:3000`을 엽니다. API 상태는 `http://127.0.0.1:8000/api/v1/health`에서 확인할 수 있습니다.

## PostgreSQL Development Mode

Docker Desktop이 실행 중일 때 다음 명령으로 로컬 PostgreSQL을 준비합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -Postgres
powershell -ExecutionPolicy Bypass -File .\scripts\run-backend.ps1 -Postgres
```

로컬 전용 DB는 호스트 포트 `5433`을 사용합니다. `compose.yaml`의 기본 자격 증명은 개발 전용이며 운영에 사용할 수 없습니다.

## Verification

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify.ps1
```

이 명령은 Django 시스템 검사, 백엔드·프런트엔드 린트, 단위/API 테스트, Nuxt 타입 검사와 프로덕션 빌드를 실행합니다.

## API

```text
GET  /api/v1/health
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
POST /api/v1/auth/logout
POST /api/v1/recommendations
POST /api/v1/recommendations/{recommendation_id}/feedback
```

로그인 요청은 `Authorization: Token <token>` 헤더를 사용합니다. 로그인 상태에서는 추천과 피드백이 서버가 확인한 계정 ID에 귀속되고, 비로그인 상태에서는 기기 로컬 ID를 사용합니다.

추천 요청의 필터는 같은 그룹 안에서 OR, 서로 다른 그룹 사이에서 AND로 계산합니다. 빈 그룹은 제한하지 않으며, 요청 예시는 [아키텍처 문서](docs/architecture.md)에 있습니다.

## Free Deployment

같은 GitHub 저장소를 Vercel 프로젝트 두 개로 연결하고, Neon 무료 PostgreSQL을 백엔드에 연결합니다. 비밀값을 파일에 내려받지 않는 초기화 절차와 환경변수 표는 [배포 가이드](docs/deployment.md)에 있습니다.

계약 예시는 [docs/architecture.md](docs/architecture.md)에 있습니다.

## Project Operating Docs

- [PRD](docs/prd.md)
- [Architecture](docs/architecture.md)
- [Deployment](docs/deployment.md)
- [Design](docs/design.md)
- [Progress](docs/progress.md)
- [Agent instructions](AGENTS.md)
