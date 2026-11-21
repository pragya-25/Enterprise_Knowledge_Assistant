"""
Access-control tests. Run with Qdrant up and the data ingested:

    python -m pytest tests -v
"""
import pytest
from fastapi.testclient import TestClient

from app.core.config import ROLES
from app.retrieval.pipeline import retrieve_mode

QUERIES = [
    "salary bands for engineers",
    "Q3 budget overrun",
    "performance improvement plan summary",
    "restructuring severance",
    "open critical vulnerabilities",
    "anti-harassment policy",
    "incident response process",
]


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("mode", ["vector", "hybrid"])
def test_results_always_match_role(role, mode):
    """Every returned chunk must be readable by the requesting role."""
    for q in QUERIES:
        for chunk in retrieve_mode(q, role, mode, 10):
            assert role in chunk["allowed_roles"], (role, q, chunk["source"])


def test_employee_cannot_see_confidential_files():
    for q in QUERIES:
        for chunk in retrieve_mode(q, "employee", "hybrid", 10):
            assert not chunk["source"].startswith("synthetic__")


def test_finance_can_see_salary_bands():
    sources = [c["source"] for c in retrieve_mode("salary bands for engineers", "finance", "hybrid", 5)]
    assert any(s.startswith("synthetic__salary-bands") for s in sources)


def test_hr_cannot_see_finance_documents():
    for chunk in retrieve_mode("salary bands for engineers", "hr", "hybrid", 10):
        assert not chunk["source"].startswith("synthetic__salary")


# ---- API-level checks (no LLM needed) ----

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "x" * 40)
    from app.api.main import app
    return TestClient(app)


def test_chat_requires_login(client):
    assert client.post("/chat", json={"question": "hello there"}).status_code in (401, 403)


def test_invalid_token_rejected(client):
    r = client.post("/chat", json={"question": "hello there"},
                    headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401
