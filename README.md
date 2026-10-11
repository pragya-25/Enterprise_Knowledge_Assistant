# Enterprise Knowledge Assistant

RAG-based assistant that answers employee questions from internal documents,
with citations and role-based access control.

## Phase 1 setup

```bash
# 1. Environment
cp .env.example .env            # then edit the password (and match it in DATABASE_URL)
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Start infrastructure
docker compose up -d
python scripts/check_services.py     # expect three [OK] lines

# 3. Get data
python scripts/download_handbook.py --list-folders   # optional: see what exists
python scripts/download_handbook.py
```

## Structure

```
app/ingestion/   parse, chunk, embed, store      (Phase 2)
app/retrieval/   hybrid search, rerank           (Phase 3)
app/api/         FastAPI routes                  (Phase 4)
app/core/        config, security, RBAC          (Phase 4-5)
app/db/          Postgres models                 (Phase 4)
scripts/         one-off utilities
data/raw/        downloaded documents (git-ignored)
tests/           tests
frontend/        UI                              (Phase 6)
```
