from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_p0_clinicalhub_has_no_fabricated_clinical_truth():
    hub = _read("frontend/src/features/patients/components/ClinicalHub.tsx")
    for banned in (
        "Détartrage & Surfaçage",
        "scientificOrder",
        "pending_devis_plan",
        "Diagnostic intelligent, plan de traitement global et suivi automatisé.",
    ):
        assert banned not in hub
    assert "Aucune étape de traitement enregistrée." in hub
    assert "Proposition à valider" in hub
    assert "Une proposition d’assistant ne devient jamais une conclusion sans cette action explicite." in hub
    assert "patientClinicalPersistence.createConclusion" in hub


def test_p0_all_clinical_assistants_are_proposal_only():
    root = ROOT / "frontend/src/features/patients/components/wizards"

    standard_assistants = (
        "AssistantATM.tsx",
        "AssistantGeneral.tsx",
        "AssistantOrtho.tsx",
        "AssistantParo.tsx",
        "AssistantProthese.tsx",
        "AssistantEndo.tsx",
        "AssistantChirurgie.tsx",
        "AssistantPedo.tsx",
        "AssistantPatho.tsx",
    )
    for filename in standard_assistants:
        source = (root / filename).read_text(encoding="utf-8")
        assert "onComplete(summary, [])" in source, filename
        assert "/prescriptions" not in source, filename
        assert "/accounting" not in source, filename
        assert "/master-plan" not in source, filename

    complete = (root / "AssistantExamenComplet.tsx").read_text(encoding="utf-8")
    assert "steps: [], next: null" in complete
    assert "ne pose pas automatiquement de diagnostic" in complete
    assert "décision du praticien" in complete


def test_p0_finance_uses_strict_binding_explicit_method_and_canonical_installments():
    accounting = _read("backend/routers/accounting.py")
    start = accounting.index('@router.post("/payments", response_model=schemas.PaymentOut)')
    end = accounting.index('@router.get("/payments/patient/{patient_id}"', start)
    payment_block = accounting[start:end]

    assert "acte.patient_id != payment.patient_id" in payment_block
    assert "plan.patient_id != payment.patient_id" in payment_block
    assert "payment.acte_id is not None and payment.installment_id is not None" in payment_block
    assert "getattr(models.PaymentMethod, payment.payment_method, None)" in payment_block
    assert "models.PaymentMethod.ESPECES" not in payment_block
    assert 'Body(default="ESPECES"' not in accounting

    for banned_route in (
        '@router.post("/plans"',
        '@router.get("/plans/patient/{patient_id}"',
        '@router.put("/installments/{installment_id}"',
        '@router.delete("/plans/{plan_id}"',
    ):
        assert banned_route not in accounting

    finances = _read("frontend/src/features/patients/components/PatientFinances.tsx")
    modal = _read("frontend/src/features/patients/components/InstallmentPlanModal.tsx")
    quick_pay = _read("frontend/src/features/patients/components/QuickPayModal.tsx")

    for required in (
        "Facturé",
        "Encaissé",
        "Reste dû",
        "Prochaine échéance",
        "has_billing_data",
        "Indéterminé",
    ):
        assert required in finances
    assert "Taux Recouvrement" not in finances
    assert "recoveryRate" not in finances
    assert "api.post('/installments/'" in modal
    assert "acte_id: acte.id" in modal
    assert "coverageExact" in modal
    assert "useState<PaymentMethod | null>(null" in quick_pay


def test_p0_clinical_header_has_no_commercial_patient_score():
    details = _read("frontend/src/features/patients/PatientDetailsInner.tsx")
    assert "PatientScoreBadge" not in details


def test_p0_nba_and_panoramic_surfaces_are_fail_closed():
    habits = _read("backend/services/habits_engine.py")
    for banned in (
        "Risque parodontal élevé",
        "Planifier Détartrage",
        "Suggérer Détartrage",
        "Patient Premium — Impayé Critique",
        "Patient PLATINUM",
        "ORTHO_PROGRESSION",
        "ORTHO_COMPLETION_ESTIMATE",
    ):
        assert banned not in habits

    elite = _read("backend/services/elite_manager.py")
    rag = _read("backend/services/rag_context.py")
    for banned in (
        "anomalies détectées sur la panoramique",
        "panoramic_findings",
        "Lésion carieuse détectée",
        "pano_predict_",
        "treatment_plan_engine.generate_plan(",
    ):
        assert banned not in elite

    assert "panoramic_findings" not in rag
    assert "panoramic_landmarks" in elite
    assert "panoramic_landmarks" in rag
    assert "Repérage Panoramique" in elite
    assert "Aucune anomalie n'est conclue automatiquement." in elite
    assert "Génération automatique du plan de traitement désactivée" in elite


def test_r1_panoramic_pdf_is_patient_authorized_and_blob_streamed():
    ia = _read("backend/routers/ia.py")
    start = ia.index('@router.get("/panoramic/{analysis_id}/pdf")')
    end = ia.index('@router.delete("/panoramic/{analysis_id}"', start)
    endpoint = ia[start:end]

    assert endpoint.index("assert_patient_access") < endpoint.index("panoramic_elite_generator.generate")
    assert "FileResponse(" in endpoint
    assert "pdf_url" not in endpoint

    studio = _read("frontend/src/features/panoramic/PanoramicStudio.tsx")
    assert "responseType: 'blob'" in studio
    assert "response.data.pdf_url" not in studio
