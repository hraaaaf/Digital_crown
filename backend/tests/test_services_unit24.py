"""Twenty-fourth batch — BaseTemplate remaining: PinnedCloture, _draw_safe_image,
PageCounter, and SyncManager pure logic."""
import os
import io
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from reportlab.lib.units import cm


# ── PinnedCloture ──────────────────────────────────────────────────────────────

class TestPinnedCloture:
    def _make(self, text="Test text", style=None):
        from backend.services.base_template import PinnedCloture
        from reportlab.lib.styles import getSampleStyleSheet
        s = style or getSampleStyleSheet()['Normal']
        return PinnedCloture(text, s)

    def test_init_stores_text(self):
        pc = self._make("Hello")
        assert pc.text == "Hello"

    def test_init_stores_style(self):
        from reportlab.lib.styles import getSampleStyleSheet
        s = getSampleStyleSheet()['Normal']
        pc = self._make("Hello", style=s)
        assert pc.style is s

    def test_wrap_returns_tuple(self):
        pc = self._make("Hello")
        result = pc.wrap(100, 200)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_wrap_height_is_minimal(self):
        pc = self._make("Hello")
        _, h = pc.wrap(200, 500)
        assert h > 0
        assert h < 1.0 * cm  # Should be very small (0.2cm)

    def test_strip_tags_removes_bold(self):
        from backend.services.base_template import PinnedCloture
        result = PinnedCloture._strip_tags("<b>Dr. Ahmed</b>")
        assert result == "Dr. Ahmed"

    def test_strip_tags_removes_italic(self):
        from backend.services.base_template import PinnedCloture
        result = PinnedCloture._strip_tags("<i>Chirurgien Dentiste</i>")
        assert result == "Chirurgien Dentiste"

    def test_strip_tags_preserves_text(self):
        from backend.services.base_template import PinnedCloture
        result = PinnedCloture._strip_tags("No tags here")
        assert result == "No tags here"

    def test_strip_tags_empty_string(self):
        from backend.services.base_template import PinnedCloture
        assert PinnedCloture._strip_tags("") == ""

    def test_drawOn_empty_text_returns_early(self):
        """drawOn with empty text should not call canvas methods."""
        from backend.services.base_template import PinnedCloture
        from reportlab.lib.styles import getSampleStyleSheet
        pc = PinnedCloture("", getSampleStyleSheet()['Normal'])
        c = MagicMock()
        pc.drawOn(c, 0, 0)
        c.saveState.assert_not_called()

    def test_drawOn_with_text_calls_saveState(self):
        """drawOn with real text should call saveState/restoreState."""
        pc = self._make("Ce certificat est délivré")
        c = MagicMock()
        # Paragraph.wrap and drawOn need a real canvas; patch those inner calls
        with patch('reportlab.platypus.Paragraph.wrap', return_value=(100, 10)), \
             patch('reportlab.platypus.Paragraph.drawOn'):
            pc.drawOn(c, 0, 0)
        assert c.saveState.called
        assert c.restoreState.called


# ── _draw_safe_image ───────────────────────────────────────────────────────────

class TestDrawSafeImage:
    def _bt(self):
        from backend.services.base_template import BaseTemplate
        return BaseTemplate()

    def test_png_image_drawn(self):
        import io
        from PIL import Image as PILImage
        buf = io.BytesIO()
        PILImage.new('RGBA', (20, 20)).save(buf, format='PNG')
        buf.seek(0)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(buf.getvalue())
            png_path = tmp.name

        try:
            bt = self._bt()
            c = MagicMock()
            bt._draw_safe_image(c, png_path, 0, 0, 2*cm, 2*cm)
            assert c.drawImage.called
        finally:
            os.unlink(png_path)

    def test_nonexistent_image_does_not_crash(self):
        bt = self._bt()
        c = MagicMock()
        bt._draw_safe_image(c, '/nonexistent/path/to/image.png', 0, 0, 2*cm, 2*cm)
        # Should not raise, error is logged and swallowed

    def test_svg_non_parseable_falls_to_png_path(self):
        # Create a fake SVG with no images embedded
        svg_content = b"""<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <rect width="100" height="100" fill="blue"/>
</svg>"""
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as tmp:
            tmp.write(svg_content)
            svg_path = tmp.name

        try:
            bt = self._bt()
            c = MagicMock()
            # _draw_safe_image catches all internal exceptions — should not raise
            bt._draw_safe_image(c, svg_path, 0, 0, 2*cm, 2*cm)
        finally:
            os.unlink(svg_path)

    def test_svg_with_embedded_png(self):
        # Create SVG with a base64 embedded PNG
        import base64
        from PIL import Image as PILImage
        buf = io.BytesIO()
        PILImage.new('RGBA', (10, 10)).save(buf, format='PNG')
        png_b64 = base64.b64encode(buf.getvalue()).decode()

        svg_content = f"""<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="100" height="100">
  <image xlink:href="data:image/png;base64,{png_b64}" width="100" height="100"/>
</svg>""".encode()

        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as tmp:
            tmp.write(svg_content)
            svg_path = tmp.name

        try:
            bt = self._bt()
            c = MagicMock()
            bt._draw_safe_image(c, svg_path, 0, 0, 2*cm, 2*cm)
            # Should have called drawImage for the extracted PNG
            assert c.drawImage.called
        finally:
            os.unlink(svg_path)


# ── PageCounter ────────────────────────────────────────────────────────────────

class TestPageCounter:
    def test_initial_count_zero(self):
        from backend.services.base_template import PageCounter
        pc = PageCounter()
        assert pc.page_count == 0

    def test_make_canvas_class_returns_class(self):
        from backend.services.base_template import PageCounter
        pc = PageCounter()
        cls = pc.make_canvas_class()
        assert cls is not None
        assert isinstance(cls, type)

    def test_make_canvas_class_subclasses_canvas(self):
        from backend.services.base_template import PageCounter
        from reportlab.pdfgen.canvas import Canvas
        pc = PageCounter()
        cls = pc.make_canvas_class()
        assert issubclass(cls, Canvas)

    def test_counting_canvas_increments_on_show_page(self):
        from backend.services.base_template import PageCounter
        pc = PageCounter()
        CountingCanvas = pc.make_canvas_class()

        import io
        buf = io.BytesIO()
        canvas = CountingCanvas(buf)
        canvas.drawString(10, 10, "Page 1")
        canvas.showPage()
        canvas.drawString(10, 10, "Page 2")
        canvas.showPage()
        canvas.save()

        assert pc.page_count == 2


# ── SyncManager pure logic ─────────────────────────────────────────────────────

class TestSyncManagerPure:
    def _svc(self):
        from backend.services.sync_manager import SyncManager
        return SyncManager(debounce_seconds=0.01)  # fast debounce for tests

    def test_init_sets_debounce(self):
        from backend.services.sync_manager import SyncManager
        sm = SyncManager(debounce_seconds=5.0)
        assert sm.debounce_seconds == 5.0

    def test_init_empty_pending_set(self):
        sm = self._svc()
        assert len(sm._pending_employers) == 0

    def test_on_change_schedules_sync_when_employer_id_present(self):
        sm = self._svc()
        target = MagicMock()
        target.employer_id = 42

        with patch.object(sm, '_schedule_sync') as mock_schedule:
            sm._on_change(None, None, target)
            mock_schedule.assert_called_once_with(42)

    def test_on_change_uses_praticien_id_when_no_employer_id(self):
        sm = self._svc()
        target = MagicMock()
        target.employer_id = None
        target.praticien_id = 99

        with patch.object(sm, '_schedule_sync') as mock_schedule:
            sm._on_change(None, None, target)
            mock_schedule.assert_called_once_with(99)

    def test_on_change_no_id_does_not_schedule(self):
        sm = self._svc()
        target = MagicMock()
        target.employer_id = None
        # No praticien_id attribute
        del target.praticien_id

        with patch.object(sm, '_schedule_sync') as mock_schedule:
            sm._on_change(None, None, target)
            mock_schedule.assert_not_called()

    def test_perform_bulk_sync_no_pending_returns_early(self):
        sm = self._svc()
        sm._pending_employers.clear()
        with patch.object(sm, '_sync_single_cabinet') as mock_sync:
            sm._perform_bulk_sync()
            mock_sync.assert_not_called()

    def test_schedule_sync_adds_employer_to_pending(self):
        import threading
        sm = self._svc()
        # Replace timer with a mock so it doesn't actually run
        with patch('threading.Timer') as mock_timer:
            mock_timer.return_value = MagicMock()
            mock_timer.return_value.start = MagicMock()
            sm._schedule_sync(55)
            assert 55 in sm._pending_employers
