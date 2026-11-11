import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "handbook_chunks"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
EMBEDDING_DIM = 384  # bge-small output size
# BGE models work better when queries (not documents) get this prefix
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# Chunking
MAX_CHUNK_CHARS = 1800   # roughly 400-450 tokens
OVERLAP_CHARS = 200
MIN_CHUNK_CHARS = 120

# Who may read which department (used for RBAC)
ROLES = ["employee", "manager", "engineer", "hr", "finance", "security", "admin"]
DEPARTMENT_ACCESS = {
    "general": ROLES,
    "hr": ["hr", "manager", "admin"],
    "engineering": ["engineer", "admin"],
    "security": ["security", "engineer", "admin"],
    "finance": ["finance", "admin"],
}

# ---- LLM (any OpenAI-compatible provider) ----
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")

# ---- Retrieval / answering ----
CANDIDATES_K = 8          # chunks fetched from Qdrant
CONTEXT_K = 5             # chunks given to the LLM
# If the best chunk scores below this, we refuse instead of guessing.
# Tune it by looking at scores for in-scope vs out-of-scope questions.
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.55"))
