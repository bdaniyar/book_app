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

## Import real book data

Run migrations before importing because imported books store their external source/id:

```bash
alembic upgrade head
```

### Open Library catalog data

Open Library is the easiest source for app catalog data because it has a public API and does not require an API key.

```bash
python3 -m app.scripts.import_books openlibrary \
  --subject fiction \
  --subject fantasy \
  --subject science_fiction \
  --limit 50
```

Use `--update-existing` if you want to refresh already imported rows.

### Goodreads/Goodbooks CSV for ML experiments

Download a `books.csv` style dataset locally, then import it:

```bash
python3 -m app.scripts.import_books goodreads-csv /path/to/books.csv \
  --genre Imported \
  --limit 1000
```

This path is useful for recommendation ML because those datasets often include ratings/interactions that can be used for offline experiments.
