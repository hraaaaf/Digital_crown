from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

policy = ROOT / 'backend/services/certificate_suggestion_policy.py'
policy.write_text('''from __future__ import annotations\n\nfrom datetime import datetime, timedelta\nfrom typing import Optional\n\nSURGICAL_KEYWORDS = ("extraction", "chirurgie", "implant", "lambeau", "resection", "résection")\nORTHO_KEYWORDS = ("ortho", "bagues", "appareil", "ajustement")\nAPTITUDE_KEYWORDS = ("aptitude", "sport")\n\n\ndef certificate_same_day_bounds(now: datetime) -> tuple[datetime, datetime]:\n    start = now.replace(hour=0, minute=0, second=0, microsecond=0)\n    return start, start + timedelta(days=1)\n\n\ndef build_certificate_context_signal(motif_text: str, *, has_same_day_visit: bool) -> Optional[dict]:\n    motif = (motif_text or "").strip().lower()\n    if not has_same_day_visit or not motif:\n        return None\n\n    if any(keyword in motif for keyword in APTITUDE_KEYWORDS):\n        # A motif alone is insufficient evidence to suggest a fitness certificate.\n        return None\n\n    if any(keyword in motif for keyword in SURGICAL_KEYWORDS):\n        return {\n            "type": "Arrêt de travail",\n            "confidence": "context",\n            "reason": "Acte chirurgical réalisé aujourd’hui. Évaluer si un repos est nécessaire ; type et durée restent à déterminer par le praticien.",\n        }\n\n    if any(keyword in motif for keyword in ORTHO_KEYWORDS):\n        return {\n            "type": "Certificat de Présence",\n            "confidence": "context",\n            "reason": "Passage orthodontique détecté aujourd’hui. Une attestation de présence peut être envisagée si elle est demandée par le patient.",\n        }\n\n    return {\n        "type": "Certificat de Présence",\n        "confidence": "context",\n        "reason": "Passage au cabinet détecté aujourd’hui. Une attestation de présence peut être envisagée si elle est demandée par le patient.",\n    }\n''', encoding='utf-8')

test = ROOT / 'backend/tests/test_certificate_suggestion_policy_p3.py'
test.write_text('''from datetime import datetime\n\nfrom backend.services.certificate_suggestion_policy import (\n    build_certificate_context_signal,\n    certificate_same_day_bounds,\n)\n\n\ndef test_same_day_bounds_exclude_tomorrow():\n    start, end = certificate_same_day_bounds(datetime(2026, 8, 15, 19, 30))\n    assert start == datetime(2026, 8, 15, 0, 0)\n    assert end == datetime(2026, 8, 16, 0, 0)\n\n\ndef test_no_same_day_evidence_means_no_suggestion():\n    assert build_certificate_context_signal('', has_same_day_visit=False) is None\n    assert build_certificate_context_signal('extraction', has_same_day_visit=False) is None\n\n\ndef test_surgery_signal_is_canonical_and_has_no_duration():\n    signal = build_certificate_context_signal('Extraction 36', has_same_day_visit=True)\n    assert signal is not None\n    assert signal['type'] == 'Arrêt de travail'\n    assert 'days' not in signal\n    assert 'durée' in signal['reason'].lower()\n    assert 'praticien' in signal['reason'].lower()\n\n\ndef test_orthodontic_visit_only_signals_presence():\n    signal = build_certificate_context_signal('Ajustement appareil ortho', has_same_day_visit=True)\n    assert signal is not None\n    assert signal['type'] == 'Certificat de Présence'\n    assert 'days' not in signal\n\n\ndef test_fitness_or_sport_word_does_not_create_medical_fitness_certificate():\n    assert build_certificate_context_signal('Certificat aptitude sport', has_same_day_visit=True) is None\n''', encoding='utf-8')

router = ROOT / 'backend/routers/prescriptions.py'
text = router.read_text(encoding='utf-8')
old = 'from backend.services.audit_service import audit_service\n'
new = 'from backend.services.audit_service import audit_service\nfrom backend.services.certificate_suggestion_policy import build_certificate_context_signal, certificate_same_day_bounds\n'
assert old in text, 'router import anchor missing'
text = text.replace(old, new, 1)
start = text.index('@prescription_router.get("/certif-suggest/{patient_id}")')
end_marker = '    return suggestion'
end = text.index(end_marker, start) + len(end_marker)
old_block = text[start:end]
new_block = '''@prescription_router.get("/certif-suggest/{patient_id}")\nasync def suggest_certificate(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("prescriptions"))):\n    """Retourne un signal documentaire contextuel, jamais une prescription automatique de type ou de durée."""\n    assert_patient_access(patient_id, current_user, db)\n\n    today, tomorrow = certificate_same_day_bounds(datetime.now())\n\n    last_act = db.query(models.Acte).filter(\n        models.Acte.patient_id == patient_id,\n        models.Acte.date_debut >= today,\n        models.Acte.date_debut < tomorrow,\n    ).order_by(models.Acte.date_debut.desc()).first()\n\n    last_rdv = db.query(models.Appointment).filter(\n        models.Appointment.patient_id == patient_id,\n        models.Appointment.datetime_start >= today,\n        models.Appointment.datetime_start < tomorrow,\n    ).order_by(models.Appointment.datetime_start.desc()).first()\n\n    if last_act:\n        motif_text = last_act.libelle or ""\n        has_same_day_visit = True\n    elif last_rdv:\n        motif_text = last_rdv.motif or ""\n        has_same_day_visit = True\n    else:\n        motif_text = ""\n        has_same_day_visit = False\n\n    return build_certificate_context_signal(motif_text, has_same_day_visit=has_same_day_visit)'''
text = text[:start] + new_block + text[end:]
router.write_text(text, encoding='utf-8')

form = ROOT / 'frontend/src/features/admin/DocumentStudio/Forms/CertificateForm.tsx'
text = form.read_text(encoding='utf-8')
old = '''                  <span>\n                    Signal documentaire : {suggestion.reason || 'contexte détecté'}. Suggestion non appliquée ; type et durée restent à valider par le praticien.\n                  </span>'''
new = '''                  <span>\n                    Signal documentaire : {suggestion.reason || 'contexte détecté'} Le logiciel ne choisit ni le type ni la durée à la place du praticien.\n                  </span>'''
assert old in text, 'certificate suggestion banner anchor missing'
form.write_text(text.replace(old, new, 1), encoding='utf-8')

form_test = ROOT / 'frontend/src/features/admin/DocumentStudio/Forms/CertificateForm.p3a.test.tsx'
text = form_test.read_text(encoding='utf-8')
old = "expect(screen.getByText(/Suggestion non appliquée/i)).toBeTruthy();\n    expect(screen.getByText(/valider.*praticien/i)).toBeTruthy();"
new = "expect(screen.getByText(/ne choisit ni le type ni la durée/i)).toBeTruthy();\n    expect(screen.getByText(/praticien/i)).toBeTruthy();"
assert old in text, 'form suggestion test anchor missing'
form_test.write_text(text.replace(old, new, 1), encoding='utf-8')

for rel in ['scripts/p3_certificat_suggestion_once.py', '.github/workflows/p3-certificat-suggestion-once.yml']:
    target = ROOT / rel
    if target.exists():
        target.unlink()
