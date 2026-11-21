"""
FastAPI backend.   Run from the project root:

    uvicorn app.api.main:app --port 8000

Interactive docs (with a login button):  http://127.0.0.1:8000/docs
"""
import math
import time
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.core.config import DEPARTMENT_ACCESS
from app.core.security import (create_token, get_current_user, require_admin,
                               verify_password, hash_password)
from app.db.database import init_db
from app.db.users import get_user_by_username, log_query, recent_logs
from app.generation.answer import RETRIEVAL_MODE, answer_question
from app.retrieval.pipeline import retrieve_mode

# Used only to burn the same time when a username doesn't exist (timing safety)
_DUMMY_HASH = hash_password("not-a-real-password")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:   # load the embedding model, BM25 index and reranker once, not on first request
        retrieve_mode("warm up", "admin", RETRIEVAL_MODE, 1)
    except Exception as e:
        print(f"[startup] warm-up skipped: {e}")
    yield


app = FastAPI(title="Enterprise Knowledge Assistant", version="1.0", lifespan=lifespan)


# ---------- schemas ----------

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=10)


class ChatResponse(BaseModel):
    answer: str
    found: bool
    sources: list[dict]
    role: str
    latency_ms: int


# ---------- routes ----------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/login")
def login(req: LoginRequest):
    user = get_user_by_username(req.username)
    ok = verify_password(req.password, user["password_hash"] if user else _DUMMY_HASH)
    if not user or not ok:
        raise HTTPException(401, "Invalid username or password")
    return {"access_token": create_token(user["username"], user["role"]),
            "token_type": "bearer", "username": user["username"], "role": user["role"]}


@app.get("/me")
def me(user=Depends(get_current_user)):
    departments = [d for d, roles in DEPARTMENT_ACCESS.items() if user["role"] in roles]
    return {"username": user["username"], "role": user["role"], "departments": departments}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user=Depends(get_current_user)):
    # `def` (not async): FastAPI runs this in a worker thread, so slow model
    # calls don't block other users.
    start = time.perf_counter()
    result = answer_question(req.question, user["role"],
                             [t.model_dump() for t in req.history])
    latency_ms = int((time.perf_counter() - start) * 1000)

    score = result["top_score"]
    try:
        log_query(user["username"], user["role"], req.question, result["found"],
                  score if math.isfinite(score) else None, latency_ms)
    except Exception as e:      # logging must never break an answer
        print(f"[log] failed: {e}")

    return ChatResponse(answer=result["answer"], found=result["found"],
                        sources=result["sources"], role=user["role"],
                        latency_ms=latency_ms)


@app.get("/admin/logs")
def admin_logs(limit: int = 50, _=Depends(require_admin)):
    return recent_logs(min(max(limit, 1), 200))
