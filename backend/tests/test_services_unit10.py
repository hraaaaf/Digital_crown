"""Tenth batch — PanoramicReportEngine pure helpers,
treatment_plan_engine exception path, zka_service exception path."""
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
        result = self._eng()._fmt_teeth_phrase([16, 26, 36], "Carie")
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


class TestPhraseFor:
    def _eng(self):
        from backend.services.panoramic_report_engine import PanoramicReportEngine
        return PanoramicReportEngine()

    def test_carie_email_has_email(self):
        result = self._eng()._phrase_for("carie_email", [16])
        assert "émail" in result.lower() or "email" in result.lower()

    def test_lesion_periapicale(self):
        result = self._eng()._phrase_for("lesion_periapicale", [16])
        assert "périapicale" in result or "periapicale" in result.lower()

    def test_implant(self):
        result = self._eng()._phrase_for("implant", [36])
        assert "implant" in result.lower()

    def test_unknown_anomaly_uses_fallback(self):
        result = self._eng()._phrase_for("anomalie_inconnue_xyz", [11])
        assert "11" in result

    def test_includes_tooth_number(self):
        result = self._eng()._phrase_for("carie_email", [16])
        assert "16" in result

    def test_returns_string(self):
        assert isinstance(self._eng()._phrase_for("tartre", [16]), str)


class TestBuildSynthesis:
    def _eng(self):
        from backend.services.panoramic_report_engine import PanoramicReportEngine
        return PanoramicReportEngine()

    def test_empty_returns_normal_string(self):
        result = self._eng()._build_synthesis({}, [], [])
        assert isinstance(result, str)
        assert len(result) > 10
        assert "normale" in result.lower() or "normal" in result.lower()

    def test_caries_mentioned_in_synthesis(self):
        anomaly_map = {"carie_email": [16, 26]}
        result = self._eng()._build_synthesis(anomaly_map, [], [])
        assert "carie" in result.lower() or "carieux" in result.lower()

    def test_urgent_key_flagged(self):
        anomaly_map = {"carie_profonde": [16]}
        result = self._eng()._build_synthesis(anomaly_map, [], [])
        assert "prioritaire" in result.lower() or "⚠️" in result

    def test_absent_teeth_mentioned(self):
        result = self._eng()._build_synthesis({}, [16, 26], [])
        assert "Édentement" in result or "dent" in result.lower()

    def test_prostheses_mentioned(self):
        anomaly_map = {"implant": [36]}
        result = self._eng()._build_synthesis(anomaly_map, [], [])
        assert "implant" in result.lower() or "réhabilitation" in result.lower()


class TestBuildRecommendations:
    def _eng(self):
        from backend.services.panoramic_report_engine import PanoramicReportEngine
        return PanoramicReportEngine()

    def test_empty_map_returns_empty(self):
        result = self._eng()._build_recommendations({}, [])
        assert result == []

    def test_caries_recommendation_present(self):
        anomaly_map = {"carie_email": [16]}
        result = self._eng()._build_recommendations(anomaly_map, [])
        assert len(result) > 0
        assert any("HBMD" in r for r in result)

    def test_absent_teeth_recommendation(self):
        result = self._eng()._build_recommendations({}, [16])
        assert any("Réhabilitation" in r or "réhabilitation" in r.lower() for r in result)

    def test_no_duplicates(self):
        # Same anomaly on multiple teeth — recommendation appears only once
        anomaly_map = {"tartre": [16, 26, 36]}
        result = self._eng()._build_recommendations(anomaly_map, [])
        ccam_count = sum(1 for r in result if "HBJD001" in r)
        assert ccam_count == 1

    def test_returns_list(self):
        assert isinstance(self._eng()._build_recommendations({}, []), list)


class TestGenerateMarkdown:
    def _eng(self):
        from backend.services.panoramic_report_engine import PanoramicReportEngine
        return PanoramicReportEngine()

    def test_empty_input_returns_string(self):
        result = self._eng().generate_markdown()
        assert isinstance(result, str)
        assert len(result) > 50

    def test_contains_synthese_section(self):
        result = self._eng().generate_markdown()
        assert "SYNTHÈSE" in result or "SYNTH" in result

    def test_contains_resultats_section(self):
        result = self._eng().generate_markdown()
        assert "RÉSULTATS" in result or "RESULTATS" in result

    def test_with_manual_anomaly(self):
        result = self._eng().generate_markdown(
            manual_anomalies={16: ["carie_email"]}
        )
        assert "16" in result

    def test_with_dict_detections(self):
        # When detections is passed as {"detections": [...]}
        result = self._eng().generate_markdown(
            detections={"detections": []}
        )
        assert isinstance(result, str)

    def test_global_finding_mixed(self):
        result = self._eng().generate_markdown(
            global_findings=["denture_mixte"]
        )
        assert "mixte" in result.lower()

    def test_singleton_importable(self):
        from backend.services.panoramic_report_engine import panoramic_report_engine
        assert panoramic_report_engine is not None


# ── treatment_plan_engine exception path ──────────────────────────────────────

class TestTreatmentPlanEngineExceptionPath:
    def _engine(self):
        from backend.services.treatment_plan_engine import TreatmentPlanEngine
        return TreatmentPlanEngine()

    def test_invalid_detections_returns_error(self):
        # Pass a string instead of list → iterating will give chars, .get() will fail
        result = self._engine().generate_plan("invalid_input")
        assert "error" in result


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
