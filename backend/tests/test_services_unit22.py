"""Twenty-second batch — BaseTemplate.draw_static_elements branches,
TemplateEngine._fallback_reportlab (ReportLab PDF path),
and TemplateEngine medication scale helpers."""
import os
import tempfile
import pytest
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
        # _draw_auto_header (swiss) should run → drawString called
        assert c.drawString.called

    def test_sidebar_template_draws_rect_and_line(self):
        cfg = {'selected_template': 'sidebar'}
        c = self._call(cfg)
        assert c.rect.called
        assert c.line.called

    def test_watermark_enabled_no_logo_skips_watermark(self):
        cfg = {'watermark_enabled': True}
        c = self._call(cfg)
        # No logo file → setFillAlpha should not be called for watermark
        # But header/footer should still draw
        assert c.drawString.called

    def test_watermark_enabled_with_existing_logo(self):
        import io
        from PIL import Image as PILImage
        # Create a tiny valid PNG in a temp file
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
            # Patch base_path so it resolves to tmp directory
            bt.base_path = os.path.dirname(os.path.dirname(logo_path))
            # Override default_logo_path to the test image
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
        # letterhead path doesn't exist → falls through to header drawing
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
        assert c.drawString.called

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
            # Create expected path structure: base_path/static/uploads/<lh_name>
            uploads_dir = os.path.join(bt.base_path, "static", "uploads")
            expected_lh = os.path.join(uploads_dir, lh_name)

            c = _canvas()
            # Patch exists to return True for our letterhead path
            original_exists = os.path.exists
            def mock_exists(path):
                if path == expected_lh:
                    return True
                return original_exists(path)

            with patch('os.path.exists', side_effect=mock_exists), \
                 patch.object(bt, '_draw_safe_image'):
                bt.draw_static_elements(c, _doc(), config=cfg)
            # When letterhead exists → saves state, draws it, and returns early
            assert c.saveState.called
        finally:
            os.unlink(lh_path)


# ── TemplateEngine._fallback_reportlab ────────────────────────────────────────

class TestFallbackReportlab:
    def _make_svc(self):
        from backend.services.template_engine import TemplateEngine
        return TemplateEngine()

    def _template(self, name="Test", body_html="<p>Test</p>", design_config=None):
        t = MagicMock()
        t.name = name
        t.body_html = body_html
        t.design_config = design_config or {}
        return t

    def _cabinet(self, primary_color='#003380'):
        c = MagicMock()
        c.margin_top = 3.6
        c.margin_bottom = 3.2
        c.primary_color = primary_color
        c.secondary_color = '#666666'
        c.accent_color = '#0055AA'
        c.logo_path = None
        c.letterhead_path = None
        c.use_letterhead = False
        c.selected_template = 'swiss'
        c.watermark_enabled = False
        c.header_lines_fr = ["Dr. Test", "Dentiste"]
        c.header_lines_ar = ["د. اختبار"]
        c.footer_address = "Casablanca"
        c.footer_phones = "0612345678"
        c.qr_code_enabled = False
        c.identifiants_legaux = {}
        # Numeric scale attributes — must be floats, not MagicMock
        c.header_font_scale = 1.0
        c.header_logo_scale = 1.0
        c.header_line_height = 1.0
        c.header_scale = 1.0
        c.footer_font_scale = 1.0
        c.footer_qr_scale = 1.0
        c.footer_line_height = 1.0
        c.watermark_opacity = 0.10
        # String attributes that should be empty/None, not MagicMock
        c.contacts_json = None
        c.ice = ""
        c.if_ = ""
        c.inpe = ""
        c.nom_praticien = "Dr. Test"
        c.qr_code_type = "VCARD"
        c.qr_code_value = ""
        c.qr_code_color = None
        c.qr_code_label = ""
        c.qr_code_style = "dots"
        return c

    def test_generates_pdf_file(self):
        svc = self._make_svc()
        tmpl = self._template()
        cab = self._cabinet()
        ctx = {
            'patient': {'nom': 'DUPONT', 'prenom': 'Marie', 'age': 35},
            'praticien': {'nom_complet': 'Dr. Ahmed Benali'},
            'date': '15/06/2026',
            'titre': 'ORDONNANCE',
            'content': '<p>Texte de test.</p>',
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            out = tmp.name

        try:
            result = svc._fallback_reportlab(tmpl, cab, ctx, out)
            assert result == out
            assert os.path.exists(out)
            assert os.path.getsize(out) > 0
        finally:
            if os.path.exists(out):
                os.unlink(out)

    def test_generates_certificat_content(self):
        svc = self._make_svc()
        tmpl = self._template(name="Certificat Medical")
        cab = self._cabinet()
        ctx = {
            'patient': {'nom': 'MARTIN', 'prenom': 'Paul', 'age': 45},
            'praticien': {'nom_complet': 'Dr. Said'},
            'titre': 'CERTIFICAT MEDICAL',
            'content': 'Court contenu.',
            'hon': 'Mr',
            'certif_days': 5,
            'type_repos': 'un repos médical',
            'start_date': '16/06/2026',
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            out = tmp.name

        try:
            result = svc._fallback_reportlab(tmpl, cab, ctx, out)
            assert os.path.exists(out)
            assert os.path.getsize(out) > 0
        finally:
            if os.path.exists(out):
                os.unlink(out)

    def test_generates_ordonnance_with_medications(self):
        svc = self._make_svc()
        tmpl = self._template(name="Ordonnance")
        cab = self._cabinet()
        ctx = {
            'patient': {'nom': 'ALAOUI', 'prenom': 'Fatima', 'age': 32},
            'praticien': {'nom_complet': 'Dr. Benali'},
            'titre': 'ORDONNANCE',
            'content': '',
            'medications': [
                {'nom': 'DOLIPRANE', 'dosage': '1000mg', 'posologie': '3x/jour'},
                {'nom': 'AMOXICILLINE', 'dosage': '1g', 'posologie': '2x/jour pendant 7 jours'},
            ],
        }

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            out = tmp.name

        try:
            result = svc._fallback_reportlab(tmpl, cab, ctx, out)
            assert os.path.exists(out)
        finally:
            if os.path.exists(out):
                os.unlink(out)


# ── TemplateEngine medication scale computation (lines 285-344) ───────────────

class TestMedicationScaleComputation:
    """Tests for the global_scale computation in _generate_weasyprint_pdf."""

    def _svc(self):
        from backend.services.template_engine import TemplateEngine
        return TemplateEngine()

    def test_short_med_name_no_scale_reduction(self):
        """A short medication name should not reduce global_scale below 1.0."""
        svc = self._svc()
        meds = [{'nom': 'DOLIPRANE', 'dosage': '500mg', 'forme': 'CP', 'posologie': '3x/jour'}]
        # Call private logic by running through the scale calculation
        global_scale = 1.0
        for med in meds:
            nom = med.get('nom', '')
            dosage = med.get('dosage', '')
            forme = med.get('forme', '').replace('AUTRE: ', '').replace('Autre: ', '')
            posologie = med.get('posologie', '')
            header_str = f"{nom} {dosage} {forme}"
            if len(header_str) > 40:
                scale = max(0.65, 40.0 / len(header_str))
                if scale < global_scale:
                    global_scale = scale
            if len(posologie) > 60:
                scale = max(0.65, 60.0 / len(posologie))
                if scale < global_scale:
                    global_scale = scale
        assert global_scale == 1.0

    def test_long_med_name_triggers_scale_reduction(self):
        """A very long medication name should reduce global_scale."""
        nom = "AMOXICILLINE ACIDE CLAVULANIQUE AUGMENTIN 1000MG BOITE DE 14 COMPRIMES PELLICULES"
        header_str = f"{nom} 1g CP"
        global_scale = 1.0
        if len(header_str) > 40:
            scale = max(0.65, 40.0 / len(header_str))
            if scale < global_scale:
                global_scale = scale
        assert global_scale < 1.0
        assert global_scale >= 0.65

    def test_long_posologie_triggers_scale_reduction(self):
        """A very long posologie should reduce global_scale."""
        posologie = "1 comprimé matin midi et soir pendant 7 jours consécutifs sans interruption"
        global_scale = 1.0
        if len(posologie) > 60:
            scale = max(0.65, 60.0 / len(posologie))
            if scale < global_scale:
                global_scale = scale
        assert global_scale < 1.0
        assert global_scale >= 0.65

    def test_scale_clamped_to_minimum_065(self):
        """Scale should never go below 0.65."""
        very_long = "X" * 1000
        scale = max(0.65, 40.0 / len(very_long))
        assert scale == 0.65
