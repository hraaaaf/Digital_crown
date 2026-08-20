from backend.services.qr_document_routes import build_document_qr_url


def test_verify_route_from_origin():
    assert build_document_qr_url("http://localhost:8000", "verify", 42) == "http://localhost:8000/api/documents/verify/42"


def test_track_route_from_origin():
    assert build_document_qr_url("https://cabinet.local/", "track", "DOC-7") == "https://cabinet.local/api/documents/track/DOC-7"


def test_route_does_not_duplicate_api_documents():
    assert build_document_qr_url("https://cabinet.local/api/documents", "verify", 9) == "https://cabinet.local/api/documents/verify/9"
    assert build_document_qr_url("https://cabinet.local/api", "track", 9) == "https://cabinet.local/api/documents/track/9"


def test_unknown_route_is_rejected():
    try:
        build_document_qr_url("https://cabinet.local", "pay", 1)
    except ValueError as exc:
        assert "Unsupported document QR route" in str(exc)
    else:
        raise AssertionError("unknown QR route must fail")
