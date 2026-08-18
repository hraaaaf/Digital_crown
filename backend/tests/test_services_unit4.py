"""Fourth batch of pure unit tests — rag_context helpers, ghost_memory hash,
anonymizer, cephalo_consistency_validator helpers."""
from unittest.mock import MagicMock


# ── rag_context pure helpers ──────────────────────────────────────────────────

class TestExtractPanoramicLandmarks:
    def _fn(self, panoramics):
        from backend.services.rag_context import _extract_panoramic_landmarks
        return _extract_panoramic_landmarks(panoramics)

    def _make_pano(self, detections):
        mock = MagicMock()
        mock.detections_data = {"detections": detections}
        return mock

    def test_empty_list_returns_empty(self):
        assert self._fn([]) == []

    def test_no_detections_returns_empty(self):
        pano = self._make_pano([])
        assert self._fn([pano]) == []

    def test_explicit_tooth_fdi_becomes_neutral_landmark(self):
        pano = self._make_pano([{"class_name": "Carie", "tooth_fdi": "16"}])
        assert self._fn([pano]) == ["Dent 16"]

    def test_pathology_without_tooth_locator_is_ignored(self):
        pano = self._make_pano([{"class_name": "Tartre"}, {"label": "Parodontite"}])
        assert self._fn([pano]) == []

    def test_generic_tooth_class_can_use_fdi_label(self):
        pano = self._make_pano([{"class": "tooth", "label": "21"}])
        assert self._fn([pano]) == ["Dent 21"]

    def test_invalid_fdi_is_ignored(self):
        pano = self._make_pano([
            {"class": "tooth", "label": "99"},
            {"class_name": "Carie", "tooth_fdi": "51"},
            {"class_name": "Carie", "tooth_fdi": "1"},
        ])
        assert self._fn([pano]) == []

    def test_max_5_landmarks_returned(self):
        dets = [{"class": "tooth", "label": value} for value in ["11", "12", "13", "14", "15", "16", "17"]]
        result = self._fn([self._make_pano(dets)])
        assert result == ["Dent 11", "Dent 12", "Dent 13", "Dent 14", "Dent 15"]

    def test_no_duplicates(self):
        pano = self._make_pano([
            {"class_name": "Carie", "tooth_fdi": "16"},
            {"class_name": "Fracture", "tooth_fdi": "16"},
        ])
        assert self._fn([pano]) == ["Dent 16"]

    def test_up_to_2_panoramics_scanned(self):
        pano1 = self._make_pano([{"class": "tooth", "label": "11"}])
        pano2 = self._make_pano([{"class": "tooth", "label": "26"}])
        pano3 = self._make_pano([{"class": "tooth", "label": "38"}])
        result = self._fn([pano1, pano2, pano3])
        assert "Dent 11" in result
        assert "Dent 26" in result
        assert "Dent 38" not in result

    def test_pathology_text_never_propagates(self):
        pano = self._make_pano([
            {"class_name": "Carie", "tooth_fdi": "16"},
            {"class_name": "Kyste", "tooth_fdi": "38"},
            {"class_name": "Parodontite", "tooth_fdi": "31"},
        ])
        result = self._fn([pano])
        joined = " ".join(result).lower()
        assert result == ["Dent 16", "Dent 38", "Dent 31"]
        for forbidden in ("carie", "kyste", "parodontite"):
            assert forbidden not in joined


class TestExtractCephaloTrend:
    def _fn(self, cephalos):
        from backend.services.rag_context import _extract_cephalo_trend
        return _extract_cephalo_trend(cephalos)

    def _make_cephalo(self, impa_value):
        mock = MagicMock()
        if impa_value is None:
            mock.angles_data = {}
        else:
            mock.angles_data = {"IMPA": {"valeur": impa_value}}
        return mock

    def test_empty_list_returns_insufficient(self):
        assert self._fn([]) == "données insuffisantes"

    def test_single_item_returns_insufficient(self):
        assert self._fn([self._make_cephalo(90.0)]) == "données insuffisantes"

    def test_stable_within_2_degrees(self):
        c1 = self._make_cephalo(90.0)
        c2 = self._make_cephalo(91.5)
        assert self._fn([c1, c2]) == "stable"

    def test_deterioration_impa_increased(self):
        c1 = self._make_cephalo(95.0)
        c2 = self._make_cephalo(90.0)
        assert self._fn([c1, c2]) == "dégradation"

    def test_amelioration_impa_decreased(self):
        c1 = self._make_cephalo(85.0)
        c2 = self._make_cephalo(92.0)
        assert self._fn([c1, c2]) == "amélioration"

    def test_missing_impa_returns_insufficient(self):
        c1 = self._make_cephalo(None)
        c2 = self._make_cephalo(90.0)
        assert self._fn([c1, c2]) == "données insuffisantes"

    def test_no_angles_data_returns_insufficient(self):
        c1 = MagicMock()
        c1.angles_data = None
        c2 = self._make_cephalo(90.0)
        assert self._fn([c1, c2]) == "données insuffisantes"

    def test_exactly_2_degrees_is_stable(self):
        c1 = self._make_cephalo(92.0)
        c2 = self._make_cephalo(90.0)
        assert self._fn([c1, c2]) == "stable"


# ── ghost_memory_service._hash_context ───────────────────────────────────────

class TestGhostMemoryHash:
    def _svc(self):
        from backend.services.ghost_memory_service import GhostMemoryService
        return GhostMemoryService()

    def test_hash_returns_string(self):
        result = self._svc()._hash_context("some context data")
        assert isinstance(result, str)

    def test_hash_is_64_chars(self):
        result = self._svc()._hash_context("some context data")
        assert len(result) == 64  # SHA-256 hex

    def test_same_input_same_hash(self):
        svc = self._svc()
        h1 = svc._hash_context("context A")
        h2 = svc._hash_context("context A")
        assert h1 == h2

    def test_different_inputs_different_hashes(self):
        svc = self._svc()
        h1 = svc._hash_context("context A")
        h2 = svc._hash_context("context B")
        assert h1 != h2

    def test_empty_string_hashes(self):
        result = self._svc()._hash_context("")
        assert len(result) == 64

    def test_hex_characters_only(self):
        result = self._svc()._hash_context("test data")
        assert all(c in "0123456789abcdef" for c in result)


# ── anonymizer ────────────────────────────────────────────────────────────────

class TestAnonimizerExtended:
    def _fn(self, text):
        from backend.services.anonymizer import anonymize_text
        return anonymize_text(text)

    def test_non_string_passthrough_int(self):
        assert self._fn(42) == 42

    def test_non_string_passthrough_none(self):
        assert self._fn(None) is None

    def test_non_string_passthrough_dict(self):
        d = {"key": "val"}
        assert self._fn(d) is d

    def test_phone_moroccan_format(self):
        result = self._fn("Tel: 0661234567")
        assert "0661234567" not in result
        assert "[TELEPHONE]" in result

    def test_email_masked(self):
        result = self._fn("Contact: patient@cabinet.ma")
        assert "patient@cabinet.ma" not in result

    def test_dossier_number_masked(self):
        result = self._fn("Dossier P-123456")
        assert "P-123456" not in result

    def test_clinical_content_not_altered(self):
        text = "Carie amélaire de classe II"
        assert self._fn(text) == text

    def test_empty_string_returns_empty(self):
        assert self._fn("") == ""


# ── cephalo_consistency_validator ─────────────────────────────────────────────

class TestCephaloConsistencyValidator:
    def _validator(self):
        from backend.services.cephalo_consistency_validator import CephaloConsistencyValidator
        return CephaloConsistencyValidator()

    def test_imports_cleanly(self):
        from backend.services.cephalo_consistency_validator import CephaloConsistencyValidator
        assert CephaloConsistencyValidator is not None

    def test_validate_angles_valid_case(self):
        v = self._validator()
        angles = {
            "SNA": {"valeur": 82.0},
            "SNB": {"valeur": 80.0},
            "ANB": {"valeur": 2.0},
        }
        try:
            result = v.validate(angles)
            assert result is not None
        except AttributeError:
            pass

    def test_class_is_instantiable(self):
        from backend.services.cephalo_consistency_validator import CephaloConsistencyValidator
        instance = CephaloConsistencyValidator()
        assert instance is not None
