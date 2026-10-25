# CliniScribe AI

A multi-tenant clinic platform that turns a doctor–patient conversation into structured clinical documentation. A recorded consultation is transcribed, cleaned, mined for medical entities, and turned into a SOAP note, a clinical summary and recommendations by an LLM. The doctor reviews and edits the output before it is saved.

> **Status: portfolio / learning project.** It is not a certified medical device and has not been security-reviewed for real patient data. See [Known limitations](#known-limitations) before deploying anything.

## What it does

- **Consultation workflow:** patients, appointments and consultations, with audio upload per consultation.
- **AI documentation pipeline:** speech-to-text → transcript cleaning → entity extraction → SOAP note → clinical summary → recommendations. Every stage is stored on its own, so a failed stage can be retried without redoing the others, and an AI failure never blocks the doctor.
- **Multi-tenant hospitals:** hospitals, departments, doctors and receptionists, with every query scoped to the user's hospital.
- **Role-based access:** `super_admin`, `hospital_admin`, `doctor` and `receptionist`.
- **Reports and analytics:** PDF report generation, dashboard and analytics views, global search.
- **Operations:** audit logs, notifications, per-hospital settings, subscription / license management.

## Architecture

```
frontend (Next.js) ──HTTP──▶ backend (FastAPI) ──▶ PostgreSQL (+ pgvector)
                                   │
                                   ├──▶ Redis (rate limiting, AI job queue)
                                   │
                                   └─ AI job ─▶ worker ──▶ ai-services (speech, NLP, prompts, Claude)
```

| Folder | What's in it |
|---|---|
| `frontend/` | Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, Zustand, React Hook Form + Zod |
| `backend/` | FastAPI, SQLAlchemy 2, Alembic migrations, layered API → service → repository code, background workers |
| `ai-services/` | Speech-to-text (faster-whisper), medical entity extraction, versioned prompt templates, Claude provider |
| `infrastructure/` | Docker Compose (Postgres + pgvector, Redis, API, worker, frontend) and an nginx config |

The AI dependencies (faster-whisper and others) are installed only in the `worker` image, so the API image stays small.

### Security design

- Passwords hashed with **Argon2id**; access tokens are short-lived JWTs.
- Refresh tokens are stored only as hashes, delivered in `HttpOnly` cookies, and **rotated** on every refresh.
- Redis-backed rate limiting that fails open if Redis is down.
- Tenant isolation: repositories filter by `hospital_id`.
- AI stage failures and key actions are recorded in an audit log.

## Quick start (Docker)

Requires Docker with Compose.

```bash
# 1. Configuration
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
# Edit backend/.env: set JWT_SECRET to a long random value.
# Set CLAUDE_API_KEY to enable the AI stages (without it they fail and can be retried).

# 2. Start everything
docker compose -f infrastructure/docker/docker-compose.yml up --build

# 3. Create the schema (first run only)
docker compose -f infrastructure/docker/docker-compose.yml exec backend alembic upgrade head
```

- App: http://localhost:3000
- API docs: http://localhost:8000/docs

The migrations also create **development-only seed accounts and demo data**. Their credentials are listed in `backend/.env.example`. They are for local use only; see below.

## Local development without Docker

```bash
# Postgres and Redis only
docker compose -f infrastructure/docker/docker-compose.yml up -d postgres redis

# Backend (Python 3.12+)
cd backend
pip install -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (Node 20+, pnpm)
cd frontend
pnpm install
pnpm dev
```

To run the AI worker locally as well: `pip install -r ai-services/requirements.txt`, then `python -m app.workers.pipeline_worker` from `backend/`.

## Tests and checks

```bash
cd backend && pytest        # 40 tests, no database or Redis needed
cd backend && ruff check app --extend-ignore E501   # one known long line, see CI
cd frontend && pnpm lint && pnpm typecheck
```

The backend tests cover token and password security, rate limiting, the AI pipeline stages and the Claude client's JSON handling (with a fake Redis and mocked responses), health checks, search, and PDF report rendering. The same checks run in GitHub Actions on every push and pull request.

## Known limitations

This project has not been through a production security review. Items I know about and plan to fix before any real deployment:

- The migrations seed development accounts (including a super admin) with a documented password, on every environment. These must become opt-in for non-development environments.
- `JWT_SECRET` defaults to a placeholder, `DEBUG` defaults to on and `COOKIE_SECURE` to off. There is no startup check that refuses to boot in production with these defaults.
- Patient identifiers such as the Aadhaar number are returned by the API in clear text; encryption at rest and masking still need to be designed.
- Uploads are validated by the declared content type and size, not by file signature.
- Entity extraction uses a curated keyword matcher, not a clinical NLP model; the `embeddings/` module and pgvector are reserved for later and not used yet.
- The frontend has no automated tests yet.

## License

MIT. See [LICENSE](LICENSE).
