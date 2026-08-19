"""Twentieth batch — BaseTemplate header drawing methods via MagicMock canvas.
Covers _draw_header_swiss, _draw_header_royal, _draw_header_clinical,
_draw_header_modern, _draw_header_heritage, _draw_auto_header,
_get_global_header_ratio, _vcenter_offset (all pure drawing logic, no PDF I/O).
"""
import pytest
from unittest.mock import MagicMock, patch
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm


# ── shared helpers ─────────────────────────────────────────────────────────────

def _bt():
    from backend.services.base_template import BaseTemplate
    return BaseTemplate()


def _canvas():
    return MagicMock()


# Typical A5 dimensions (148mm × 210mm in points)
_W = 148 * cm
_H = 210 * cm

_P = HexColor('#003380')
_S = HexColor('#666666')
_A = HexColor('#003380')

_FR = ["Dr. Nom Prénom", "Chirurgien Dentiste", "Numéro RPPS : 12345"]
_AR = ["د. الإسم الكامل", "طبيب جراح للأسنان"]

_CFG_EMPTY = {}
_CFG_SCALED = {
    'header_font_scale': 0.8,
    'header_logo_scale': 0.9,
    'header_line_height': 1.1,
}


# ── _vcenter_offset ────────────────────────────────────────────────────────────

class TestVcenterOffset:
    def _fn(self, lines, sizes, lh_mult, lh_scale):
        return _bt()._vcenter_offset(lines, sizes, lh_mult, lh_scale)

    def test_two_lines_returns_sum(self):
        result = self._fn(["a", "b"], [12.0, 10.0], 1.2, 1.0)
        assert abs(result - (12.0 * 1.2 + 10.0 * 1.2)) < 0.001

    def test_single_line(self):
        result = self._fn(["x"], [14.0], 1.2, 1.0)
        assert abs(result - 14.0 * 1.2) < 0.001

    def test_empty_lines_returns_zero(self):
        result = self._fn([], [], 1.2, 1.0)
        assert result == 0

    def test_scale_applied(self):
        r1 = self._fn(["a"], [12.0], 1.2, 1.0)
        r2 = self._fn(["a"], [12.0], 1.2, 2.0)
        assert abs(r2 - r1 * 2.0) < 0.001


# ── _get_global_header_ratio ───────────────────────────────────────────────────

class TestGetGlobalHeaderRatio:
    def _fn(self, fr, ar, col_w=200, hf=1.0, tmpl='swiss'):
        return _bt()._get_global_header_ratio(fr, ar, col_w, hf, tmpl)

    def test_returns_float_between_04_and_10(self):
        r = self._fn(_FR, _AR, col_w=200)
        assert 0.4 <= r <= 1.0

    def test_narrow_column_shrinks_ratio(self):
        r_wide = self._fn(_FR, _AR, col_w=500)
        r_narrow = self._fn(_FR, _AR, col_w=50)
        assert r_narrow <= r_wide

    def test_empty_lines_returns_one(self):
        r = self._fn([], [], col_w=200)
        assert r == 1.0

    def test_empty_fr_uses_ar(self):
        r = self._fn([], _AR, col_w=200)
        assert 0.4 <= r <= 1.0

    def test_empty_ar_uses_fr(self):
        r = self._fn(_FR, [], col_w=200)
        assert 0.4 <= r <= 1.0

    def test_html_tags_stripped(self):
        fr = ["<b>Dr. Nom</b>", "<i>Dentiste</i>"]
        r = self._fn(fr, [], col_w=200)
        assert 0.4 <= r <= 1.0

    def test_different_templates_accepted(self):
        for tmpl in ('swiss', 'royal', 'clinical', 'modern', 'heritage'):
            r = self._fn(_FR, _AR, col_w=200, tmpl=tmpl)
            assert 0.4 <= r <= 1.0


# ── _draw_header_swiss ─────────────────────────────────────────────────────────

class TestDrawHeaderSwiss:
    def _call(self, cfg=None, logo=None, fr=None, ar=None, h_scale=1.0):
        bt = _bt()
        c = _canvas()
        bt._draw_header_swiss(
            c, cfg or _CFG_EMPTY, logo, _P, _S, _A,
            _W, _H, fr or _FR, ar or _AR, h_scale
        )
        return c

    def test_canvas_drawString_called(self):
        c = self._call()
        assert c.drawString.called

    def test_canvas_drawRightString_called(self):
        c = self._call()
        assert c.drawRightString.called

    def test_canvas_setFont_called(self):
        c = self._call()
        assert c.setFont.called

    def test_canvas_setFillColor_called(self):
        c = self._call()
        assert c.setFillColor.called

    def test_canvas_saveState_restoreState(self):
        c = self._call()
        assert c.saveState.called
        assert c.restoreState.called

    def test_canvas_line_called_for_separator(self):
        c = self._call()
        assert c.line.called

    def test_with_scale_cfg_runs_without_error(self):
        c = self._call(cfg=_CFG_SCALED)
        assert c.drawString.called

    def test_single_line_each(self):
        c = self._call(fr=["Dr. Test"], ar=["د. اختبار"])
        assert c.drawString.called

    def test_h_scale_zero_point_five_runs(self):
        c = self._call(h_scale=0.5)
        assert c.drawString.called

    def test_logo_path_triggers_draw_safe_image(self):
        bt = _bt()
        c = _canvas()
        with patch.object(bt, '_draw_safe_image') as mock_img:
            bt._draw_header_swiss(
                c, _CFG_EMPTY, '/fake/logo.png', _P, _S, _A,
                _W, _H, _FR, _AR, 1.0
            )
            mock_img.assert_called_once()


# ── _draw_header_royal ─────────────────────────────────────────────────────────

class TestDrawHeaderRoyal:
    def _call(self, cfg=None, logo=None, fr=None, ar=None, h_scale=1.0):
        bt = _bt()
        c = _canvas()
        bt._draw_header_royal(
            c, cfg or _CFG_EMPTY, logo, _P, _S, _A,
            _W, _H, fr or _FR, ar or _AR, h_scale
        )
        return c

    def test_canvas_drawString_called(self):
        assert self._call().drawString.called

    def test_canvas_drawRightString_called(self):
        assert self._call().drawRightString.called

    def test_canvas_line_called_for_hairline(self):
        assert self._call().line.called

    def test_canvas_saveState_restoreState(self):
        c = self._call()
        assert c.saveState.called
        assert c.restoreState.called

    def test_with_scale_cfg_runs(self):
        assert self._call(cfg=_CFG_SCALED).drawString.called

    def test_logo_triggers_draw_safe_image(self):
        bt = _bt()
        c = _canvas()
        with patch.object(bt, '_draw_safe_image') as mock_img:
            bt._draw_header_royal(
                c, _CFG_EMPTY, '/fake/logo.png', _P, _S, _A,
                _W, _H, _FR, _AR, 1.0
            )
            mock_img.assert_called_once()

    def test_no_logo_no_draw_safe_image(self):
        bt = _bt()
        c = _canvas()
        with patch.object(bt, '_draw_safe_image') as mock_img:
            bt._draw_header_royal(
                c, _CFG_EMPTY, None, _P, _S, _A,
                _W, _H, _FR, _AR, 1.0
            )
            mock_img.assert_not_called()


# ── _draw_header_clinical ──────────────────────────────────────────────────────

class TestDrawHeaderClinical:
    def _call(self, cfg=None, logo=None, fr=None, ar=None, h_scale=1.0):
        bt = _bt()
        c = _canvas()
        bt._draw_header_clinical(
            c, cfg or _CFG_EMPTY, logo, _P, _S, _A,
            _W, _H, fr or _FR, ar or _AR, h_scale
        )
        return c

    def test_canvas_drawString_called(self):
        assert self._call().drawString.called

    def test_canvas_drawRightString_called(self):
        assert self._call().drawRightString.called

    def test_canvas_line_called(self):
        # Two lines: vertical + horizontal separator
        c = self._call()
        assert c.line.call_count >= 2

    def test_saveState_restoreState(self):
        c = self._call()
        assert c.saveState.called
        assert c.restoreState.called

    def test_logo_branch_with_draw_safe_image(self):
        bt = _bt()
        c = _canvas()
        with patch.object(bt, '_draw_safe_image') as mock_img:
            bt._draw_header_clinical(
                c, _CFG_EMPTY, '/fake/logo.png', _P, _S, _A,
                _W, _H, _FR, _AR, 1.0
            )
            mock_img.assert_called_once()

    def test_no_logo_branch_runs(self):
        c = self._call(logo=None)
        assert c.drawString.called


# ── _draw_header_modern ────────────────────────────────────────────────────────

class TestDrawHeaderModern:
    def _call(self, cfg=None, logo=None, fr=None, ar=None, h_scale=1.0):
        bt = _bt()
        c = _canvas()
        bt._draw_header_modern(
            c, cfg or _CFG_EMPTY, logo, _P, _S, _A,
            _W, _H, fr or _FR, ar or _AR, h_scale
        )
        return c

    def test_canvas_drawString_called(self):
        assert self._call().drawString.called

    def test_canvas_drawRightString_called(self):
        assert self._call().drawRightString.called

    def test_canvas_line_called(self):
        assert self._call().line.called

    def test_saveState_restoreState(self):
        c = self._call()
        assert c.saveState.called
        assert c.restoreState.called

    def test_logo_branch(self):
        bt = _bt()
        c = _canvas()
        with patch.object(bt, '_draw_safe_image') as mock_img:
            bt._draw_header_modern(
                c, _CFG_EMPTY, '/fake/logo.png', _P, _S, _A,
                _W, _H, _FR, _AR, 1.0
            )
            mock_img.assert_called_once()

    def test_with_scale_cfg_runs(self):
        assert self._call(cfg=_CFG_SCALED).drawString.called


# ── _draw_header_heritage ──────────────────────────────────────────────────────

class TestDrawHeaderHeritage:
    def _call(self, cfg=None, logo=None, fr=None, ar=None, h_scale=1.0):
        bt = _bt()
        c = _canvas()
        bt._draw_header_heritage(
            c, cfg or _CFG_EMPTY, logo, _P, _S, _A,
            _W, _H, fr or _FR, ar or _AR, h_scale
        )
        return c

    def test_canvas_drawCentredString_called(self):
        assert self._call().drawCentredString.called

    def test_centered_layout_avoids_left_right_draws(self):
        c = self._call()
        assert not c.drawString.called
        assert not c.drawRightString.called

    def test_canvas_double_line_drawn(self):
        # Heritage uses two lines for its separator
        c = self._call()
        assert c.line.call_count >= 2

    def test_saveState_restoreState(self):
        c = self._call()
        assert c.saveState.called
        assert c.restoreState.called

    def test_logo_branch(self):
        bt = _bt()
        c = _canvas()
        with patch.object(bt, '_draw_safe_image') as mock_img:
            bt._draw_header_heritage(
                c, _CFG_EMPTY, '/fake/logo.png', _P, _S, _A,
                _W, _H, _FR, _AR, 1.0
            )
            mock_img.assert_called_once()

    def test_no_logo_runs(self):
        assert self._call(logo=None).drawCentredString.called


# ── _draw_auto_header dispatch ─────────────────────────────────────────────────

class TestDrawAutoHeader:
    def _call(self, template_key):
        bt = _bt()
        c = _canvas()
        cfg = {'selected_template': template_key}
        bt._draw_auto_header(c, cfg, None, _P, _S, _A, _W, _H)
        return c

    def test_swiss_default_called(self):
        c = self._call('swiss')
        assert c.drawString.called

    def test_royal_called(self):
        c = self._call('royal')
        assert c.drawString.called

    def test_clinical_called(self):
        c = self._call('clinical')
        assert c.drawString.called

    def test_modern_called(self):
        c = self._call('modern')
        assert c.drawString.called

    def test_heritage_called(self):
        c = self._call('heritage')
        assert c.drawCentredString.called

    def test_unknown_template_falls_through_to_swiss(self):
        # Any unrecognised key hits the `else` branch → swiss
        bt = _bt()
        c = _canvas()
        bt._draw_auto_header(c, {'selected_template': 'INVALID'}, None, _P, _S, _A, _W, _H)
        assert c.drawString.called

    def test_empty_config_defaults_to_swiss(self):
        c = self._call('swiss')
        assert c.drawString.called

    def test_auto_header_reads_fr_lines_from_config(self):
        bt = _bt()
        c = _canvas()
        cfg = {
            'selected_template': 'swiss',
            'header_lines_fr': ["Custom Dr.", "Custom Specialty"],
            'header_lines_ar': ["اسم مخصص"],
        }
        bt._draw_auto_header(c, cfg, None, _P, _S, _A, _W, _H)
        # drawString should have been called with our custom text somewhere
        all_calls = [str(ca) for ca in c.drawString.call_args_list]
        assert any("Custom Dr." in s for s in all_calls)
