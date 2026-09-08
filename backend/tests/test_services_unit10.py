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

    def test_empty_is_explicitly_not_a_normality_conclusion(self):
        result = self._eng()._build_synthesis({}, [], [])
        assert isinstance(result, str)
        assert "aucune anomalie" in result.lower()
        assert "ne constitue pas une conclusion de normalité" in result.lower()

    def test_documented_tooth_observations_are_counted_without_diagnosis(self):
        anomaly_map = {"carie_email": [16, 26]}
        result = self._eng()._build_synthesis(anomaly_map, [], [])
        assert "2 observation(s) dentaire(s)" in result
        assert "documentée(s) par le praticien" in result
        assert "prioritaire" not in result.lower()

    def test_absent_teeth_are_counted_as_observations(self):
        result = self._eng()._build_synthesis({}, [16, 26], [])
        assert "2 observation(s) dentaire(s)" in result
        assert "réhabil" not in result.lower()

    def test_general_findings_are_counted_as_practitioner_findings(self):
        result = self._eng()._build_synthesis({}, [], ["alveolyse_gen_legere"])
        assert "1 constat(s) général(aux)" in result
        assert "documenté(s) par le praticien" in result

    def test_denture_mixte_is_not_counted_as_general_pathology(self):
        result = self._eng()._build_synthesis({}, [], ["denture_mixte"])
        assert "aucune anomalie" in result.lower()
        assert "constat(s) général(aux)" not in result


class TestGenerateMarkdown:
    def _eng(self):
        from backend.services.panoramic_report_engine import PanoramicReportEngine
        return PanoramicReportEngine()

    def test_empty_input_returns_string(self):
        result = self._eng().generate_markdown()
        assert isinstance(result, str)
        assert len(result) > 50

    def test_contains_radiographic_synthesis_section(self):
        result = self._eng().generate_markdown()
        assert "SYNTHÈSE RADIOGRAPHIQUE" in result

    def test_contains_resultats_section(self):
        result = self._eng().generate_markdown()
        assert "RÉSULTATS" in result or "RESULTATS" in result

    def test_empty_report_is_fail_closed(self):
        result = self._eng().generate_markdown()
        assert "non documentés / non évalués" in result
        assert "conclusion de normalité" in result
        assert "CONDUITE À TENIR" not in result
        assert "HBMD" not in result
        assert "HBFD" not in result
        assert "HBGD" not in result
        assert "HBJD" not in result

    def test_with_manual_anomaly_is_practitioner_observation(self):
        result = self._eng().generate_markdown(
            manual_anomalies={16: ["carie_email"]}
        )
        assert "Observation praticien" in result
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
        assert "Observation praticien : denture mixte" in result

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
