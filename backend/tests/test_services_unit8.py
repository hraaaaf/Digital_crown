"""Eighth batch — CephaloEngine geometric utils."""
import math


# ── CephaloEngine geometric utils ─────────────────────────────────────────────

class TestCephaloEngineGetPoint:
    def _eng(self):
        from backend.services.cephalo_engine import CephaloEngine
        return CephaloEngine()

    def test_returns_tuple_when_key_present(self):
        eng = self._eng()
        pts = {"S": [10.0, 20.0]}
        result = eng._get_point(pts, "S")
        assert result == (10.0, 20.0)

    def test_alias_resolution(self):
        eng = self._eng()
        # "Sella" is an alias for "S"
        pts = {"Sella": [5.0, 15.0]}
        result = eng._get_point(pts, "S")
        assert result == (5.0, 15.0)

    def test_missing_key_returns_none(self):
        eng = self._eng()
        result = eng._get_point({}, "S")
        assert result is None

    def test_list_input_returns_tuple(self):
        eng = self._eng()
        result = eng._get_point({"N": [100, 200]}, "N")
        assert result == (100, 200)

    def test_tuple_input_returns_tuple(self):
        eng = self._eng()
        result = eng._get_point({"N": (100, 200)}, "N")
        assert result == (100, 200)


class TestCephaloEngineClinicalAngle:
    def _eng(self):
        from backend.services.cephalo_engine import CephaloEngine
        return CephaloEngine()

    def test_parallel_lines_zero_angle(self):
        eng = self._eng()
        # Both lines go horizontally right
        result = eng._get_clinical_angle((0, 0), (10, 0), (0, 5), (10, 5))
        assert result is not None
        assert abs(result) < 1.0  # nearly 0°

    def test_perpendicular_lines_90_degrees(self):
        eng = self._eng()
        # Horizontal vs vertical
        result = eng._get_clinical_angle((0, 0), (10, 0), (5, 0), (5, 10))
        assert result is not None
        assert abs(result - 90.0) < 1.0

    def test_returns_float(self):
        eng = self._eng()
        result = eng._get_clinical_angle((0, 0), (10, 0), (0, 5), (10, 5))
        assert isinstance(result, float)

    def test_invert_flag(self):
        eng = self._eng()
        r1 = eng._get_clinical_angle((0, 0), (10, 0), (0, 5), (10, 5), invert=False)
        r2 = eng._get_clinical_angle((0, 0), (10, 0), (0, 5), (10, 5), invert=True)
        # Invert should give 180 - r1
        assert abs((r1 + r2) - 180.0) < 1.0

    def test_none_point_returns_none(self):
        eng = self._eng()
        result = eng._get_clinical_angle(None, (10, 0), (0, 5), (10, 5))
        assert result is None

    def test_result_in_range_0_to_180(self):
        eng = self._eng()
        import random
        random.seed(42)
        for _ in range(10):
            p1 = (random.uniform(0, 100), random.uniform(0, 100))
            p2 = (random.uniform(0, 100), random.uniform(0, 100))
            p3 = (random.uniform(0, 100), random.uniform(0, 100))
            p4 = (random.uniform(0, 100), random.uniform(0, 100))
            result = eng._get_clinical_angle(p1, p2, p3, p4)
            if result is not None:
                assert 0.0 <= result <= 180.0


class TestCephaloEngineOrthogonalProjection:
    def _eng(self):
        from backend.services.cephalo_engine import CephaloEngine
        return CephaloEngine()

    def test_point_on_line_projects_to_itself(self):
        eng = self._eng()
        # A point already on the line (0,0)→(10,0) at x=5, y=0
        result = eng._get_orthogonal_projection((0, 0), (10, 0), (5, 0))
        assert abs(result[0] - 5.0) < 0.01
        assert abs(result[1] - 0.0) < 0.01

    def test_point_above_horizontal_line(self):
        eng = self._eng()
        # Horizontal line y=0, point at (5, 3)
        result = eng._get_orthogonal_projection((0, 0), (10, 0), (5, 3))
        assert abs(result[1] - 0.0) < 0.01
        assert abs(result[0] - 5.0) < 0.01

    def test_degenerate_line_returns_target(self):
        eng = self._eng()
        # Zero-length line — should return target
        result = eng._get_orthogonal_projection((5, 5), (5, 5), (3, 7))
        assert result == (3, 7)

    def test_returns_tuple(self):
        eng = self._eng()
        result = eng._get_orthogonal_projection((0, 0), (10, 0), (5, 5))
        assert isinstance(result, tuple)
        assert len(result) == 2
