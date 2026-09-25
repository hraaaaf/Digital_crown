"""Tenth batch — PanoramicReportEngine pure helpers and zka_service exception path."""
import pytest


# ── PanoramicReportEngine pure helpers ────────────────────────────────────────

class TestFmtTeethPhrase:
    def _eng(self):
        from backend.services.panoramic_report_engine import PanoramicReportEngine
        return PanoramicReportEngine()

    def test_empty_list_returns_prefix(self):
        assert self._eng()._fmt_teeth_phrase([], "Absence") == "Absence"

    def test_single_tooth(self):
        result = self._eng()._fmt_teeth_phrase([16], "Absence")
        assert "16" in result
        assert "dent" in result

    def test_two_teeth(self):
        result = self._eng()._fmt_teeth_phrase([16, 26], "Absence")
        assert "16" in result
        assert "26" in result
        assert "dents" in result

    def test_three_teeth_comma_separated(self):
        result = self._eng()._fmt_teeth_phrase([16, 26, 36], "Observation")
        assert "16" in result
        assert "36" in result
        assert "et" in result


class TestTeethList:
    def _eng(self):
        from backend.services.panoramic_report_engine import PanoramicReportEngine
        return PanoramicReportEngine()

    def test_single_tooth(self):
        assert "16" in self._eng()._teeth_list([16])

    def test_two_teeth(self):
        result = self._eng()._teeth_list([16, 26])
        assert "16" in result
        assert "26" in result
        assert "et" in result

    def test_three_teeth(self):
        result = self._eng()._teeth_list([16, 26, 36])
        assert "16" in result
        assert "36" in result


class TestObservationPhrase:
    def _eng(self):
        from backend.services.panoramic_report_engine import PanoramicReportEngine
        return PanoramicReportEngine()

    def test_carie_email_preserves_manual_label(self):
        result = self._eng()._observation_phrase("carie_email", [16])
        assert "émail" in result.lower() or "email" in result.lower()
        assert "16" in result

    def test_lesion_periapicale_preserves_manual_label(self):
        result = self._eng()._observation_phrase("lesion_periapicale", [16])
        assert "périapicale" in result.lower() or "periapicale" in result.lower()
        assert "16" in result

    def test_implant_preserves_manual_label(self):
        result = self._eng()._observation_phrase("implant", [36])
        assert "implant" in result.lower()
        assert "36" in result

    def test_unknown_anomaly_uses_neutral_fallback(self):
        result = self._eng()._observation_phrase("anomalie_inconnue_xyz", [11])
        assert "anomalie_inconnue_xyz" in result
        assert "11" in result

    def test_atm_observation_does_not_require_tooth_number(self):
        result = self._eng()._observation_phrase("condyle_asymetrie", [16])
        assert "asymétrie condylienne" in result.lower()


class TestBuildSynthesis:
    def _eng(self):
        from backend.services.panoramic_report_engine import PanoramicReportEngine
        return PanoramicReportEngine()

    def test_empty_returns_no_synthetic_finding(self):
        result = self._eng()._build_synthesis({}, [])
        assert result == []

    def test_documented_tooth_observations_are_preserved_without_diagnosis(self):
        section_items = {
            "LÉSIONS CARIEUSES": {"carie_email": [16, 26]},
        }
        result = self._eng()._build_synthesis(section_items, [])
        assert result == ["Carie de l'émail — les dents 16 et 26."]
        assert "prioritaire" not in " ".join(result).lower()

    def test_absent_teeth_are_preserved_as_observations(self):
        section_items = {
            "DENTITION ET ANOMALIES DENTAIRES": {"dent_absente": [16, 26]},
        }
        result = self._eng()._build_synthesis(section_items, [])
        assert result == ["Dent absente — les dents 16 et 26."]
        assert "réhabil" not in " ".join(result).lower()

    def test_general_findings_are_restated_without_upgrading_them(self):
        result = self._eng()._build_synthesis(
            {},
            ["Alvéolyse horizontale généralisée légère"],
        )
        assert result == ["Alvéolyse horizontale généralisée légère."]

    def test_denture_mixte_is_context_not_general_pathology(self):
        report = self._eng().generate_markdown(global_findings=["denture_mixte"])
        assert "### CONTEXTE DENTAIRE DOCUMENTÉ" in report
        assert "Denture mixte documentée par le praticien." in report
        assert "### CONSTATATIONS GÉNÉRALES" not in report


class TestGenerateMarkdown:
    def _eng(self):
        from backend.services.panoramic_report_engine import PanoramicReportEngine
        return PanoramicReportEngine()

    def test_empty_input_returns_string(self):
        result = self._eng().generate_markdown()
        assert isinstance(result, str)
        assert len(result) > 50

    def test_contains_synthesis_section(self):
        result = self._eng().generate_markdown()
        assert "### SYNTHÈSE" in result

    def test_contains_structured_technique_section(self):
        result = self._eng().generate_markdown()
        assert "### TECHNIQUE" in result

    def test_empty_report_is_fail_closed(self):
        result = self._eng().generate_markdown()
        assert "Aucune constatation n'a été documentée" in result
        assert "ne constitue pas une conclusion de normalité radiographique" in result
        assert "Les territoires sans annotation explicite restent non documentés" in result
        assert "CONDUITE À TENIR" not in result
        assert "HBMD" not in result
        assert "HBFD" not in result
        assert "HBGD" not in result
        assert "HBJD" not in result

    def test_with_manual_anomaly_is_practitioner_observation(self):
        result = self._eng().generate_markdown(
            manual_anomalies={16: ["carie_email"]}
        )
        assert "Carie de l'émail — la dent 16." in result
        assert "16" in result
        assert "CONDUITE À TENIR" not in result

    def test_with_dict_detections(self):
        result = self._eng().generate_markdown(
            detections={"detections": []}
        )
        assert isinstance(result, str)

    def test_global_finding_mixed(self):
        result = self._eng().generate_markdown(
            global_findings=["denture_mixte"]
        )
        assert "### CONTEXTE DENTAIRE DOCUMENTÉ" in result
        assert "Denture mixte documentée par le praticien." in result

    def test_singleton_importable(self):
        from backend.services.panoramic_report_engine import panoramic_report_engine
        assert panoramic_report_engine is not None


# ── zka_service exception path ────────────────────────────────────────────────

class TestZkaServiceExceptionPath:
    def test_encrypt_with_invalid_key_raises(self):
        from backend.services.zka_service import ZKAService
        with pytest.raises(Exception):
            ZKAService.encrypt_payload({"data": "test"}, "not_a_valid_hex_key")

    def test_decrypt_with_invalid_blob_raises(self):
        from backend.services.zka_service import ZKAService
        key = ZKAService.generate_master_key()
        with pytest.raises(Exception):
            ZKAService.decrypt_payload("not_valid_base64_blob!!!", key)
