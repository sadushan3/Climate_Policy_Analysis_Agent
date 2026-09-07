"""End-to-end API tests.

These drive the real application through the real pipeline -- upload, background
analysis, comparison, retrieval -- with no mocking of the NLP layer. Slower than
unit tests, and worth it: they are the only thing that catches a wiring mistake
between two components that are each individually correct.

The LLM layer is absent here (no API key in the test environment), which also
verifies the graceful-degradation contract holds.
"""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture(scope="module")
def client(isolated_data_dir):
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def auth(client):
    from tests.conftest import register_and_authenticate

    return register_and_authenticate(client, "api-tests@example.com")


def _upload(client: TestClient, auth: dict, name: str, text: str) -> str:
    response = client.post(
        "/api/v1/documents",
        files={"file": (name, text.encode(), "text/plain")},
        headers=auth,
    )
    assert response.status_code == 202, response.text
    body = response.json()
    doc_id = body["document"]["id"]

    if body.get("job_id"):
        _await_job(client, auth, body["job_id"])
    return doc_id


def _await_job(client: TestClient, auth: dict, job_id: str, timeout: float = 180.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/api/v1/jobs/{job_id}", headers=auth)
        assert response.status_code == 200, response.text
        state = response.json()
        if state["status"] == "succeeded":
            return client.get(f"/api/v1/jobs/{job_id}/result", headers=auth).json()
        if state["status"] == "failed":
            pytest.fail(f"job failed: {state['error']}")
        time.sleep(0.25)
    pytest.fail(f"job {job_id} did not finish within {timeout}s")


# --------------------------------------------------------------------------

def test_health(client):
    body = client.get("/health").json()
    assert body["status"] in {"ok", "warming"}
    assert body["environment"] == "test"
    assert body["llm_enabled"] is False  # no key in the test environment


def test_taxonomy_is_exposed(client):
    """Public: the classification scheme is not sensitive and the UI reads it
    before a user has signed in."""
    dimensions = client.get("/api/v1/taxonomy").json()["dimensions"]
    assert len(dimensions) == 9
    assert all(d["prototype_count"] > 0 for d in dimensions)


def test_rejects_unsupported_file_type(client, auth):
    response = client.post(
        "/api/v1/documents",
        files={"file": ("payload.exe", b"MZ", "application/octet-stream")},
        headers=auth,
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_file_type"


def test_missing_document_returns_structured_404(client, auth):
    response = client.get("/api/v1/documents/does-not-exist", headers=auth)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_request_id_header_is_returned(client):
    response = client.get("/health", headers={"X-Request-ID": "trace-me"})
    assert response.headers["X-Request-ID"] == "trace-me"


# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def documents(client, auth):
    from tests.conftest import POLICY_A, POLICY_B

    return {
        "a": _upload(client, auth, "policy_a.txt", POLICY_A),
        "b": _upload(client, auth, "policy_b.txt", POLICY_B),
    }


def test_upload_produces_full_analysis(client, auth, documents):
    body = client.get(f"/api/v1/documents/{documents['a']}", headers=auth).json()
    assert body["status"] == "ready"

    analysis = body["analysis"]
    stats = analysis["statistics"]
    assert stats["chunk_count"] > 0
    assert stats["word_count"] > 100

    # The document commits to net zero, a 45% cut and USD 12.6bn; the pipeline
    # must find quantified targets rather than reporting that "billion" occurred.
    assert stats["target_count"] > 0
    target_types = {t["target_type"] for t in analysis["targets"]}
    assert "net_zero" in target_types
    assert "emissions_reduction" in target_types

    # Multiple policy dimensions, each with page-cited evidence.
    assert stats["dimensions_covered"] >= 4
    for dimension in analysis["dimensions"]:
        for evidence in dimension["evidence"]:
            assert evidence["page_start"] >= 1

    # Without an API key the summary must still exist, via the extractive path.
    assert analysis["summary"]
    assert analysis["summary_method"] == "extractive"


def test_duplicate_upload_is_deduplicated(client, auth, documents):
    from tests.conftest import POLICY_A

    response = client.post(
        "/api/v1/documents",
        files={"file": ("again.txt", POLICY_A.encode(), "text/plain")},
        headers=auth,
    )
    body = response.json()
    assert body["deduplicated"] is True
    assert body["document"]["id"] == documents["a"]
    assert body["job_id"] is None


def test_document_list_and_chunks(client, auth, documents):
    listing = client.get("/api/v1/documents", headers=auth).json()
    assert {d["id"] for d in listing} >= set(documents.values())

    chunks = client.get(f"/api/v1/documents/{documents['a']}/chunks", headers=auth).json()
    assert chunks["total"] > 0
    assert all(c["page_start"] >= 1 for c in chunks["chunks"])


def test_hybrid_search_returns_cited_passages(client, auth, documents):
    response = client.post(
        "/api/v1/search",
        json={"query": "how much money is committed to adaptation", "doc_ids": [documents["a"]], "top_k": 5},
        headers=auth,
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    assert all(r["citation"] for r in results)
    # The finance section should surface for a finance question.
    assert any("billion" in r["text"] or "million" in r["text"] for r in results)


def test_search_finds_rare_literal_tokens(client, auth, documents):
    """The case that motivates hybrid retrieval: a pure dense retriever is
    unreliable on rare literal strings like a specific figure."""
    response = client.post(
        "/api/v1/search",
        json={"query": "120 km shoreline coastal protection", "doc_ids": [documents["a"]], "top_k": 5},
        headers=auth,
    )
    assert any("120 km" in r["text"] for r in response.json()["results"])


def test_ask_degrades_honestly_without_api_key(client, auth, documents):
    """No key must mean 'here are the passages, ungrounded' -- never a fabricated
    answer presented as grounded."""
    response = client.post(
        "/api/v1/ask",
        json={"question": "What is the net zero target year?", "doc_ids": [documents["a"]]},
        headers=auth,
    )
    body = response.json()
    assert body["answer_source"] == "retrieval_only"
    assert body["grounded"] is False
    assert body["sources"]


def test_compare_two_documents(client, auth, documents):
    response = client.post(
        "/api/v1/compare",
        json={"doc_id_a": documents["a"], "doc_id_b": documents["b"]},
        headers=auth,
    )
    assert response.status_code == 202
    result = _await_job(client, auth, response.json()["job_id"])["result"]

    assert 0.0 <= result["similarity"]["overall"] <= 1.0
    assert result["alignment"]["pairs"], "no passages aligned between two climate policies"
    assert result["dimensions"]

    # Policy A has a 2050 net zero date, Policy B has 2060 -- A is more ambitious.
    net_zero = next((r for r in result["targets"] if r["target_type"] == "net_zero"), None)
    assert net_zero is not None
    assert net_zero["verdict"] == "stronger_a"

    # B covers just transition and technology; A does not.
    verdicts = {r["key"]: r["verdict"] for r in result["dimensions"]}
    assert verdicts.get("equity") in {"only_b", "stronger_b"}

    # No key configured, so there is no narrative -- and that is reported, not faked.
    assert result["narrative"] is None
    assert result["narrative_source"] == "unavailable"


def test_compare_rejects_identical_documents(client, auth, documents):
    response = client.post(
        "/api/v1/compare",
        json={"doc_id_a": documents["a"], "doc_id_b": documents["a"]},
        headers=auth,
    )
    assert response.status_code == 422


def test_delete_document(client, auth):
    from tests.conftest import POLICY_B

    doc_id = _upload(client, auth, "temporary.txt", POLICY_B.replace("2040", "2041"))
    assert client.delete(f"/api/v1/documents/{doc_id}", headers=auth).status_code == 204
    assert client.get(f"/api/v1/documents/{doc_id}", headers=auth).status_code == 404
