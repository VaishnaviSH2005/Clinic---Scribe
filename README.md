# CliniScribe AI

AI Clinical Decision Support System for Doctor–Patient Conversations.

This repository is the production foundation for CliniScribe AI, built per the
Product Requirements Document (`CliniScribe_AI_PRD.pdf` + `PRD_Chapters_15-20.md`).

## Milestone 1 — Foundation (current)

This milestone establishes the project skeleton only: monorepo structure, frontend
and backend scaffolding, database schema/migrations, AI service structure, Docker,
linting/formatting, and the global design system tokens. **No business modules**
(auth, patients, consultations, AI features, reports, analytics, settings) are
implemented yet — those arrive in later milestones.

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

### Local development

```bash
cp .env.example .env
docker compose -f infrastructure/docker/docker-compose.yml up -d postgres redis
cd backend && pip install -r requirements.txt && alembic upgrade head && uvicorn app.main:app --reload
cd frontend && pnpm install && pnpm dev
```

Or run everything via Docker Compose:

```bash
docker compose -f infrastructure/docker/docker-compose.yml up --build
```
