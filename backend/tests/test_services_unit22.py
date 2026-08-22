"""Twenty-second batch — BaseTemplate.draw_static_elements branches."""
import os
import tempfile
from unittest.mock import MagicMock, patch
from reportlab.lib.units import cm


# ── shared helpers ─────────────────────────────────────────────────────────────

def _bt():
    from backend.services.base_template import BaseTemplate
    return BaseTemplate()


def _canvas():
    return MagicMock()


def _doc(width=148 * cm, height=210 * cm):
    doc = MagicMock()
    doc.pagesize = (width, height)
    return doc


# ── draw_static_elements ───────────────────────────────────────────────────────

class TestDrawStaticElements:
    def _call(self, config=None, draw_legal_ids=False, user=None):
        bt = _bt()
        c = _canvas()
        bt.draw_static_elements(c, _doc(), config=config or {}, draw_legal_ids=draw_legal_ids, user=user)
        return c

    def test_canvas_saveState_called(self):
        assert self._call().saveState.called

    def test_canvas_restoreState_called(self):
        assert self._call().restoreState.called

    def test_empty_config_runs_full_path(self):
        c = self._call()
        assert c.drawString.called

    def test_sidebar_template_draws_rect_and_line(self):
        cfg = {'selected_template': 'sidebar'}
        c = self._call(cfg)
        assert c.rect.called
        assert c.line.called

    def test_watermark_enabled_no_logo_skips_watermark(self):
        cfg = {'watermark_enabled': True}
        c = self._call(cfg)
        assert c.drawString.called

    def test_watermark_enabled_with_existing_logo(self):
        import io
        from PIL import Image as PILImage
        buf = io.BytesIO()
        PILImage.new('RGB', (10, 10), color=(0, 0, 255)).save(buf, format='PNG')
        buf.seek(0)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(buf.getvalue())
            logo_path = tmp.name

        try:
            cfg = {
                'watermark_enabled': True,
                'watermark_opacity': 0.08,
                'logo_path': os.path.basename(logo_path),
            }
            bt = _bt()
            bt.base_path = os.path.dirname(os.path.dirname(logo_path))
            bt.default_logo_path = logo_path

            c = _canvas()
            with patch.object(bt, '_draw_safe_image'):
                bt.draw_static_elements(c, _doc(), config=cfg)
            assert c.saveState.called
        finally:
            os.unlink(logo_path)

    def test_letterhead_path_nonexistent_falls_through(self):
        cfg = {
            'use_letterhead': True,
            'letterhead_path': 'nonexistent_letterhead.png',
        }
        c = self._call(cfg)
        assert c.drawString.called

    def test_swiss_template_draws_header(self):
        cfg = {'selected_template': 'swiss'}
        c = self._call(cfg)
        assert c.drawString.called

    def test_royal_template_draws_header(self):
        cfg = {'selected_template': 'royal'}
        c = self._call(cfg)
        assert c.drawString.called

    def test_modern_template_draws_header(self):
        cfg = {'selected_template': 'modern'}
        c = self._call(cfg)
        assert c.drawString.called

    def test_heritage_template_draws_header(self):
        cfg = {'selected_template': 'heritage'}
        c = self._call(cfg)
        assert c.drawCentredString.called

    def test_draw_legal_ids_true(self):
        cfg = {'ice': '001234567890123', 'footer_address': 'Rabat'}
        c = self._call(cfg, draw_legal_ids=True)
        assert c.drawCentredString.called

    def test_with_user_object(self):
        user = MagicMock()
        user.adresse_complete = "Casablanca"
        user.telephone_mobile = "0612345678"
        user.identifiants_legaux = {}
        c = self._call({}, user=user)
        assert c.drawString.called

    def test_letterhead_enabled_with_existing_file(self):
        import io
        from PIL import Image as PILImage
        buf = io.BytesIO()
        PILImage.new('RGB', (10, 10)).save(buf, format='PNG')
        buf.seek(0)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(buf.getvalue())
            lh_path = tmp.name

        try:
            lh_name = os.path.basename(lh_path)
            cfg = {
                'use_letterhead': True,
                'letterhead_path': lh_name,
            }
            bt = _bt()
            uploads_dir = os.path.join(bt.base_path, "static", "uploads")
            expected_lh = os.path.join(uploads_dir, lh_name)

            c = _canvas()
            original_exists = os.path.exists
            def mock_exists(path):
                if path == expected_lh:
                    return True
                return original_exists(path)

            with patch('os.path.exists', side_effect=mock_exists), \
                 patch.object(bt, '_draw_safe_image'):
                bt.draw_static_elements(c, _doc(), config=cfg)
            assert c.saveState.called
        finally:
            os.unlink(lh_path)
