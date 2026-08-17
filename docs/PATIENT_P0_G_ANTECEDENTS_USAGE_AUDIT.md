# Patient P0-G — Audit exhaustif des usages `antecedents_medicaux`

Source de preuve : `git grep -n -I antecedents_medicaux` exécuté sur la branche Patient P0. Ce rapport ne déduit aucune migration ; il inventorie uniquement les références réellement présentes dans le repository.

Nombre de références textuelles trouvées : **62**.

## Références

```text
.github/workflows/patient-p0-g-antecedents-audit.yml:29:              ["git", "grep", "-n", "-I", "antecedents_medicaux", "--", ".", ":!docs/PATIENT_P0_G_ANTECEDENTS_USAGE_AUDIT.md"],
.github/workflows/patient-p0-g-antecedents-audit.yml:38:              "# Patient P0-G — Audit exhaustif des usages `antecedents_medicaux`",
.github/workflows/patient-p0-g-antecedents-audit.yml:40:              "Source de preuve : `git grep -n -I antecedents_medicaux` exécuté sur la branche Patient P0. Ce rapport ne déduit aucune migration ; il inventorie uniquement les références réellement présentes dans le repository.",
.github/workflows/patient-p0-g-antecedents-audit.yml:52:              "La suppression ou migration de `DossierClinique.antecedents_medicaux` reste interdite tant que les références ci-dessus n'ont pas été classées en lecture, écriture, schéma, test ou documentation et qu'une stratégie de migration de données n'est pas prouvée.",
DOCUMENT_STUDIO_ROADMAP.md:198:- **P7-C — contexte clinique structuré** : le schéma patient inspecté ne démontre qu’un `antecedents_medicaux` texte libre, sans source allergies structurée ; nécessite évolution du modèle patient et gouvernance clinique ;
alembic/versions/0ac66fa0bdb8_remove_color_ref_and_init_lab_jobs.py:319:    sa.Column('antecedents_medicaux', sa.String(), nullable=True),
alembic/versions/0ac66fa0bdb8_remove_color_ref_and_init_lab_jobs.py:420:    sa.Column('antecedents_medicaux', sa.Text(), nullable=True),
backend/models.py:235:    antecedents_medicaux: Mapped[str | None] = mapped_column(String, nullable=True)
backend/models.py:301:    antecedents_medicaux: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
backend/schemas/patient.py:62:    antecedents_medicaux: Optional[str] = None
backend/schemas/patient.py:116:    antecedents_medicaux: Optional[str] = None
backend/services/bot/action_dispatcher.py:355:            "antecedents": patient.antecedents_medicaux or "Aucun",
backend/services/bot/action_dispatcher.py:368:        if patient.antecedents_medicaux:
backend/services/bot/action_dispatcher.py:369:            message += f"\n⚠️ Antécédents : {patient.antecedents_medicaux}"
backend/services/clinical_coherence.py:71:            if patient and self._is_stomach_risk(patient.antecedents_medicaux):
backend/services/clinical_intelligence.py:123:        if patient.antecedents_medicaux:
backend/services/clinical_intelligence.py:124:            clinical_parts.append(f"Antécédents : {patient.antecedents_medicaux}")
backend/services/clinical_intelligence.py:148:        if patient.antecedents_medicaux and any(x in patient.antecedents_medicaux.lower() for x in ["diabète", "avk", "cardiaque", "hypertension"]):
backend/services/clinical_intelligence.py:149:            alerts.append(f"Alerte Médicale : {patient.antecedents_medicaux}")
backend/services/clinical_intelligence.py:250:                          f"**Antécédents** : {patient.antecedents_medicaux or 'Néant'}." +
backend/services/elite_manager.py:254:            if patient.antecedents_medicaux: score += 10
backend/services/fts_indexer.py:30:        if patient.antecedents_medicaux:
backend/services/fts_indexer.py:31:            entries.append((patient_id, patient.antecedents_medicaux, "antecedent", ""))
backend/services/habits_engine.py:237:        if patient.antecedents_medicaux:
backend/services/habits_engine.py:238:            cleaned_ant = patient.antecedents_medicaux.strip()
backend/services/prescription_context_guard.py:74:    antecedents = getattr(patient, "antecedents_medicaux", None)
backend/services/prescription_service_legacy.py:29:            "antecedents": patient.antecedents_medicaux or ""
backend/services/prescription_service_legacy.py:425:        if patient and patient.antecedents_medicaux:
backend/services/prescription_service_legacy.py:426:            antecedents = patient.antecedents_medicaux.lower()
backend/tests/test_clinical_intelligence_service.py:16:        antecedents_medicaux=antecedents,
backend/tests/test_habits_engine.py:248:            antecedents_medicaux=None,
backend/tests/test_habits_engine.py:268:            antecedents_medicaux="RAS",
backend/tests/test_patient_medical_history_contract.py:3:The Patient API is the authoritative public contract for antecedents_medicaux.
backend/tests/test_patient_medical_history_contract.py:13:    assert "antecedents_medicaux" in PatientCreate.model_fields
backend/tests/test_patient_medical_history_contract.py:14:    assert "antecedents_medicaux" in PatientOut.model_fields
backend/tests/test_patient_medical_history_contract.py:18:    assert "antecedents_medicaux" not in DossierOut.model_fields
backend/tests/test_prescription_missing_data_guard.py:15:    antecedents_medicaux = "RAS renseigné"
backend/tests/test_prescription_missing_data_guard.py:51:    patient.antecedents_medicaux = None
docs/PAGE_PATIENT_AUDIT_ROADMAP.md:87:- [ ] Résoudre le doublon `Patient.antecedents_medicaux` / `DossierClinique.antecedents_medicaux`.
docs/audits/DOCUMENT_STUDIO_P7_COMPAGNON_DIAGNOSTIQUE_AUDIT.md:175:`antecedents_medicaux` est abaissé en minuscules puis testé par `includes(...)`.
docs/audits/DOCUMENT_STUDIO_P7_INTEGRATION_STATUS.md:44:Vérification du schéma patient : il existe `antecedents_medicaux: Optional[str]`, mais aucun champ allergies structuré n’a été démontré dans la baseline inspectée.
e2e/tests/helpers.ts:34:  antecedents_medicaux: '',
frontend/src/features/admin/DocumentStudio/DocumentHubClinicalBoundary.test.ts:12:    expect(documentHubSource).not.toContain('antecedents_medicaux');
frontend/src/features/admin/DocumentStudio/HouseWizard.tsx:69:         .then(res => setMedicalHistory(res.data.antecedents_medicaux || ''))
frontend/src/features/admin/DocumentStudio/P7DirtyState.p7f.test.tsx:20:    mocks.get.mockResolvedValue({ data: { antecedents_medicaux: '' } });
frontend/src/features/admin/DocumentStudio/TreatmentPlanStudio.p7a.test.tsx:21:    mocks.get.mockResolvedValue({ data: { antecedents_medicaux: '' } });
frontend/src/features/admin/DocumentStudio/TreatmentPlanStudio.p7d.test.tsx:17:    mocks.get.mockResolvedValue({ data: { antecedents_medicaux: '' } });
frontend/src/features/admin/DocumentStudio/TreatmentPlanStudio.p7g.test.tsx:17:    mocks.get.mockResolvedValue({ data: { antecedents_medicaux: '' } });
frontend/src/features/admin/DocumentStudio/TreatmentPlanStudio.tsx:67:          setMedicalHistory(response.data.antecedents_medicaux || '');
frontend/src/features/patients/AddPatientForm.tsx:54:    antecedents_medicaux: '',
frontend/src/features/patients/AddPatientForm.tsx:167:        antecedents_medicaux: formData.antecedents_medicaux || null
frontend/src/features/patients/AddPatientForm.tsx:214:      antecedents_medicaux: formData.antecedents_medicaux === '' ? null : formData.antecedents_medicaux,
frontend/src/features/patients/AddPatientForm.tsx:585:                name="antecedents_medicaux" 
frontend/src/features/patients/AddPatientForm.tsx:586:                value={formData.antecedents_medicaux} 
frontend/src/features/patients/EditPatientForm.tsx:46:    antecedents_medicaux: '',
frontend/src/features/patients/EditPatientForm.tsx:85:          antecedents_medicaux: patient.antecedents_medicaux || '',
frontend/src/features/patients/EditPatientForm.tsx:436:              value={formData.antecedents_medicaux} 
frontend/src/features/patients/EditPatientForm.tsx:437:              onChange={(e) => setFormData({...formData, antecedents_medicaux: e.target.value})} 
frontend/src/features/patients/PatientDetailsInner.tsx:56:  antecedents_medicaux?: string;
frontend/src/features/patients/PatientDetailsInner.tsx:295:        {!isCompact && (patient.antecedents_medicaux || patient.motif_consultation) && (
frontend/src/features/patients/PatientDetailsInner.tsx:297:            {patient.antecedents_medicaux && (
frontend/src/features/patients/PatientDetailsInner.tsx:302:                  <p className="text-sm font-medium whitespace-pre-wrap">{patient.antecedents_medicaux}</p>
```

## Gate P0-G

La suppression ou migration de `DossierClinique.antecedents_medicaux` reste interdite tant que les références ci-dessus n'ont pas été classées en lecture, écriture, schéma, test ou documentation et qu'une stratégie de migration de données n'est pas prouvée.
