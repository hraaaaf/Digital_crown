"""R17 premium PDF template: presentation-only, same authoritative backend truth.

Uses a deliberately synthetic study; no external clinical data, no patient media.
"""
from __future__ import annotations
import html
import re
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE="bilan_ortho_authoritative.html"

def _sample():
    return {
      "primary_color":"#003380", "secondary_color":"#64748B",
      "patient_nom":"TEST", "patient_prenom":"Synthetic", "patient_age":"12",
      "cephalo_source_analysis_id":41, "cephalo_source_analysis_revision":3,
      "date_analyse":"23/10/2026", "doctor_name":"Dr TEST",
      "is_pre_bilan":True, "contract_version":"CEPHALO_PDF_PROJECTION_V1",
      "authority":"BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO",
      "active_runtime_chain_verified":True,
      "document_state":"INCOMPLETE",
      "clinical_validation_reason":"R14 NO VERIFIED PRACTITIONER SNAPSHOT",
      "validation_warnings":[],
      "blocking_gates":["diagnostic_rule_registry_empty","r14_authoritative_snapshot_not_persisted"],
      "measurements":[
        {"measurement_id":"SNA",
         "value":"82 deg","availability_status":"AVAILABLE",
         "method":"STEINER_SNA_DEG_V1 v1","source":"EVIDENCE_GRAPH_V1","calibration":"non requise"},
        {"measurement_id":"RICKETTS FACIAL AXIS",
         "value":"NOT_COMPUTABLE","availability_status":"NOT_COMPUTABLE",
         "method":"RICKETTS_FACIAL_AXIS_CANONICAL_DEG_V2 v2",
         "source":"EVIDENCE_GRAPH_V1","calibration":"requise / absente"},
        {"measurement_id":"INJECTION <script>alert('x')</script>",
         "value":"NOT_COMPUTABLE","availability_status":"NOT_COMPUTABLE",
         "method":"<unsafe&method>","source":"<unsafe&source>","calibration":"<unsafe&calibration>"},
      ],
      "steiner_protocol":{
        "protocol_profile_id":"STEINER_STATIC_PROTOCOL_PROFILE_V1",
        "source_lock_status":"SATISFIED",
        "rows":[{"label":"SNA","value":"82 deg","reference":"82 deg","delta":"0 deg",
            "interpretation_status":"Référence historique — aucune classification clinique"}],
      },
      "tweed_merrifield_protocol":{
        "protocol_profile_id":"TWEED_MERRIFIELD_DC_PROTOCOL_PROFILE_V1",
        "source_lock_status":"SATISFIED",
        "rows":[{"label":"FMA","value":"22 deg","profile_section":"TWEED_1954_TRIANGLE_DC_PO_OR_V1",
            "reference_authority":"CONTEXT_ONLY_NO_RUNTIME_DELTA",
            "interpretation_status":"RAW_MEASUREMENT_WITH_SOURCE_CONTEXT_ONLY"}],
      },
      "stages":[
        {"stage_id":"R11","title":"Diagnostic scientifique","presentation_state":"BLOCKED",
        "summary":"Ne jamais générer un diagnostic",
        "blocking_gates":["diagnostic_rule_registry_empty"],
        "missing_data_refs":["r11_provenance_missing"],
        "contradictions":[],"contraindications":[],
        "provenance":[{"label":"Autorité","value":"EVIDENCE_GRAPH_V1"}]},
      ],
    }

def render_sample():
    env=Environment(loader=FileSystemLoader(str(ROOT/"backend/templates")),
      autoescape=select_autoescape(enabled_extensions=("html","xml"),default_for_string=True))
    return env.get_template(TEMPLATE).render(_sample())

class PremiumCephalometryPdfTests(unittest.TestCase):
    def test_compiles_into_complete_html(self):
        document=render_sample()
        self.assertIn("<!DOCTYPE html>",document)
        self.assertIn("Étude céphalométrique.",document)
        self.assertIn("DIGITAL <span>CROWN</span>",document)
        self.assertIn("CEPHALO_PDF_PROJECTION_V1",document)

    def test_all_source_fields_survive_in_same_row(self):
        document=render_sample()
        self.assertIn("STEINER_SNA_DEG_V1 v1",document)
        self.assertIn("EVIDENCE_GRAPH_V1",document)
        self.assertIn("non requise",document)
        self.assertIn("RICKETTS_FACIAL_AXIS_CANONICAL_DEG_V2 v2",document)
        self.assertIn("requise / absente",document)

    def test_missing_measurements_are_never_silently_removed(self):
        doc=render_sample()
        self.assertEqual(doc.count('class="is-missing"'),2)
        self.assertIn("NOT_COMPUTABLE",doc)
        self.assertIn("Indisponibles / non calculables",doc)
        self.assertIn("<strong>1</strong><span>Mesures disponibles",doc)
        self.assertIn("<strong>2</strong><span>Indisponibles",doc)

    def test_untrusted_content_is_html_escaped(self):
        doc=render_sample()
        self.assertNotIn("<script>",doc)
        self.assertNotIn("<unsafe&source>",doc)
        self.assertIn("&lt;script&gt;",doc)
        self.assertIn("&lt;unsafe&amp;source&gt;",doc)
        self.assertIn("&lt;unsafe&amp;calibration&gt;",doc)

    def test_original_clinical_safety_and_source_lock_states_remain(self):
        doc=render_sample()
        for s in ["DOCUMENT CLINIQUE INCOMPLET","R14 NO VERIFIED PRACTITIONER SNAPSHOT",
                  "PRÉ-BILAN","SATISFIED","BLOCKED","diagnostic_rule_registry_empty",
                  "r14_authoritative_snapshot_not_persisted","r11_provenance_missing"]:
            self.assertIn(s,doc)
        self.assertNotIn("Classe II diagnostiquée",doc)
        self.assertNotIn("Traitement indiqué",doc)

    def test_historical_norm_stays_context_not_diagnosis(self):
        doc=render_sample()
        self.assertIn("Référence historique — aucune classification clinique",doc)
        self.assertIn("CONTEXT_ONLY_NO_RUNTIME_DELTA",doc)
        self.assertIn("RAW_MEASUREMENT_WITH_SOURCE_CONTEXT_ONLY",doc)
        self.assertIn("TWEED_1954_TRIANGLE_DC_PO_OR_V1",doc)

    def test_page_and_table_print_contract(self):
        doc=render_sample()
        self.assertIn("@page {",doc)
        self.assertIn("table-header-group",doc)
        self.assertIn("break-inside: avoid",doc)
        self.assertIn("Source et calibration",doc)

if __name__=="__main__":
    unittest.main()
