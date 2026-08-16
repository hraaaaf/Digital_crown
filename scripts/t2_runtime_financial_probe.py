#!/usr/bin/env python3
"""Strict persisted reconciliation proof for Document Studio P3/P4/P5.

Runs only against the disposable T2 runtime database configured by the workflow.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from backend import database, models

BASE_URL = "http://127.0.0.1:8005"
OUT_PATH = Path("artifacts/t2-browser/financial-probe.json")


def fail(message: str, details: dict | None = None) -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"status": "FAIL", "error": message}
    if details:
        payload["details"] = details
    OUT_PATH.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    raise SystemExit(message)


def post_ok(client: httpx.Client, path: str, headers: dict, payload: dict) -> dict:
    response = client.post(path, headers=headers, json=payload)
    if response.status_code != 200:
        fail(f"POST {path}={response.status_code}", {"body": response.text[:800]})
    return response.json()


def counts(patient_id: int) -> dict[str, int]:
    with database.SessionLocal() as db:
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            fail("patient disappeared from runtime database")
        return {
            "documents": len(patient.documents),
            "actes": db.query(models.Acte).filter(models.Acte.patient_id == patient_id).count(),
            "payments": db.query(models.Payment).filter(models.Payment.patient_id == patient_id).count(),
            "plans": db.query(models.InstallmentPlan).filter(models.InstallmentPlan.patient_id == patient_id).count(),
        }


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(base_url=BASE_URL, timeout=90.0) as client:
        login = client.post(
            "/api/auth/login",
            data={"username": "t2-browser@cabinet.ma", "password": "T2BrowserPass123!"},
        )
        if login.status_code != 200:
            fail(f"login={login.status_code}", {"body": login.text[:500]})
        token = login.json().get("access_token")
        if not token:
            fail("missing access_token")
        headers = {"Authorization": f"Bearer {token}"}

        patients = client.get("/api/patients", headers=headers)
        if patients.status_code != 200:
            fail(f"patients={patients.status_code}", {"body": patients.text[:500]})
        patient = next((p for p in patients.json() if p.get("numero_dossier") == "T2-0001"), None)
        if not patient:
            fail("T2-0001 patient not found")
        patient_id = int(patient["id"])

        baseline = counts(patient_id)

        # P3 — Devis archives a financial document but must not invent performed acts/payments.
        devis = {
            "type": "devis",
            "patient_id": patient_id,
            "data": {
                "items": [{
                    "acte": "T2 Devis Probe",
                    "dent": "11",
                    "dents": [11],
                    "prix_unitaire": 650.0,
                    "montant": 650.0,
                    "date": "2026-08-16",
                }],
                "doc_date": "2026-08-16",
                "teeth_data": {"11": ["probe"]},
            },
            "is_accounted": True,
            "payment_status": "EN_ATTENTE",
        }
        post_ok(client, "/api/documents/generate?archive=true&preview=false&force=true", headers, devis)
        after_devis = counts(patient_id)
        if after_devis["documents"] != baseline["documents"] + 1:
            fail("P3 devis archive count mismatch", {"before": baseline, "after": after_devis})
        if after_devis["actes"] != baseline["actes"] or after_devis["payments"] != baseline["payments"]:
            fail("P3 devis invented transactional rows", {"before": baseline, "after": after_devis})

        # P4a — Pending note persists the act, not cash collection.
        pending_note = {
            "type": "note",
            "patient_id": patient_id,
            "data": {
                "payments": [{
                    "acte": "T2 Honoraires Pending Probe",
                    "dent": "21",
                    "dents": [21],
                    "prix_unitaire": 777.0,
                    "montant": 777.0,
                    "date": "2026-08-16",
                }],
                "doc_date": "2026-08-16",
                "teeth_data": {"21": ["probe"]},
                "installments": [],
                "is_global_note": False,
            },
            "is_accounted": True,
            "payment_status": "EN_ATTENTE",
        }
        post_ok(client, "/api/documents/generate?archive=true&preview=false&force=true", headers, pending_note)
        after_pending = counts(patient_id)
        if after_pending["documents"] != after_devis["documents"] + 1:
            fail("P4 pending note archive count mismatch", {"before": after_devis, "after": after_pending})
        if after_pending["actes"] != after_devis["actes"] + 1:
            fail("P4 pending note did not persist exactly one act", {"before": after_devis, "after": after_pending})
        if after_pending["payments"] != after_devis["payments"]:
            fail("P4 pending note incorrectly collected cash", {"before": after_devis, "after": after_pending})

        # P4b — Paid note persists exactly one act and one exact linked cash payment.
        paid_note = {
            "type": "note",
            "patient_id": patient_id,
            "data": {
                "payments": [{
                    "acte": "T2 Honoraires Paid Probe",
                    "dent": "22",
                    "dents": [22],
                    "prix_unitaire": 888.0,
                    "montant": 888.0,
                    "date": "2026-08-16",
                    "mode_reglement": "Espèces",
                }],
                "doc_date": "2026-08-16",
                "teeth_data": {"22": ["probe"]},
                "installments": [],
                "is_global_note": False,
            },
            "is_accounted": True,
            "payment_status": "PAYE",
        }
        post_ok(client, "/api/documents/generate?archive=true&preview=false&force=true", headers, paid_note)
        after_paid = counts(patient_id)
        if after_paid["documents"] != after_pending["documents"] + 1:
            fail("P4 paid note archive count mismatch", {"before": after_pending, "after": after_paid})
        if after_paid["actes"] != after_pending["actes"] + 1 or after_paid["payments"] != after_pending["payments"] + 1:
            fail("P4 paid note transactional count mismatch", {"before": after_pending, "after": after_paid})
        with database.SessionLocal() as db:
            last_payment = (
                db.query(models.Payment)
                .filter(models.Payment.patient_id == patient_id)
                .order_by(models.Payment.id.desc())
                .first()
            )
            if not last_payment or abs(float(last_payment.amount) - 888.0) >= 0.005 or not last_payment.acte_id:
                fail("P4 paid note payment is not exact/linked", {
                    "paymentId": getattr(last_payment, "id", None),
                    "amount": getattr(last_payment, "amount", None),
                    "acteId": getattr(last_payment, "acte_id", None),
                })

        # P5 — Persist a balanced plan, reload it, then collect one exact installment.
        plan_payload = {
            "patient_id": patient_id,
            "title": "T2 P5 Probe",
            "total_amount": 1200.0,
            "installments": [
                {"label": "T2 Acompte", "amount": 500.0, "due_date": "2026-09-01T00:00:00", "status": "EN_ATTENTE"},
                {"label": "T2 Solde", "amount": 700.0, "due_date": "2026-10-01T00:00:00", "status": "EN_ATTENTE"},
            ],
        }
        plan = post_ok(client, "/api/installments/", headers, plan_payload)
        if abs(float(plan.get("total_amount", 0)) - 1200.0) >= 0.005 or len(plan.get("installments", [])) != 2:
            fail("P5 created plan is not exactly reconciled", {"plan": plan})
        persisted_sum = sum(float(row.get("amount", 0)) for row in plan["installments"])
        if abs(persisted_sum - 1200.0) >= 0.005:
            fail("P5 persisted installment sum mismatch", {"sum": persisted_sum, "plan": plan})

        latest = client.get(f"/api/installments/patient/{patient_id}/latest", headers=headers)
        if latest.status_code != 200:
            fail(f"P5 reload={latest.status_code}", {"body": latest.text[:500]})
        latest_body = latest.json()
        if latest_body.get("id") != plan.get("id") or abs(float(latest_body.get("total_amount", 0)) - 1200.0) >= 0.005:
            fail("P5 reload differs from persisted plan", {"created": plan, "latest": latest_body})

        first = latest_body["installments"][0]
        before_collection = counts(patient_id)
        collected = client.put(
            f"/api/installments/{first['id']}",
            headers=headers,
            json={"status": "PAYE", "payment_method": "ESPECES"},
        )
        if collected.status_code != 200 or collected.json().get("status") != "PAYE":
            fail(f"P5 collection={collected.status_code}", {"body": collected.text[:500]})
        after_collection = counts(patient_id)
        if after_collection["payments"] != before_collection["payments"] + 1:
            fail("P5 collection did not create exactly one payment", {"before": before_collection, "after": after_collection})
        with database.SessionLocal() as db:
            last_payment = (
                db.query(models.Payment)
                .filter(models.Payment.patient_id == patient_id)
                .order_by(models.Payment.id.desc())
                .first()
            )
            if (
                not last_payment
                or abs(float(last_payment.amount) - 500.0) >= 0.005
                or last_payment.installment_id != first["id"]
            ):
                fail("P5 collection payment is not exact/linked", {
                    "paymentId": getattr(last_payment, "id", None),
                    "amount": getattr(last_payment, "amount", None),
                    "installmentId": getattr(last_payment, "installment_id", None),
                    "expectedInstallmentId": first["id"],
                })

        result = {
            "status": "PASS",
            "patientId": patient_id,
            "P3_devis": {"baseline": baseline, "after": after_devis},
            "P4_pending": {"after": after_pending},
            "P4_paid": {"after": after_paid, "exactPayment": 888.0},
            "P5_installments": {"planId": plan["id"], "total": 1200.0, "rows": [500.0, 700.0], "collected": 500.0},
        }
        OUT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
