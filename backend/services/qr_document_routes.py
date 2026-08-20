from __future__ import annotations


def build_document_qr_url(base_url: str, route: str, document_id: object) -> str:
    """Build the public document QR URL from the backend origin.

    The verification router is mounted under /api/documents. Accept an origin,
    an /api base, or an already-complete /api/documents base without duplicating
    path segments.
    """
    if route not in {"verify", "track"}:
        raise ValueError(f"Unsupported document QR route: {route}")

    root = (base_url or "http://localhost:8000").rstrip("/")
    if root.endswith("/api/documents"):
        documents_root = root
    elif root.endswith("/api"):
        documents_root = f"{root}/documents"
    else:
        documents_root = f"{root}/api/documents"

    return f"{documents_root}/{route}/{document_id}"
