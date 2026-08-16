#!/usr/bin/env python3
"""Strict T2 runtime PDF proof against the disposable certification backend."""

from __future__ import annotations

import json
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8005"
OUT_PATH = Path("artifacts/t2-browser/pdf-probe.json")


def fail(message: str) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({"status": "FAIL", "error": message}, indent=2), encoding="utf-8")
    raise SystemExit(message)


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(base_url=BASE_URL, timeout=60.0) as client:
        login = client.post(
            "/api/auth/login",
            data={"username": "t2-browser@cabinet.ma", "password": "T2BrowserPass123!"},
        )
        if login.status_code != 200:
            fail(f"login={login.status_code}: {login.text[:300]}")
        token = login.json().get("access_token")
        if not token:
            fail("login response missing access_token")
        headers = {"Authorization": f"Bearer {token}"}

        patients = client.get("/api/patients/", headers=headers)
        if patients.status_code != 200:
            fail(f"patients={patients.status_code}: {patients.text[:300]}")
        patient = next((p for p in patients.json() if p.get("numero_dossier") == "T2-0001"), None)
        if not patient:
            fail("T2-0001 patient not found")

        payload = {
            "type": "libre",
            "patient_id": patient["id"],
            "data": {
                "title": "Certification PDF T2",
                "content": "Preuve PDF runtime stricte Document Studio.",
                "doc_date": "2026-08-16",
                "page_size": "A5",
                "alignment": "justify",
                "hide_patient_header": False,
            },
            "is_accounted": True,
            "payment_status": "EN_ATTENTE",
        }
        generated = client.post(
            "/api/documents/generate?archive=false&preview=true&force=false",
            headers=headers,
            json=payload,
        )
        if generated.status_code != 200:
            fail(f"generate={generated.status_code}: {generated.text[:500]}")
        body = generated.json()
        if body.get("status") != "success" or not body.get("pdf_url"):
            fail(f"invalid generate response: {body}")

        pdf_url = str(body["pdf_url"]).lstrip("/")
        if pdf_url.startswith("api/"):
            fetch_path = f"/{pdf_url}"
        else:
            fetch_path = f"/api/{pdf_url}"
        pdf = client.get(fetch_path, headers=headers)
        if pdf.status_code != 200:
            fail(f"pdf fetch={pdf.status_code} path={fetch_path}: {pdf.text[:300]}")
        if not pdf.content.startswith(b"%PDF"):
            fail(f"served payload is not PDF: first_bytes={pdf.content[:12]!r}")

        result = {
            "status": "PASS",
            "patientId": patient["id"],
            "generateStatus": generated.status_code,
            "pdfFetchStatus": pdf.status_code,
            "pdfUrl": body["pdf_url"],
            "contentType": pdf.headers.get("content-type"),
            "bytes": len(pdf.content),
            "signature": pdf.content[:4].decode("ascii", errors="replace"),
        }
        OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
