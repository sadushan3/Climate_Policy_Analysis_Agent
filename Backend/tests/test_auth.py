"""Authentication, session lifecycle and tenant isolation.

The isolation tests are the important ones. Auth that merely *has* login is easy;
auth that provably prevents one tenant reading another's data is the thing worth
testing, and retrieval is where such a bug would otherwise be invisible.
"""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

PASSWORD = "correct-horse-battery-staple"


@pytest.fixture(scope="module")
def client(isolated_data_dir):
    with TestClient(create_app()) as test_client:
        yield test_client


def register(client: TestClient, email: str, password: str = PASSWORD) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": email.split("@")[0]},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------
# registration and login
# --------------------------------------------------------------------------

def test_register_returns_token_and_never_the_hash(client):
    body = register(client, "alice@example.com")
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["user"]["email"] == "alice@example.com"
    assert "password_hash" not in body["user"]
    assert "password" not in str(body["user"])


def test_refresh_token_is_httponly_and_not_in_the_body(client):
    """An XSS bug must not be able to steal a long-lived session."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "cookie@example.com", "password": PASSWORD},
    )
    assert "refresh_token" not in response.text
    cookie_header = response.headers.get("set-cookie", "")
    assert "refresh_token=" in cookie_header
    assert "HttpOnly" in cookie_header


def test_duplicate_email_is_rejected(client):
    register(client, "dup@example.com")
    response = client.post(
        "/api/v1/auth/register", json={"email": "DUP@example.com", "password": PASSWORD}
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "email_already_registered"


def test_weak_password_is_rejected(client):
    response = client.post(
        "/api/v1/auth/register", json={"email": "weak@example.com", "password": "short"}
    )
    assert response.status_code == 422
    assert "12 characters" in response.json()["error"]["message"]


def test_common_password_is_rejected(client):
    response = client.post(
        "/api/v1/auth/register", json={"email": "common@example.com", "password": "password123"}
    )
    assert response.status_code == 422


def test_login_succeeds_and_email_is_case_insensitive(client):
    register(client, "case@example.com")
    response = client.post(
        "/api/v1/auth/login", json={"email": "CASE@Example.COM", "password": PASSWORD}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_wrong_password_is_rejected_without_revealing_the_account(client):
    register(client, "known@example.com")
    known = client.post(
        "/api/v1/auth/login", json={"email": "known@example.com", "password": "wrong-password-here"}
    )
    unknown = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.com", "password": "wrong-password-here"}
    )
    assert known.status_code == unknown.status_code == 401
    # Identical wording: the response must not disclose whether the email exists.
    assert known.json()["error"]["message"] == unknown.json()["error"]["message"]


# --------------------------------------------------------------------------
# protected endpoints
# --------------------------------------------------------------------------

def test_endpoints_require_authentication(client):
    for method, path, kwargs in [
        ("get", "/api/v1/documents", {}),
        ("post", "/api/v1/documents", {"files": {"file": ("a.txt", b"hello there", "text/plain")}}),
        ("post", "/api/v1/search", {"json": {"query": "x", "doc_ids": ["d"]}}),
        ("post", "/api/v1/ask", {"json": {"question": "what", "doc_ids": ["d"]}}),
        ("post", "/api/v1/compare", {"json": {"doc_id_a": "a", "doc_id_b": "b"}}),
        ("get", "/api/v1/auth/me", {}),
        ("get", "/api/v1/jobs/anything", {}),
        ("get", "/api/v1/jobs/anything/result", {}),
    ]:
        response = getattr(client, method)(path, **kwargs)
        assert response.status_code == 401, f"{method.upper()} {path} was not protected"


def test_garbage_and_tampered_tokens_are_rejected(client):
    body = register(client, "tamper@example.com")
    valid = body["access_token"]

    for token in [
        "not-a-token",
        valid[:-3] + "aaa",                        # signature no longer verifies
        valid.rsplit(".", 1)[0] + ".",             # stripped signature
        "",
    ]:
        assert client.get("/api/v1/auth/me", headers=auth_header(token)).status_code == 401


def test_me_reports_the_callers_own_document_count(client):
    body = register(client, "counter@example.com")
    response = client.get("/api/v1/auth/me", headers=auth_header(body["access_token"]))
    assert response.status_code == 200
    assert response.json()["document_count"] == 0
    assert response.json()["email"] == "counter@example.com"


# --------------------------------------------------------------------------
# session lifecycle
# --------------------------------------------------------------------------

def test_refresh_rotates_the_token_and_the_old_one_dies(client):
    """Rotation is what bounds the damage from a stolen refresh token."""
    with TestClient(create_app()) as session:
        register(session, "rotate@example.com")
        first_cookie = session.cookies.get("refresh_token")
        assert first_cookie

        refreshed = session.post("/api/v1/auth/refresh")
        assert refreshed.status_code == 200
        assert refreshed.json()["access_token"]

        second_cookie = session.cookies.get("refresh_token")
        assert second_cookie != first_cookie, "refresh token was not rotated"

        # Replaying the superseded token must fail.
        session.cookies.set("refresh_token", first_cookie)
        replay = session.post("/api/v1/auth/refresh")
        assert replay.status_code == 401


def test_reusing_a_revoked_token_kills_every_session(client):
    """Reuse of a rotated token means it leaked, so all sessions are revoked --
    the legitimate user is logged out rather than silently sharing access."""
    with TestClient(create_app()) as session:
        register(session, "breach@example.com")
        stolen = session.cookies.get("refresh_token")

        session.post("/api/v1/auth/refresh")     # legitimate rotation
        live = session.cookies.get("refresh_token")

        session.cookies.set("refresh_token", stolen)
        assert session.post("/api/v1/auth/refresh").status_code == 401

        # The still-current token is now dead too.
        session.cookies.set("refresh_token", live)
        assert session.post("/api/v1/auth/refresh").status_code == 401


def test_logout_revokes_the_session(client):
    with TestClient(create_app()) as session:
        register(session, "logout@example.com")
        assert session.post("/api/v1/auth/logout").status_code == 204
        assert session.post("/api/v1/auth/refresh").status_code == 401


def test_logout_everywhere(client):
    with TestClient(create_app()) as session:
        body = register(session, "everywhere@example.com")
        response = session.post(
            "/api/v1/auth/logout-all", headers=auth_header(body["access_token"])
        )
        assert response.status_code == 200
        assert response.json()["revoked_sessions"] >= 1


def test_login_is_rate_limited(client):
    """Brute force must be throttled, and a legitimate user must not be locked
    out by someone else's failures against a different account."""
    from app.api.deps import login_limiter

    register(client, "brute@example.com")
    login_limiter.reset("account:brute@example.com")
    login_limiter.reset("ip:testclient")

    statuses = [
        client.post(
            "/api/v1/auth/login", json={"email": "brute@example.com", "password": "wrong-guess-1234"}
        ).status_code
        for _ in range(12)
    ]
    assert 429 in statuses, "login endpoint was never throttled"

    login_limiter.reset("account:brute@example.com")
    login_limiter.reset("ip:testclient")


# --------------------------------------------------------------------------
# tenant isolation
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def two_tenants(client):
    from tests.conftest import POLICY_A, POLICY_B

    alpha = register(client, "alpha@tenant.example.com")
    beta = register(client, "beta@tenant.example.com")

    def upload(token: str, name: str, text: str) -> str:
        response = client.post(
            "/api/v1/documents",
            files={"file": (name, text.encode(), "text/plain")},
            headers=auth_header(token),
        )
        assert response.status_code == 202, response.text
        body = response.json()
        if body["job_id"]:
            deadline = time.time() + 180
            while time.time() < deadline:
                state = client.get(f"/api/v1/jobs/{body['job_id']}", headers=auth_header(token)).json()
                if state["status"] == "succeeded":
                    break
                if state["status"] == "failed":
                    pytest.fail(state["error"])
                time.sleep(0.25)
        return body["document"]["id"]

    return {
        "alpha": {"token": alpha["access_token"], "doc": upload(alpha["access_token"], "alpha.txt", POLICY_A)},
        "beta": {"token": beta["access_token"], "doc": upload(beta["access_token"], "beta.txt", POLICY_B)},
    }


def test_library_lists_only_your_own_documents(client, two_tenants):
    alpha_ids = {
        d["id"] for d in client.get("/api/v1/documents", headers=auth_header(two_tenants["alpha"]["token"])).json()
    }
    assert two_tenants["alpha"]["doc"] in alpha_ids
    assert two_tenants["beta"]["doc"] not in alpha_ids


def test_reading_another_tenants_document_is_a_404_not_a_403(client, two_tenants):
    """404 rather than 403: a 403 confirms the id exists, which turns the
    endpoint into an enumeration oracle."""
    response = client.get(
        f"/api/v1/documents/{two_tenants['beta']['doc']}",
        headers=auth_header(two_tenants["alpha"]["token"]),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_cannot_read_another_tenants_chunks(client, two_tenants):
    response = client.get(
        f"/api/v1/documents/{two_tenants['beta']['doc']}/chunks",
        headers=auth_header(two_tenants["alpha"]["token"]),
    )
    assert response.status_code == 404


def test_cannot_delete_another_tenants_document(client, two_tenants):
    response = client.delete(
        f"/api/v1/documents/{two_tenants['beta']['doc']}",
        headers=auth_header(two_tenants["alpha"]["token"]),
    )
    assert response.status_code == 404

    # And it is still there for its owner.
    still_there = client.get(
        f"/api/v1/documents/{two_tenants['beta']['doc']}",
        headers=auth_header(two_tenants["beta"]["token"]),
    )
    assert still_there.status_code == 200


def test_retrieval_cannot_reach_another_tenants_passages(client, two_tenants):
    """The isolation failure that would otherwise be invisible: an unscoped index
    would return the other tenant's text inside a perfectly normal-looking answer."""
    response = client.post(
        "/api/v1/search",
        json={"query": "just transition for coal workers", "doc_ids": [two_tenants["beta"]["doc"]]},
        headers=auth_header(two_tenants["alpha"]["token"]),
    )
    assert response.status_code == 404


def test_ask_cannot_reach_another_tenants_passages(client, two_tenants):
    response = client.post(
        "/api/v1/ask",
        json={"question": "what are the targets", "doc_ids": [two_tenants["beta"]["doc"]]},
        headers=auth_header(two_tenants["alpha"]["token"]),
    )
    assert response.status_code == 404


def test_mixing_your_document_with_a_foreign_one_is_rejected_wholesale(client, two_tenants):
    """Partial success would be worse than failure: it would silently return an
    answer over a smaller corpus than the caller asked for."""
    response = client.post(
        "/api/v1/search",
        json={
            "query": "emissions target",
            "doc_ids": [two_tenants["alpha"]["doc"], two_tenants["beta"]["doc"]],
        },
        headers=auth_header(two_tenants["alpha"]["token"]),
    )
    assert response.status_code == 404


def test_cannot_compare_against_another_tenants_document(client, two_tenants):
    response = client.post(
        "/api/v1/compare",
        json={"doc_id_a": two_tenants["alpha"]["doc"], "doc_id_b": two_tenants["beta"]["doc"]},
        headers=auth_header(two_tenants["alpha"]["token"]),
    )
    assert response.status_code == 404


def test_deduplication_does_not_leak_across_tenants(client):
    """Identical content uploaded by two tenants must produce two documents.

    A global content-hash lookup would tell the second uploader that the file
    already existed -- disclosing that another tenant holds it.
    """
    from tests.conftest import POLICY_A

    one = register(client, "dedupe-one@tenant.example.com")
    two = register(client, "dedupe-two@tenant.example.com")
    payload = POLICY_A.replace("2050", "2051")  # distinct from other fixtures

    first = client.post(
        "/api/v1/documents",
        files={"file": ("shared.txt", payload.encode(), "text/plain")},
        headers=auth_header(one["access_token"]),
    ).json()
    second = client.post(
        "/api/v1/documents",
        files={"file": ("shared.txt", payload.encode(), "text/plain")},
        headers=auth_header(two["access_token"]),
    ).json()

    assert second["deduplicated"] is False
    assert second["document"]["id"] != first["document"]["id"]
