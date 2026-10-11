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

# Who may read which department (used for RBAC in Phase 5)
ROLES = ["employee", "manager", "engineer", "hr", "finance", "security", "admin"]
DEPARTMENT_ACCESS = {
    "general": ROLES,
    "hr": ["hr", "manager", "admin"],
    "engineering": ["engineer", "admin"],
    "security": ["security", "engineer", "admin"],
    "finance": ["finance", "admin"],
}
