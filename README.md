# CliniScribe AI

AI Clinical Decision Support System for Doctor–Patient Conversations.

This repository is the production foundation for CliniScribe AI, built per the
Product Requirements Document (`CliniScribe_AI_PRD.pdf` + `PRD_Chapters_15-20.md`).

## Status (verified 2026-11-17)

Milestones 1-8 are implemented: auth + RBAC with hospital-level data isolation, patients,
appointments, consultations (record -> live captions -> transcribe -> AI documentation ->
doctor review -> approval), PDF reports, notifications, dashboards, platform and hospital
analytics, audit logs, settings, subscriptions, and production hardening.

| Check | Result |
|---|---|
| Backend unit tests (`pytest app/tests`) | 110 passed |
| `ruff`, `mypy` (142 files), `tsc`, ESLint, Prettier | all clean |
| Full A-to-Z live-stack test (`backend/e2e/run_e2e.py`: onboarding by email, RBAC matrix, tenant isolation, consultation -> AI -> report -> notifications, frontend pages) | 202 passed |
| Live captions, real WebSocket (`backend/e2e/live_ws_test.py`) | security + ordering + delay verified |
| Live captions, real Chrome with a fake microphone (`backend/e2e/browser_live.js`) | 13 passed |
| SOAP note / clinical summary / recommendations | need `CLAUDE_API_KEY` (verified end to end against a local stand-in for the Claude API; they fail gracefully and are retryable until a real key is set) |

**Access** follows the PRD Ch6.15 matrix. Super Admin can view Patients and Reports of one chosen
hospital at a time, read-only, and every such view is audit-logged; Receptionist can view (not
edit) Reports; Consultations are Doctor-only; Hospital Admin sees their own hospital's audit log.

**Live captions** (PRD Ch9.6): while recording, audio streams to a separate `live_worker` that
captions with a tiny Whisper model - about 3.5 s behind speech on a laptop CPU (the PRD target is
2 s; Whisper's fixed 30 s window makes that unreachable on CPU). They are a preview: the accurate
transcript from the full recording replaces them after Stop. Whisper models are downloaded from
Hugging Face on first use.

**Owner decisions recorded:** appointments in the past require an explicit "book anyway";
department names are unique per hospital; Super Admin "Revenue" is left out (no price data).

Not built yet (PRD items): appointment calendar/queue views, report search + print layout,
analytics KPI set/filters/export, AI patient summary, consultation-history tab, transcript editing,
doctor AI preferences / profile photo, login-page support/privacy/terms links, appointment reminders.
S3 storage is configured but not wired: reports/audio use local disk under `backend/storage`,
which must be a persistent volume in any container deployment.

## Structure

```
cliniscribe-ai/
├── frontend/        Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui
├── backend/          FastAPI + SQLAlchemy + Alembic
├── ai-services/       Speech, NLP, summarization, prompts (structure only)
├── database/          Migrations, seed data, schema docs
├── infrastructure/    Docker, nginx, deployment, monitoring
├── docs/              Documentation
└── scripts/           Dev/ops scripts
```

## Tech Stack

See Chapter 3 of the PRD. Frontend: Next.js 15, TypeScript, Tailwind CSS,
shadcn/ui, TanStack Query, React Hook Form + Zod, Zustand, Framer Motion, Recharts.
Backend: FastAPI, Python 3.12+ (3.10 used locally where 3.12 is unavailable),
SQLAlchemy, Alembic, PostgreSQL + pgvector, Redis.

## Getting Started

### Prerequisites
- Node.js 20+, pnpm
- Python 3.12+
- Docker & Docker Compose

### Local development (Windows, one command)

```powershell
# 1. one-time: backend\.env from backend\.env.example (set CLAUDE_API_KEY), Docker Desktop running
# 2. start everything (DB + Redis, migrations, API :8000, AI worker, frontend :3000)
powershell -ExecutionPolicy Bypass -File scripts\dev-start.ps1
```

Manual equivalent:

```bash
docker compose -f infrastructure/docker/docker-compose.yml up -d postgres redis mailpit
cd backend && pip install -r requirements.txt -r ../ai-services/requirements.txt && alembic upgrade head
uvicorn app.main:app --reload                       # API  :8000
python -m app.workers.pipeline_worker               # AI worker (separate terminal)
python -m app.workers.live_worker                   # live caption worker (separate terminal)
cd frontend && pnpm install && pnpm dev             # UI   :3000
```

The AI worker is required: without it consultations stay in `ai_processing`.
Emails (staff invitations, password resets) are caught by Mailpit in development:
open http://localhost:8025. A consultation stranded in `ai_processing` (worker crash,
Redis restart) is re-queued automatically by the worker.

Or run everything via Docker Compose:

```bash
docker compose -f infrastructure/docker/docker-compose.yml up --build
```
