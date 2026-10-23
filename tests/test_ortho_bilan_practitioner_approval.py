"""G2 synthetic SQLite checks: no real account/patient and no production data."""
from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import patch
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend import models
from backend.models_base import Base
from backend.services import ortho_bilan_practitioner_notes as notes
from backend.services.ortho_bilan_document_v5 import build_ortho_bilan_document
from backend.services.cephalo_document_lock import render_payload_digest
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


class PractitionerNotePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite://",connect_args={"check_same_thread":False},
                                  poolclass=StaticPool)
        tables=[models.User.__table__,models.Patient.__table__,
                models.CephaloAnalysis.__table__,models.OrthoBilanPractitionerNote.__table__]
        Base.metadata.create_all(self.engine,tables=tables)
        self.db=Session(self.engine)
        self.owner=models.User(id=10,email="dentist-a@example.invalid",
                               hashed_password="X",role=models.UserRole.DENTISTE,
                               is_active=True,nom_complet="Synthetic Dentist A")
        self.other=models.User(id=11,email="dentist-b@example.invalid",
                               hashed_password="X",role=models.UserRole.DENTISTE,
                               is_active=True,nom_complet="Synthetic Dentist B")
        self.staff=models.User(id=12,email="staff@example.invalid",
                               hashed_password="X",role=models.UserRole.SECRETAIRE,
                               employer_id=10,is_active=True)
        self.db.add_all([self.owner,self.other,self.staff])
        self.patient=models.Patient(id=17,nom="TEST",prenom="PATIENT",
            date_naissance=datetime(2010,1,1),sexe="F",employer_id=10)
        self.study=models.CephaloAnalysis(id=41,patient_id=17,
            image_original_path="synthetic-only.png",
            angles_data={EVIDENCE_GRAPH_KEY:{"revision":3}, "demo":"v1"})
        self.db.add_all([self.patient,self.study])
        self.db.commit()

        def fake_verified_source(db,patient_id,analysis_id,expected_revision,actor,*,lock=False):
            if actor.get_employer_id()!=self.patient.employer_id:
                raise HTTPException(status_code=403,detail="Tenant refused")
            if patient_id!=17 or analysis_id!=41:
                raise HTTPException(status_code=404,detail="Wrong study")
            if expected_revision!=self.study.angles_data[EVIDENCE_GRAPH_KEY]["revision"]:
                raise HTTPException(status_code=409,detail="Revision changed")
            return self.study,expected_revision,notes.source_digest(self.study)
        self.bound_patch=patch.object(notes,"_get_current",side_effect=fake_verified_source)
        self.bound_patch.start()
        # The source serialization primitive is tested in the existing PDF
        # archive suite. This isolated notes unit stays database-only.
        self.lock_patch=patch("backend.services.cephalo_document_lock.lock_selected_cephalo_for_archive")
        self.lock_patch.start()

    def tearDown(self):
        self.lock_patch.stop()
        self.bound_patch.stop()
        self.db.rollback()
        self.db.close()
        self.engine.dispose()

    def save(self,version=0,summary="Synthèse explicitement saisie par un praticien fictif"):
        return notes.save_practitioner_draft(
            self.db,patient_id=17,analysis_id=41,expected_revision=3,
            expected_draft_version=version,casts={
                "commentaire":"Empreintes fictives", "ddm_maxillaire":-2.5},
            summary=summary,plan="Plan fictif écrit par le praticien",
            actor=self.owner)

    def approve(self,version=1):
        return notes.approve_practitioner_draft(
            self.db,patient_id=17,analysis_id=41,
            expected_revision=3,expected_draft_version=version,actor=self.owner)

    def resolve(self):
        return notes.resolve_approved_practitioner_sections(
            self.db,patient_id=17,analysis_id=41,
            expected_revision=3,study_data=self.study.angles_data,
            employer_id=10)

    def test_draft_requires_explicit_signoff_and_exact_study(self):
        saved=self.save()
        self.assertEqual(saved["draft_version"],1)
        self.assertFalse(saved["approved"])
        self.assertIsNone(self.resolve())
        approved=self.approve()
        self.assertTrue(approved["approved"])
        sections=self.resolve()
        self.assertEqual(sections["practitioner_id"],10)
        self.assertEqual(sections["moulages"]["ddm_maxillaire"],-2.5)
        self.assertEqual(sections["analysis_revision"],3)
        self.assertIsNone(notes.resolve_approved_practitioner_sections(
            self.db,patient_id=17,analysis_id=41,expected_revision=4,
            study_data=self.study.angles_data,employer_id=10))
        self.assertIsNone(notes.resolve_approved_practitioner_sections(
            self.db,patient_id=17,analysis_id=41,expected_revision=3,
            study_data=self.study.angles_data,employer_id=11))

    def test_notes_appear_in_pdf_projection_without_promoting_r14(self):
        self.save()
        self.approve()
        sections=self.resolve()
        source={"patient_id":17,"analysis_id":41,"analysis_revision":3,
                "clinical_validation_available":False,"document_state":"INCOMPLETE",
                "blocking_gates":["r14_not_verified"],"active_runtime_chain_verified":False,
                "measurements":[],"stages":[],"practitioner_approved_sections":sections}
        self.assertFalse(build_ortho_bilan_document(source)["moulages"])
        source["practitioner_sections_authorized"]=True
        result=build_ortho_bilan_document(source)
        self.assertEqual(result["moulages"][0]["value"],"Empreintes fictives")
        self.assertIn("praticien",result["resume_diagnostique"])
        self.assertIn("Plan fictif",result["plan_traitement"])
        self.assertFalse(source["clinical_validation_available"])

    def test_reediting_notes_revokes_previous_approval(self):
        self.save();self.approve()
        self.assertIsNotNone(self.resolve())
        updated=self.save(version=1,summary="Texte modifié")
        self.assertFalse(updated["approved"])
        self.assertEqual(updated["draft_version"],2)
        self.assertIsNone(self.resolve())
        with self.assertRaises(HTTPException) as ctx:
            self.approve(version=1)
        self.assertEqual(ctx.exception.status_code,409)

    def test_source_mutation_or_auth_revocation_fail_closed(self):
        self.save();self.approve()
        self.assertIsNotNone(self.resolve())
        self.study.angles_data={EVIDENCE_GRAPH_KEY:{"revision":3},"demo":"modified"}
        self.db.commit()
        self.assertIsNone(self.resolve())
        self.study.angles_data={EVIDENCE_GRAPH_KEY:{"revision":3},"demo":"v1"}
        self.db.commit()
        self.owner.is_active=False
        self.db.commit()
        self.assertIsNone(self.resolve())

    def test_secretary_and_other_tenant_cannot_approve(self):
        self.save()
        for actor in (self.staff,self.other):
            with self.assertRaises(HTTPException) as ctx:
                notes.approve_practitioner_draft(
                    self.db,patient_id=17,analysis_id=41,
                    expected_revision=3,expected_draft_version=1,actor=actor)
            self.assertEqual(ctx.exception.status_code,403)

    def test_unknown_fields_and_wrong_version_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            notes.save_practitioner_draft(
                self.db,patient_id=17,analysis_id=41,expected_revision=3,
                expected_draft_version=0,casts={"faux":"non"},
                summary="",plan="",actor=self.owner)
        self.assertEqual(ctx.exception.status_code,422)
        self.save()
        with self.assertRaises(HTTPException) as ctx:
            self.save(version=0)
        self.assertEqual(ctx.exception.status_code,409)

    def test_archive_digest_distinguishes_approved_note_snapshots(self):
        d1=render_payload_digest(clinical_data={},ai_diagnostic={})
        d2=render_payload_digest(clinical_data={},ai_diagnostic={},
            practitioner_note_approval={"resume_diagnostique":"Version A"})
        d3=render_payload_digest(clinical_data={},ai_diagnostic={},
            practitioner_note_approval={"resume_diagnostique":"Version B"})
        self.assertEqual(len({d1,d2,d3}),3)


if __name__=="__main__":
    unittest.main()
