"""Sixth batch — qr_service pure helpers, notification_service pure methods,
cephalo_measure_registry, habits_engine.get_recommended_duration,
document_factory._calculate_age, css_generator."""
from datetime import datetime, date


# ── qr_service pure helpers ───────────────────────────────────────────────────

class TestQrServiceGenerateVcard:
    def _fn(self, name, phone, email, address=""):
        from backend.services.qr_service import QRService
        return QRService.generate_vcard(name, phone, email, address)

    def test_contains_begin_vcard(self):
        assert "BEGIN:VCARD" in self._fn("Dr. Dupont", "0661000000", "dr@cabinet.ma")

    def test_contains_end_vcard(self):
        assert "END:VCARD" in self._fn("Dr. Dupont", "0661000000", "dr@cabinet.ma")

    def test_contains_name(self):
        assert "FN:Dr. Dupont" in self._fn("Dr. Dupont", "0661000000", "dr@cabinet.ma")

    def test_contains_phone(self):
        assert "TEL;TYPE=CELL:0661000000" in self._fn("Dr. Dupont", "0661000000", "dr@cabinet.ma")

    def test_contains_email(self):
        assert "EMAIL:dr@cabinet.ma" in self._fn("Dr. Dupont", "0661000000", "dr@cabinet.ma")

    def test_address_included_when_given(self):
        result = self._fn("Dr. X", "0600000000", "x@x.ma", "123 Rue Casablanca")
        assert "123 Rue Casablanca" in result

    def test_address_omitted_when_empty(self):
        result = self._fn("Dr. X", "0600000000", "x@x.ma", "")
        assert "ADR" not in result

    def test_version_is_3(self):
        assert "VERSION:3.0" in self._fn("A", "B", "C")

    def test_returns_string(self):
        assert isinstance(self._fn("A", "B", "C"), str)


class TestQrServiceWhatsappUrl:
    def _fn(self, phone, message=""):
        from backend.services.qr_service import QRService
        return QRService.generate_whatsapp_url(phone, message)

    def test_empty_phone_returns_empty(self):
        assert self._fn("") == ""

    def test_moroccan_local_number_converted(self):
        url = self._fn("0661234567")
        assert "212661234567" in url

    def test_contains_wa_me(self):
        assert "wa.me" in self._fn("0661234567")

    def test_message_encoded_in_url(self):
        url = self._fn("0661234567", "Bonjour")
        assert "text=" in url
        assert "Bonjour" in url or "Bonjour" in url

    def test_no_message_no_query_string(self):
        url = self._fn("0661234567")
        assert "?" not in url

    def test_double_zero_prefix_stripped(self):
        url = self._fn("00212661234567")
        assert "00212" not in url

    def test_returns_string(self):
        assert isinstance(self._fn("0661234567"), str)


class TestQrServiceMapsUrl:
    def _fn(self, address):
        from backend.services.qr_service import QRService
        return QRService.generate_maps_url(address)

    def test_contains_maps_base(self):
        assert "google.com/maps" in self._fn("Casablanca, Maroc")

    def test_address_encoded(self):
        url = self._fn("12 Rue de la Paix")
        assert "12" in url

    def test_returns_string(self):
        assert isinstance(self._fn("Test"), str)


# ── notification_service pure methods ─────────────────────────────────────────

class TestNotificationServiceFormatReminder:
    def _svc(self):
        from backend.services.notification_service import NotificationService
        return NotificationService()

    def test_message_contains_patient_name(self):
        svc = self._svc()
        msg = svc._format_reminder_message("Ahmed HASSAN", datetime(2025, 3, 15, 10, 30), "Dr. Samir")
        assert "Ahmed HASSAN" in msg

    def test_message_contains_doctor_name(self):
        svc = self._svc()
        msg = svc._format_reminder_message("Patient", datetime(2025, 3, 15, 10, 30), "Dr. Samir")
        assert "Dr. Samir" in msg

    def test_message_contains_formatted_date(self):
        svc = self._svc()
        msg = svc._format_reminder_message("Patient", datetime(2025, 3, 15, 10, 30), "Dr. X")
        assert "15/03/2025" in msg

    def test_message_contains_time(self):
        svc = self._svc()
        msg = svc._format_reminder_message("Patient", datetime(2025, 3, 15, 10, 30), "Dr. X")
        assert "10:30" in msg

    def test_returns_string(self):
        svc = self._svc()
        result = svc._format_reminder_message("A", datetime(2025, 1, 1, 9, 0), "B")
        assert isinstance(result, str)
        assert len(result) > 20


class TestNotificationServiceSendSms:
    def _svc(self):
        from backend.services.notification_service import NotificationService
        return NotificationService()

    def test_empty_number_returns_false(self):
        assert self._svc().send_sms_via_twilio("", "test message") is False

    def test_short_number_returns_false(self):
        assert self._svc().send_sms_via_twilio("123", "test message") is False

    def test_valid_number_returns_true(self):
        assert self._svc().send_sms_via_twilio("+212661234567", "Bonjour") is True

    def test_moroccan_number_returns_true(self):
        assert self._svc().send_sms_via_twilio("0661234567", "Bonjour") is True


# ── cephalo_measure_registry ───────────────────────────────────────────────────

class TestCephaloMeasureRegistry:
    def test_sna_is_not_mm(self):
        from backend.services.cephalo_measure_registry import is_mm_metric
        assert not is_mm_metric("SNA")

    def test_snb_is_not_mm(self):
        from backend.services.cephalo_measure_registry import is_mm_metric
        assert not is_mm_metric("SNB")

    def test_wits_is_mm(self):
        from backend.services.cephalo_measure_registry import is_mm_metric
        assert is_mm_metric("Wits")

    def test_surplomb_is_mm(self):
        from backend.services.cephalo_measure_registry import is_mm_metric
        assert is_mm_metric("Surplomb_Incisif")

    def test_recouvrement_is_mm(self):
        from backend.services.cephalo_measure_registry import is_mm_metric
        assert is_mm_metric("Recouvrement")

    def test_longueur_is_mm(self):
        from backend.services.cephalo_measure_registry import is_mm_metric
        assert is_mm_metric("Longueur_mandibulaire")

    def test_impa_is_degrees(self):
        from backend.services.cephalo_measure_registry import cephalo_unit
        assert cephalo_unit("IMPA") == "°"

    def test_wits_unit_is_mm(self):
        from backend.services.cephalo_measure_registry import cephalo_unit
        assert cephalo_unit("Wits") == "mm"

    def test_surplomb_unit_is_mm(self):
        from backend.services.cephalo_measure_registry import cephalo_unit
        assert cephalo_unit("Surplomb_Incisif") == "mm"

    def test_anb_unit_is_degrees(self):
        from backend.services.cephalo_measure_registry import cephalo_unit
        assert cephalo_unit("ANB") == "°"

    def test_mm_keywords_tuple_exists(self):
        from backend.services.cephalo_measure_registry import MM_KEYWORDS
        assert isinstance(MM_KEYWORDS, tuple)
        assert len(MM_KEYWORDS) > 0

    def test_case_insensitive(self):
        from backend.services.cephalo_measure_registry import is_mm_metric
        assert is_mm_metric("WITS")
        assert is_mm_metric("wits")


# ── habits_engine.get_recommended_duration ────────────────────────────────────

class TestGetRecommendedDuration:
    def _svc(self):
        from backend.services.habits_engine import HabitsEngine
        return HabitsEngine()

    def test_canalaire_returns_45(self):
        assert self._svc().get_recommended_duration("Traitement Canalaire") == 45

    def test_canalaire_molaire_returns_60(self):
        assert self._svc().get_recommended_duration("Traitement Canalaire Molaire") == 60

    def test_implant_returns_90(self):
        assert self._svc().get_recommended_duration("Pose Implant") == 90

    def test_extraction_simple_returns_30(self):
        assert self._svc().get_recommended_duration("Extraction dentaire") == 30

    def test_extraction_sagesse_returns_45(self):
        assert self._svc().get_recommended_duration("Extraction Dent de Sagesse") == 45

    def test_couronne_returns_45(self):
        assert self._svc().get_recommended_duration("Couronne céramique") == 45

    def test_composite_returns_30(self):
        assert self._svc().get_recommended_duration("Composite postérieur") == 30

    def test_detartrage_returns_30(self):
        assert self._svc().get_recommended_duration("Détartrage complet") == 30

    def test_consultation_returns_15(self):
        assert self._svc().get_recommended_duration("Consultation initiale") == 15

    def test_bilan_returns_15(self):
        assert self._svc().get_recommended_duration("Bilan radiologique") == 15

    def test_unknown_returns_30(self):
        assert self._svc().get_recommended_duration("Acte inconnu") == 30

    def test_chirurgie_returns_60(self):
        assert self._svc().get_recommended_duration("Chirurgie parodontale") == 60


# ── document_factory._calculate_age ──────────────────────────────────────────

class TestDocumentFactoryCalculateAge:
    def _svc(self):
        from backend.services.document_factory import DocumentFactory
        return DocumentFactory.__new__(DocumentFactory)

    def test_born_none_returns_zero(self):
        assert self._svc()._calculate_age(None) == 0

    def test_returns_int(self):
        born = datetime(1990, 1, 1)
        result = self._svc()._calculate_age(born)
        assert isinstance(result, int)

    def test_age_is_positive(self):
        born = datetime(1985, 6, 15)
        assert self._svc()._calculate_age(born) > 0

    def test_datetime_input(self):
        born = datetime(1990, 1, 1)
        age = self._svc()._calculate_age(born)
        today = date.today()
        expected_age = today.year - 1990 - ((today.month, today.day) < (1, 1))
        assert age == expected_age

    def test_date_input(self):
        born = date(2000, 7, 4)
        age = self._svc()._calculate_age(born)
        assert age >= 24


# ── css_generator ─────────────────────────────────────────────────────────────

class TestCSSGenerator:
    def _gen(self):
        from backend.services.css_generator import CSSGenerator
        return CSSGenerator()

    def test_generate_document_css_returns_string(self):
        css = self._gen().generate_document_css()
        assert isinstance(css, str)
        assert len(css) > 100

    def test_css_contains_root_variables(self):
        css = self._gen().generate_document_css()
        assert ":root" in css

    def test_css_contains_page_rule(self):
        css = self._gen().generate_document_css()
        assert "@page" in css

    def test_css_contains_primary_color(self):
        from backend.services.css_generator import CSSGenerator, ColorConfig
        gen = CSSGenerator(colors=ColorConfig(primary="#FF0000"))
        css = gen.generate_document_css()
        assert "#FF0000" in css or "#ff0000" in css.lower()

    def test_custom_margins_applied(self):
        from backend.services.css_generator import CSSGenerator, MarginConfig
        gen = CSSGenerator(margins=MarginConfig(top=5.0))
        css = gen.generate_document_css()
        assert "5.0cm" in css

    def test_a4_page_size_in_output(self):
        css = self._gen().generate_document_css(page_size="A4")
        assert "A4" in css

    def test_margin_config_defaults(self):
        from backend.services.css_generator import MarginConfig
        mc = MarginConfig()
        assert mc.top == 3.0
        assert mc.left == 1.5

    def test_color_config_defaults(self):
        from backend.services.css_generator import ColorConfig
        cc = ColorConfig()
        assert cc.primary == "#003380"

    def test_header_footer_config_defaults(self):
        from backend.services.css_generator import HeaderFooterConfig
        hf = HeaderFooterConfig()
        assert hf.auto_generate is True
        assert hf.letterhead_enabled is False
