"""P0-F — document download authentication contract.

Bearer credentials are accepted only through the Authorization header.
Query-string tokens must never authenticate document or RVG downloads because
URLs leak through history, logs, referrers and monitoring layers.
"""


def _access_token(auth_headers: dict[str, str]) -> str:
    scheme, token = auth_headers["Authorization"].split(" ", 1)
    assert scheme == "Bearer"
    return token


def test_document_download_rejects_query_token(client, auth_headers):
    token = _access_token(auth_headers)
    client.cookies.delete("access_token")
    response = client.get(f"/api/documents/999999/download?token={token}")
    assert response.status_code == 401


def test_document_download_accepts_bearer_header(client, auth_headers):
    # A non-existent document is intentional: 404 proves authentication passed
    # and execution reached the document lookup instead of failing at auth.
    response = client.get("/api/documents/999999/download", headers=auth_headers)
    assert response.status_code == 404


def test_document_download_rejects_revoked_bearer_token(client, dentiste):
    login = client.post(
        "/api/auth/login",
        data={"username": dentiste.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200
    tokens = login.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    logout = client.post(
        "/api/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=headers,
    )
    assert logout.status_code == 204

    response = client.get("/api/documents/999999/download", headers=headers)
    assert response.status_code == 401


def test_preview_url_contract_is_signed_and_non_persistent():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "routers" / "documents.py").read_text(encoding="utf-8")
    assert "create_document_preview_token" in source
    assert "preview_token=" in source
    assert "if preview and isinstance(pdf_url, str)" in source
