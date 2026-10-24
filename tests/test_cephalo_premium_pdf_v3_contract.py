"""Premium V3 — real synthetic PDF parity without a patient or clinical promotion."""
from __future__ import annotations
import os
import copy
from datetime import date
from unittest.mock import MagicMock
import shutil
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from PyPDF2 import PdfReader
import fitz
from PIL import Image, ImageDraw

from backend.services.cephalo_pdf_presentation import clinical_term, measurement_value
from backend.services.document_branding_contract import serialize_document_branding
from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator
from backend.services.generators.ordonnance_gen import OrdonnanceGenerator
from backend.services.base_template import BaseTemplate
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

TEMPLATES = ("swiss", "royal", "clinical", "modern", "heritage")

def synthetic_branding(template="swiss"):
    return {
        "selected_template": template,
        "selected_theme": "rose",  # deliberate counterexample: never drives PDF identity
        "nom_praticien": "Dr Salma Atlas - DEMO",
        "nom_cabinet": "Cabinet Atlas - DEMONSTRATION",
        "header_customized": True,
        "specialty_ids": ["ortho"],
        "header_lines_fr": ["Dr Salma Atlas - DEMO", "Chirurgienne-dentiste - Orthodontie", "Orthodontie et orthopedie dento-faciale"],
        "header_lines_ar": [],
        "footer_address": "24 avenue de l'Exemple, Rabat (adresse fictive)",
        "footer_phones": "06 00 00 00 00",
        "contacts_json": {"fixe": {"enabled": True, "value": "05 00 00 00 00"}, "mobile": {"enabled": True, "value": "06 00 00 00 00"}},
        "primary_color": "#29476a", "secondary_color": "#506379",
        "accent_color": "#a9b2c2", "font_fr": "outfit",
        "margin_top": 3.6, "margin_bottom": 3.2,
        "qr_code_enabled": True, "qr_code_type": "WEBSITE",
        "qr_code_value": "https://example.org/digital-crown-demo",
        "qr_code_label": "SITE DEMO", "qr_code_style": "classic",
        "qr_code_color": "#29476a", "logo_path": "logo_atlas_demo.png",
        "use_letterhead": False,
        "hide_header": False, "hide_footer": False,
    }

def synthetic_projection(n=95):
    measurement = []
    known = (
        "M_SNA_DEG_V1", "M_SNB_DEG_V1", "M_ANB_DEG_V1",
        "M_SN_GOGN_DEG_V1", "M_FH_GOME_DEG_V1",
        "M_A_NPERP_MM_V1", "M_CO_A_MM_V1",
        "M_U1_NA_DEG_V1", "M_U1_NA_MM_V1", "M_L1_NB_DEG_V1",
        "M_L1_NB_MM_V1", "M_IMPA_GOME_DEG_V1",
        "M_FMIA_L1_FH_DEG_V1", "M_INTERINCISAL_DEG_V1",
        "M_RICKETTS_OVERJET_FOP_MM_V1", "M_RICKETTS_OVERBITE_FOP_MM_V1",
    )
    # Human-plausible but entirely synthetic measurements; a repeated 82
    # across unrelated angles and mm lengths is not an acceptable visual test.
    demo_values = (82.0, 80.0, 2.0, 32.0, 25.0, 0.8, 84.0, 22.0,
                   4.0, 25.0, 4.0, 92.0, 64.0, 132.0, 2.0, 2.5)
    canonical = []
    for i in range(n):
        available = i < len(known) and (i % 3 == 0 or i == 11)
        name = known[i] if i < len(known) else f"ANALYSIS_MEASURE_{i:03d}"
        original_ref = f"evidence:demo:{i}"
        method = f"DEMO_TYPED_METHOD_{i:03d}"
        unit = "°" if i < len(known) and "_DEG_" in known[i] else "mm"
        status = "AVAILABLE" if available else "NOT_COMPUTABLE"
        value = demo_values[i] if available else None
        measurement.append({
            "measurement_id": original_ref,
            "availability_status": status,
            "value": value,
            "unit": unit, "method_id": method,
            "method_version": "1", "scientific_source": "EVIDENCE_GRAPH_V1",
            "calibration_ref": "non requise",
        })
        if i < len(known):
            canonical.append({
                "canonical_measurement_id": name,
                "value_authority_method_id": method,
                "measurement_refs": [original_ref],
                "availability_status": status, "value": value, "unit": unit,
            })
    return {
        "analysis_id": 41, "analysis_revision": 3,
        "contract_version": "CEPHALO_PDF_PROJECTION_V1",
        "document_state": "INCOMPLETE",
        "authority": "BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO",
        "active_runtime_chain_verified": True,
        "clinical_validation_reason": "R14 NO VERIFIED PRACTITIONER SNAPSHOT",
        "blocking_gates": ["diagnostic_rule_registry_empty",
                           "r14_authoritative_snapshot_not_persisted"],
        "measurements": measurement,
        "canonical_measurements": canonical,
        "stages": [
            {"stage_id": "R11", "title": "Diagnostic scientifique",
             "presentation_state": "BLOCKED",
             "blocking_gates": ["diagnostic_rule_registry_empty"],
             "missing_data_refs": ["r11_provenance_missing"]},
        ],
    }

def synthetic_approved_projection(n=95):
    """Purpose-built TEST-only clinician-approved narrative, never a live R15 snapshot."""
    projection = synthetic_projection(n)
    projection.update({
        "patient_id": 17,
        "document_state": "INCOMPLETE",
        "clinical_validation_available": False,
        "blocking_gates": ["r14_authoritative_snapshot_not_persisted"],
        "practitioner_sections_authorized": True,  # synthetic test fixture; live authority only injected by document_factory
        "practitioner_approved_sections": {
            "contract_version": "ORTHO_PRACTITIONER_APPROVED_V1",
            "validation_state": "APPROVED",
            "patient_id": 17, "analysis_id": 41, "analysis_revision": 3,
            "practitioner_id": 9,
            "validated_at": "2026-10-23T16:00:00+01:00",
            "moulages": {
                "classe_molaire_droite": "Classe I (démonstration)",
                "classe_molaire_gauche": "Classe I (démonstration)",
                "classe_canine_droite": "Classe I (démonstration)",
                "classe_canine_gauche": "Classe I (démonstration)",
                "forme_arcade": "Ovale (démonstration)",
                "ddm_maxillaire": -2.0,
                "ddm_mandibulaire": -1.0,
                "commentaire": "Examen effectué sur moulages fictifs.",
            },
            "resume_diagnostique": (
                "Compte rendu synthétique saisi et approuvé par un dentiste de test : "
                "observations dentaires fictives à fins exclusives de mise en page."
            ),
            "plan_traitement": (
                "Plan fictif rédigé par un dentiste de test : "
                "aucune indication thérapeutique pour un patient réel."
            ),
        },
    })
    return projection

def synthetic_vm(template="swiss"):
    return SimpleNamespace(
        patient_nom="TEST", patient_prenom="Synthétique", patient_age="12",
        date_generation="23/10/2026", doctor_name="Dr Salma Atlas - DEMO",
        cabinet_config=synthetic_branding(template),
        is_pre_bilan=True, validation_warnings=[],
    )

class PdfV3Contract(unittest.TestCase):
    def test_allowlist_separates_theme_and_sensitive_fields(self):
        cabinet = SimpleNamespace(**dict(synthetic_branding(), hashed_password="NEVER_PRINT"))
        branded = serialize_document_branding(cabinet)
        self.assertEqual(branded["selected_template"], "swiss")
        self.assertNotIn("selected_theme", branded)
        self.assertNotIn("hashed_password", branded)
        self.assertEqual(branded["footer_address"], "24 avenue de l'Exemple, Rabat (adresse fictive)")
        self.assertEqual(branded["qr_code_type"], "WEBSITE")
        self.assertEqual(branded["qr_code_value"], "https://example.org/digital-crown-demo")
        self.assertEqual(branded["header_lines_fr"][1], "Chirurgienne-dentiste - Orthodontie")

    def test_fail_closed_display_language(self):
        self.assertEqual(clinical_term("NOT_COMPUTABLE"),
                         "Non calculable avec les données disponibles")
        self.assertEqual(measurement_value("82 deg", "BLOCKED"), "Non calculable")
        self.assertNotIn("R14", clinical_term("R14 NO VERIFIED PRACTITIONER SNAPSHOT"))
        self.assertNotIn("method_id", clinical_term("method_id_unknown"))
        self.assertNotIn("source-lock", clinical_term("source-lock SATISFIED"))

    def test_no_fictitious_arabic_practitioner_in_explicitly_unilingual_cabinet(self):
        canvas = MagicMock()
        base = BaseTemplate()
        cfg = synthetic_branding()
        base._draw_auto_header(
            canvas, cfg, None, colors.HexColor("#29476a"),
            colors.HexColor("#506379"), colors.HexColor("#a9b2c2"),
            *A4,
        )
        all_call_reprs = " ".join(map(str, canvas.method_calls))
        self.assertNotIn("الإسم الكامل", all_call_reprs)
        self.assertNotIn("طبيب جراح", all_call_reprs)
        self.assertIn("Dr Salma Atlas - DEMO", all_call_reprs)
        self.assertIn("Chirurgienne-dentiste - Orthodontie", all_call_reprs)

    def test_real_weasyprint_a4_all_five_cabinet_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "demo_brand_assets"
            media.mkdir()
            logo = Image.new("RGB", (160, 160), "white")
            draw = ImageDraw.Draw(logo)
            draw.ellipse((9, 9, 151, 151), fill="#29476a")
            draw.ellipse((30, 30, 130, 130), fill="#f8fafc")
            draw.text((69, 63), "A", fill="#29476a")
            logo.save(media / "logo_atlas_demo.png")
            previous_media = os.environ.get("MEDIA_ROOT")
            os.environ["MEDIA_ROOT"] = str(media)
            try:
                self._check_five_templates(tmp)
            finally:
                if previous_media is None:
                    os.environ.pop("MEDIA_ROOT", None)
                else:
                    os.environ["MEDIA_ROOT"] = previous_media

    def _check_five_templates(self, tmp):
            generator = BilanOrthoPDFGenerator(tmp)
            for template in TEMPLATES:
                with self.subTest(template=template):
                    vm = synthetic_vm(template)
                    vm.cabinet_config = serialize_document_branding(
                        SimpleNamespace(**vm.cabinet_config))
                    output = str(Path(tmp) / f"bilan_{template}.pdf")
                    source_projection = synthetic_approved_projection()
                    frozen_projection = copy.deepcopy(source_projection)
                    generator._generate_weasyprint(vm, output,
                        projection=source_projection, user=None)
                    self.assertEqual(source_projection, frozen_projection,
                        "The PDF presentation must never alter the clinical projection")
                    pdf = PdfReader(output)
                    self.assertGreaterEqual(len(pdf.pages), 1)
                    self.assertLessEqual(len(pdf.pages), 9,
                        "Rapport dense excessivement long (page finale orpheline possible)")
                    full = "\n".join(page.extract_text() or "" for page in pdf.pages)
                    last = pdf.pages[-1].extract_text() or ""
                    print("CEPH_V4_LAST_PAGE_DIAGNOSTIC", template, len(pdf.pages),
                          [len(p.extract_text() or "") for p in pdf.pages],
                          repr(last[-530:]))
                    capture_debug = os.environ.get("CEPH_V3_CAPTURE_DIR")
                    if capture_debug:
                        Path(capture_debug).mkdir(parents=True, exist_ok=True)
                        shutil.copy2(output, Path(capture_debug) / f"bilan_{template}.pdf")
                    self.assertGreater(len(last), 180,
                        "La dernière page ne doit pas contenir seulement une clôture")
                    self.assertIn("Non calculable", full)
                    self.assertIn("Bilan orthodontique", full)
                    phases = ("Analyse céphalométrique", "Analyse osseuse",
                              "Analyse dento-alvéolaire", "Examen des moulages",
                              "Résumé diagnostique", "Plan de traitement")
                    self.assertTrue(all(full.find(phases[i]) < full.find(phases[i+1])
                                        for i in range(len(phases)-1)))
                    for item in phases:
                        self.assertIn(item, full)
                    self.assertIn("moulages fictifs", full)
                    self.assertIn("dentiste de test", full)
                    self.assertIn("Plan fictif", full)
                    self.assertIn("SNA", full)
                    self.assertIn("IMPA", full)
                    self.assertNotIn("Mesure complémentaire", full)
                    self.assertNotIn("ANALYSIS MEASURE", full)
                    self.assertNotIn("ANALYSIS_MEASURE", full)
                    self.assertIn("Chirurgienne-dentiste - Orthodontie", full)
                    for forbidden in ("Lignes de mesures documentées",
                                      "Mesures disponibles (non validées)",
                                      "Indisponibles / non calculables",
                                      "Source et calibration", "Valeur et disponibilité",
                                      "Origine des mesures", "Vérification des données",
                                      "DOCUMENT CLINIQUE INCOMPLET",
                                      "PRÉ-BILAN",
                                      "document de travail non archivé",
                                      "Le référentiel de diagnostic n'est pas disponible",
                                      "La validation finale du praticien n'est pas enregistrée",
                                      "La validation finale du praticien n'est pas confirmée",
                                      "État des vérifications cliniques",
                                      "Vérifications encore nécessaires",
                                      "État documentaire", "Points à vérifier"):
                        self.assertNotIn(forbidden, full)
                    self.assertNotIn("NOT_COMPUTABLE", full)
                    self.assertNotIn("source-lock", full)
                    self.assertNotIn("EVIDENCE_GRAPH_V1", full)
                    self.assertNotIn("diagnostic_rule_registry_empty", full)
                    self.assertNotIn("Chaîne clinique R11", full)
                    capture = os.environ.get("CEPH_V3_CAPTURE_DIR")
                    if capture:
                        Path(capture).mkdir(parents=True, exist_ok=True)
                        shutil.copy2(output, Path(capture) / Path(output).name)
                    # Actual A5 prescription and A4 report from one *identical*
                    # authorized document configuration; not a fake stylesheet.
                    prescription = OrdonnanceGenerator(str(Path(tmp) / "ordonnances"))
                    patient = SimpleNamespace(nom="TEST", prenom="Synthétique",
                                              date_naissance=date(2014, 1, 1))
                    prescription_data = SimpleNamespace(
                        doc_date=date(2026, 10, 23), medications=[])
                    prescription_path = prescription.generate(
                        patient, prescription_data, custom_config=vm.cabinet_config)
                    ordonnance = PdfReader(prescription_path)
                    self.assertGreaterEqual(len(ordonnance.pages), 1)
                    ordonnance_text = "\n".join(p.extract_text() or "" for p in ordonnance.pages)
                    for shared_string in (
                        "Dr Salma Atlas - DEMO", "Chirurgienne-dentiste - Orthodontie",
                        "24 avenue de l'Exemple, Rabat (adresse fictive)", "06 00 00 00 00",
                    ):
                        self.assertIn(shared_string, full, "Missing bilan branding")
                        self.assertIn(shared_string, ordonnance_text, "Missing ordonnance branding")
                    self.assertFalse(any(
                        ("\u0600" <= ch <= "\u06ff") or ("\ufb50" <= ch <= "\ufeff")
                        for ch in full + ordonnance_text),
                        "Un cabinet sans en-tête arabe ne doit pas inventer un praticien arabe")
                    for actual_path in (output, prescription_path):
                        image_doc = fitz.open(actual_path)
                        for p in image_doc:
                            rects = [box for xref, *_ in p.get_images(full=True)
                                     for box in p.get_image_rects(xref)]
                            self.assertTrue(any(
                                box.x0 > p.rect.width-125 and
                                box.y0 > p.rect.height-135 and
                                33 < box.width < 66 and 33 < box.height < 66
                                for box in rects), f"Missing bottom-right QR on {actual_path}")
                    if capture:
                        shutil.copy2(prescription_path, Path(capture) / f"ordonnance_{template}.pdf")
                    for page in pdf.pages:
                        self.assertAlmostEqual(float(page.mediabox.width), A4[0], delta=0.5)
                        self.assertAlmostEqual(float(page.mediabox.height), A4[1], delta=0.5)
                        body = page.extract_text() or ""
                        self.assertIn("24 avenue de l'Exemple, Rabat (adresse fictive)", body,
                                      "Le pied de page BaseTemplate doit apparaître sur chaque page")

    def test_reportlab_fallback_uses_the_same_branding(self):
        with tempfile.TemporaryDirectory() as tmp:
            generator = BilanOrthoPDFGenerator(tmp)
            output = str(Path(tmp) / "reportlab.pdf")
            generator._generate_reportlab(synthetic_vm("heritage"), output,
                                          projection=synthetic_projection(n=25))
            pdf = PdfReader(output)
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            self.assertIn("24 avenue de l'Exemple, Rabat (adresse fictive)", text)
            self.assertNotIn("source-lock", text)
            self.assertNotIn("NOT_COMPUTABLE", text)
            for forbidden in ("Document clinique explicitement incomplet",
                              "État du bilan", "Révision du document",
                              "État des vérifications cliniques",
                              "Points restant à vérifier",
                              "validation finale du praticien",
                              "Le référentiel de diagnostic"):
                self.assertNotIn(forbidden, text)
            capture = os.environ.get("CEPH_V3_CAPTURE_DIR")
            if capture:
                Path(capture).mkdir(parents=True, exist_ok=True)
                shutil.copy2(output, Path(capture) / Path(output).name)

    def test_only_real_clinical_alerts_survive_workflow_panel_removal(self):
        with tempfile.TemporaryDirectory() as tmp:
            vm = synthetic_vm()
            study = synthetic_projection(n=2)
            study["stages"][0]["contraindications"] = [
                "Alerte clinique synthétique : vérification médicale requise"
            ]
            study["stages"][0]["contradictions"] = [
                "Résultats cliniques contradictoires à examiner"
            ]
            frozen_study = copy.deepcopy(study)
            output = str(Path(tmp) / "clinical_alerts.pdf")
            BilanOrthoPDFGenerator(tmp)._generate_weasyprint(
                vm, output, projection=study)
            text = "\n".join(p.extract_text() or "" for p in PdfReader(output).pages)
            self.assertIn("Alerte clinique synthétique", text)
            self.assertIn("Résultats cliniques contradictoires", text)
            self.assertNotIn("DOCUMENT CLINIQUE INCOMPLET", text)
            self.assertNotIn("PRÉ-BILAN", text)
            self.assertNotIn("Le référentiel de diagnostic", text)
            self.assertEqual(study, frozen_study)

    def test_custom_letterhead_image_repeated_on_all_pages(self):
        from PIL import Image, ImageDraw
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            media = root / "synthetic_media"
            media.mkdir()
            letterhead = media / "letterhead.png"
            picture = Image.new("RGB", (595, 842), "white")
            art = ImageDraw.Draw(picture)
            art.rectangle((0, 0, 595, 45), fill="#29476a")
            art.rectangle((0, 810, 595, 842), fill="#29476a")
            picture.save(letterhead)
            previous = os.environ.get("MEDIA_ROOT")
            os.environ["MEDIA_ROOT"] = str(media)
            try:
                vm = synthetic_vm("swiss")
                vm.cabinet_config.update(
                    use_letterhead=True, letterhead_path="letterhead.png",
                    hide_header=True, hide_footer=True,
                )
                output = str(root / "bilan_papier_personnalise.pdf")
                generator = BilanOrthoPDFGenerator(str(root))
                generator._generate_weasyprint(vm, output,
                    projection=synthetic_projection(n=65))
                pdf = PdfReader(output)
                self.assertGreaterEqual(len(pdf.pages), 1)
                for page in pdf.pages:
                    resources = page["/Resources"]
                    xobjects = resources.get("/XObject")
                    self.assertIsNotNone(xobjects)
                    images = xobjects.get_object()
                    self.assertTrue(any(
                        obj.get_object().get("/Subtype") == "/Image"
                        for obj in images.values()
                    ), "Image de papier à en-tête attendue sur chaque page")
                capture = os.environ.get("CEPH_V3_CAPTURE_DIR")
                if capture:
                    Path(capture).mkdir(parents=True, exist_ok=True)
                    shutil.copy2(output, Path(capture) / Path(output).name)
            finally:
                if previous is None:
                    os.environ.pop("MEDIA_ROOT", None)
                else:
                    os.environ["MEDIA_ROOT"] = previous

if __name__ == "__main__":
    unittest.main()
