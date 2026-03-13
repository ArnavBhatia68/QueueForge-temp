# QueueForge

QueueForge is a production-grade, distributed background job processing platform with a polished, real-time administrative dashboard.

QueueForge demonstrates a modern approach to asynchronous architectural patterns. It features an API-driven control plane, robust Python workers, Redis message passing, and a sleek Next.js (App Router) interface. 

![QueueForge Architecture](./docs/architecture.png)

## Why It Matters
Modern SaaS applications rely heavily on background processing to keep web requests fast and reliable. QueueForge implements common patterns seen in production platforms like Celery, BullMQ, or Sidekiq but consolidates the control plane and visibility into an easy-to-deploy package with a premium user experience.

## Architecture

```mermaid
graph TD
    A[Web Client (Next.js)] -->|REST API (FastAPI)| B(API Service)
    B -->|State / Logs| C[(PostgreSQL)]
    B -.->|Enqueue Job ID| D[(Redis Broker)]
    E[Worker Node (Python)] -.->|BLPOP| D
    E -->|Execute Handlers| F[Job Logic]
    E -->|Update Status| C
```

## Tech Stack
**Frontend (Web Dashboard)**
- Framework: Next.js 15 (App Router)
- Language: TypeScript
- UI/Styling: Tailwind CSS, shadcn/ui
- State & Data Fetching: Zustand, React Query `@tanstack/react-query`

**Backend (API & Worker)**
- Frameworks: FastAPI
- Database ORM: SQLAlchemy (Async), Alembic
- Language: Python 3.12
- Message Broker: Redis (`redis-py`)

**Infrastructure**
- Database: PostgreSQL
- Containerization: Docker, docker-compose
- CI: GitHub Actions

---

## Features
- **Job Lifecycle Management**: Enqueue, monitor, retry, or cancel jobs with full observability.
- **Real-Time Dashboard**: 7-day job volume chart, live KPIs, and a live activity feed — all polling the real backend API.
- **Robust Worker Architecture**: Python worker nodes asynchronously pull from Redis queues, execute handlers, and persist granular execution logs to PostgreSQL.
- **Multi-Queue Routing**: Route tasks to isolated named queues (`default`, `emails`, `reports`, `ml_pipeline`).
- **Resilience**: Auto-retries with configurable limits and exponential backoff mechanisms.
- **Alembic Migrations**: Versioned schema migrations (`alembic/versions/e161f3005cc9_initial_schema.py`) — `alembic upgrade head` re-runs cleanly on an empty database.

## Local Setup
QueueForge uses Docker Compose for infrastructural dependencies and requires Node 18+ and Python 3.12+.

### 1. Database & Broker
Launch PostgreSQL and Redis in the background. The Postgres database maps to host port `5434` to prevent conflicts with local database installations.
```bash
docker-compose up -d
```

### 2. Configure Environment
Copy the example environment securely. All services are hardcoded in `.env.example` to point to the correct port mappings (`127.0.0.1:5434`, `127.0.0.1:6379`, `127.0.0.1:8001`).
```bash
cp .env.example .env
```

### 3. Setup Backend API
The FastAPI backend serves the frontend proxy and administrates the database schema.
```bash
cd apps/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run migrations to build the tables
PYTHONPATH=. alembic upgrade head

# Seed sample data for local development (optional)
PYTHONPATH=. python scripts/seed.py

# Start the API server on :8001
PYTHONPATH=. uvicorn main:app --reload --port 8001
```

### 4. Start the Worker Service
The background Python worker daemonizes a Redis polling loop to consume payloads asynchronously.
Open a new terminal tab and run:
```bash
cd apps/worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the worker logger and dispatcher
PYTHONPATH=. python main.py
```

### 5. Launch the Web Dashboard
```bash
cd apps/web
npm install
npm run dev
```

Visit `http://localhost:3000` and create a user with `POST /api/v1/auth/register` (or seed local sample data for quick exploration).

## Deployment (Track A: Vercel + Railway)
QueueForge is structurally ready for cloud deployments. This architecture splits the Next.js frontend to Vercel and the Python backend services to Railway.

### 1. Database & Redis (Railway / Neon / Upstash)
Provision a PostgreSQL database and a Redis instance. Railway provides native plugins for both, or use Neon (Postgres) and Upstash (Redis).

### 2. API Service (Railway)
Create a new service in Railway pointing to this repository.
- **Root Directory:** `/apps/api`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT` (Auto-detected via `Procfile`)

**Environment Variables Required:**
| Variable | Example | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:port/db` | Railway provides `postgresql://`; you **must** change it to `postgresql+asyncpg://` for the async engine. |
| `REDIS_URL` | `redis://default:pass@host:port` | Connection to Redis broker |
| `JWT_SECRET` | `your_secure_random_string` | Must match across API and Worker (if worker needs it) |
| `FRONTEND_URL` | `https://queueforge.vercel.app` | **Critical for CORS:** Must match your Vercel deployment URL exactly |

### 3. Worker Service (Railway)
Create a second service in Railway pointing to this repository.
- **Root Directory:** `/apps/worker`
- **Start Command:** `python main.py` (Auto-detected via `Procfile`)

**Environment Variables Required:**
| Variable | Example | Description |
|---|---|---|
| `DATABASE_URL` | Same as API | Worker must read/write to the exact same Postgres DB |
| `REDIS_URL` | Same as API | Worker must poll the exact same Redis instance |

### 4. Web Dashboard (Vercel)
Import the repository into Vercel.
- **Root Directory:** `apps/web`
- **Framework Preset:** Next.js (Auto-detected)

**Environment Variables Required:**
| Variable | Example | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://queueforge-api.railway.app/api/v1` | URL of the Railway API service *with* the `/api/v1` suffix |

## API Summary
JWT-authenticated REST API:
- `GET /health` — Liveness probe for API process
- `GET /health/deep` — Readiness probe that verifies PostgreSQL + Redis connectivity
- `POST /api/v1/auth/login` — Obtain access token
- `GET /api/v1/jobs` — List jobs (optional `?status=` / `?queue_name=` filters)
- `POST /api/v1/jobs` — Enqueue a new job
- `GET /api/v1/jobs/{id}` — Retrieve job details and execution logs
- `POST /api/v1/jobs/{id}/retry` — Re-enqueue a failed job
- `POST /api/v1/jobs/{id}/cancel` — Cancel a queued job
- `GET /api/v1/analytics/overview` — Platform KPIs
- `GET /api/v1/analytics/daily` — Last 7 days of job counts by status (used by the dashboard chart)
- `GET /api/v1/analytics/recent` — Last 10 jobs across all queues (used by the activity feed)

## Database Migrations
Schemas are managed with Alembic. A proper versioned revision is included at `apps/api/alembic/versions/e161f3005cc9_initial_schema.py`.

```bash
# Apply migrations to an empty database
cd apps/api && PYTHONPATH=. alembic upgrade head

# After model changes, generate a new revision
cd apps/api && PYTHONPATH=. alembic revision --autogenerate -m "your_change_description"
```

## Future Enhancements
- CRON schedule triggers for recurring jobs.
- WebSocket streaming for dashboard updates (currently uses smart polling).
- Complex DAG (Directed Acyclic Graph) workflow dependencies.


## Production Readiness Checklist
- Configure unique strong secrets and service credentials (`JWT_SECRET`, Postgres, Redis).
- Set `FRONTEND_URL` and `NEXT_PUBLIC_API_URL` to deployed domains.
- Run migrations in the deployed environment before first boot.
- Disable demo-only login hints (`NEXT_PUBLIC_SHOW_DEMO_CREDENTIALS` should be unset).
- Replace sample worker handlers with your business-specific handlers.
- Add automated integration tests for your critical job types and API flows.
- Frontend now uses system fonts to keep builds deterministic in restricted CI/network environments.
