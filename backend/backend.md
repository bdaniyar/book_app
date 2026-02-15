# Backend

## How to run (macOS/zsh)

### 1) Create/activate venv & install deps
From the repo root:

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 2) Configure env
Create/edit `backend/.env` and set at least:
- `DATABASE_URL`
- `JWT_SECRET_KEY`

(Optional for tests)
- `TEST_DATABASE_URL`

### 3) Run migrations (first time / after model changes)
```bash
cd backend
alembic upgrade head
```

### 4) Start the API
Run from the `backend` folder:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs
- API prefix: http://localhost:8000/api/v1

### 5) Run tests
```bash
cd backend
pytest
```
