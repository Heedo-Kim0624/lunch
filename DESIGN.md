# Project Design

## Goal

개인화 점심 추천기 개발 세팅 및 MVP 시작

## Context From Knowledge Base

- Preflight brief: ready; no domain-specific prior project was attached.
- Workspace snapshot: `.agentos/PREFLIGHT.md`
- Knowledge Index hits: unrelated project-process references only; no lunch recommender truth imported.
- Graphify report: not yet useful because the application source did not exist at kickoff.
- Relevant playbooks: project Genesis and Spec -> Test -> Code -> Review -> Ship.

## Archetype-Specific Plan

- Kind: inventory-project
- Archetype: inventory-project
- Related playbook: [[Project Workspace Kickoff]]

## Brain-like Loop And Pivot Policy

- Operating loop: sense -> gate -> infer -> select -> execute -> verify -> consolidate -> adapt.
- Current inferred user intent: create the development environment and begin an executable personalized lunch recommender MVP.
- Expected outcome / prediction: a local vertical slice from lever interaction to persisted recommendation feedback passes automated checks.
- Prediction-error signals to watch: Python launcher collision, Nuxt/Node compatibility, feedback ownership bugs, and overbuilding ML before interaction data.
- Harness updates needed if the project pivots: change the archetype from generated inventory-project to full-stack application in a later harness pivot.
- Token strategy: compact maps first, raw evidence only for gaps or source verification.

### Design Questions

- What outcome, scope, evidence, risks, and verification gates define this project?

### Evidence To Capture

- Web, PDF, YouTube, GitHub, meeting, chat, selected local document, and desktop evidence that directly supports this project.

## Scope

- In scope: Nuxt UI, Django API, local and Neon persistence, seed foods, explainable rules recommendation, account authentication, event logging, tests, and Vercel deployment.
- Out of scope: GNN, pgvector, restaurant availability, payment, email verification, and social login.

## Architecture / Workflow

- Main components: Nuxt client, Django REST API, authentication, recommendation service, Django ORM database.
- Data flow: optional account session -> lever -> recommendation request -> scored candidate -> exposure -> explicit feedback event.
- External systems: npm and Python package registries during setup, GitHub, Vercel, and Neon for production.
- Files or modules likely touched: `frontend/`, `backend/`, `scripts/`, project docs and quality gates.

## Risks

- Secrets/privacy boundary: no `.env` reads; only non-secret local defaults and `.env.example`.
- Missing evidence: no real user interaction or restaurant availability data yet.
- Test or verification gaps: browser E2E is deferred from the first slice.
- Repeated blocker or prediction-error risk: the global `python` command points to an unrelated Hermes venv; run backend commands from `backend/` through its uv-managed Python 3.12 environment.

## Decisions

- Decision: rules plus exploration before GNN.
- Reason: the product currently has content attributes but no collaborative behavior graph.
- Alternatives considered: HGT + LightGCN at launch, a pure random picker, and a single Nuxt full-stack service.
