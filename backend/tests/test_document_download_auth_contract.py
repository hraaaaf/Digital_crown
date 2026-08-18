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
    response = client.get(f"/api/documents/999999/download?token={token}")
    assert response.status_code == 401


def test_document_download_accepts_bearer_header(client, auth_headers):
    # A non-existent document is intentional: 404 proves authentication passed
    # and execution reached the document lookup instead of failing at auth.
    response = client.get("/api/documents/999999/download", headers=auth_headers)
    assert response.status_code == 404
