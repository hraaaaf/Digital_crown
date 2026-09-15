from backend.main import app
from backend.routers.insurance_submissions import get_insurance_source_store_root
from backend.core.media_paths import get_media_root


def test_insurance_submission_routes_are_mounted_under_documents():
    paths = {getattr(route, "path", None) for route in app.routes}
    assert "/api/documents/insurance-submissions/prepare" in paths
    assert "/api/documents/insurance-submissions/validate" in paths
    assert "/api/documents/insurance-submissions/finalize" in paths


def test_insurance_submission_api_uses_canonical_media_source_store():
    assert get_insurance_source_store_root() == get_media_root() / "insurance_sources"


def test_prepare_route_returns_404_for_unknown_honoraires(client, auth_headers):
    response = client.post(
        "/api/documents/insurance-submissions/prepare",
        json={"honoraires_document_id": 999999, "organization": "CNSS"},
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Note d'honoraires introuvable"
