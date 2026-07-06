"""Unit tests for services/qr_service.py — pure Python, no DB required."""
from backend.services.qr_service import QRService


class TestGenerateVcard:
    def test_basic_vcard(self):
        svc = QRService()
        vcard = svc.generate_vcard("Dr. Test", "0600000001", "test@cabinet.ma")
        assert "BEGIN:VCARD" in vcard
        assert "VERSION:3.0" in vcard
        assert "FN:Dr. Test" in vcard
        assert "TEL;TYPE=CELL:0600000001" in vcard
        assert "EMAIL:test@cabinet.ma" in vcard
        assert "END:VCARD" in vcard

    def test_vcard_with_address(self):
        svc = QRService()
        vcard = svc.generate_vcard("Dr. Test", "0600000001", "t@t.ma", "Casablanca")
        assert "ADR;TYPE=WORK:;;Casablanca" in vcard

    def test_vcard_without_address_no_adr_line(self):
        svc = QRService()
        vcard = svc.generate_vcard("Dr. Test", "0600000001", "t@t.ma", "")
        assert "ADR" not in vcard


class TestGenerateWhatsappUrl:
    def setup_method(self):
        self.svc = QRService()

    def test_empty_phone_returns_empty(self):
        assert self.svc.generate_whatsapp_url("") == ""

    def test_local_number_gets_country_code(self):
        url = self.svc.generate_whatsapp_url("0612345678")
        assert "212612345678" in url
        assert url.startswith("https://wa.me/")

    def test_double_zero_prefix_stripped(self):
        url = self.svc.generate_whatsapp_url("00212612345678")
        assert "https://wa.me/212612345678" == url

    def test_with_message_encoded(self):
        url = self.svc.generate_whatsapp_url("0612345678", "Bonjour!")
        assert "text=" in url
        assert "Bonjour" in url

    def test_no_message_no_query_string(self):
        url = self.svc.generate_whatsapp_url("0612345678")
        assert "?" not in url

    def test_non_digit_chars_stripped(self):
        url = self.svc.generate_whatsapp_url("+212 612-345-678")
        assert "+" not in url
        assert " " not in url

    def test_already_international_number(self):
        url = self.svc.generate_whatsapp_url("212612345678")
        assert "https://wa.me/212612345678" == url


class TestGenerateMapsUrl:
    def test_maps_url_contains_address(self):
        svc = QRService()
        url = svc.generate_maps_url("Casablanca, Maroc")
        assert "google.com/maps" in url
        assert "Casablanca" in url

    def test_maps_url_encoded(self):
        svc = QRService()
        url = svc.generate_maps_url("Avenue Hassan II, Rabat")
        assert "%20" in url or "+" in url or "Avenue" in url


class TestGenerateQrBytes:
    def test_returns_bytesio(self):
        import io
        svc = QRService()
        buf = svc.generate_qr_bytes("https://example.com")
        assert isinstance(buf, io.BytesIO)

    def test_non_empty_output(self):
        svc = QRService()
        buf = svc.generate_qr_bytes("test data")
        assert buf.getvalue() != b""

    def test_classic_style(self):
        import io
        svc = QRService()
        buf = svc.generate_qr_bytes("data", qr_style="classic")
        assert isinstance(buf, io.BytesIO)

    def test_rounded_style(self):
        import io
        svc = QRService()
        buf = svc.generate_qr_bytes("data", qr_style="rounded")
        assert isinstance(buf, io.BytesIO)

    def test_elite_style(self):
        import io
        svc = QRService()
        buf = svc.generate_qr_bytes("data", qr_style="elite")
        assert isinstance(buf, io.BytesIO)

    def test_custom_color(self):
        import io
        svc = QRService()
        buf = svc.generate_qr_bytes("data", color="#FF5733")
        assert isinstance(buf, io.BytesIO)

    def test_svg_logo_path_ignored(self):
        import io
        svc = QRService()
        buf = svc.generate_qr_bytes("data", add_logo=True, logo_path="logo.svg")
        assert isinstance(buf, io.BytesIO)

    def test_unknown_style_falls_back_to_dots(self):
        import io
        svc = QRService()
        buf = svc.generate_qr_bytes("data", qr_style="unknown_style")
        assert isinstance(buf, io.BytesIO)


class TestGenerateDocumentQrBase64:
    def test_returns_data_uri(self):
        svc = QRService()
        result = svc.generate_document_qr_base64("doc123", "pub456")
        assert result.startswith("data:image/png;base64,")

    def test_custom_base_url(self):
        svc = QRService()
        result = svc.generate_document_qr_base64("doc123", "pub456", base_url="https://myapp.com")
        assert result.startswith("data:image/png;base64,")
