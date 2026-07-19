# Book App

Book App is a full-stack personal reading tracker: catalog search, library
statuses and progress, reviews, personalized recommendations, profile statistics,
and a grounded AI reading assistant.

## Architecture

- `backend/` — FastAPI, SQLAlchemy 2, Alembic, PostgreSQL.
- `frontend/` — Next.js 15, React 19, TypeScript.
- `backend/app/ai/` — assistant orchestration, policy, provider adapter, and
  read-only catalog/profile tools.
- `backend/app/api/v1/endpoints/assistant.py` — authenticated assistant HTTP API.
- `frontend/app/assistant/` — the **Assistant** tab and conversation UI.

The assistant always grounds book suggestions in the local catalog. It runs in a
useful deterministic `local` mode by default. With `AI_PROVIDER=openai` and an
`OPENAI_API_KEY`, generation is delegated to the OpenAI Responses API. Changes to
the user's library are never executed directly from chat: the backend creates an
expiring proposed action, and the user must explicitly confirm it.

## Local setup

Prerequisites: Python 3.12+, Node.js 22+, and PostgreSQL 16+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Create the application and test databases referenced by `backend/.env`, then:

```bash
alembic upgrade head
cd backend && uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. API documentation is at
`http://localhost:8000/docs`; liveness and database readiness endpoints are
`/health/live` and `/health/ready`.

## AI configuration

Local mode requires no API key:

```dotenv
AI_PROVIDER=local
```

For the hosted model:

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-5.6-sol
```

Never put `OPENAI_API_KEY` in `frontend/.env.local`: model calls are made only by
the backend so the secret cannot reach the browser.

## Verification

Tests are deliberately blocked unless `TEST_DATABASE_URL` points to a separate
database whose name clearly looks disposable. This protects development and
production data from the test suite's table cleanup.

```bash
cd backend && pytest
cd ../frontend && npm run lint && npm run build
```

GitHub Actions runs migrations, backend tests, TypeScript validation, and the
production frontend build for every pull request.

## Production checklist

- Use long, independent values for `JWT_SECRET_KEY` and
  `ADMIN_SESSION_SECRET_KEY`.
- Set secure cookies and HTTPS-only origins.
- Keep `ADMIN_ENABLED=false` unless the protected admin interface is needed.
- Run `alembic upgrade head` before deploying a new backend version.
- Configure SMTP if password-reset email should be delivered outside development.
