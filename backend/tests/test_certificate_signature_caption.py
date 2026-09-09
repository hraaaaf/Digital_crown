from backend.services.generators.certificat_gen import CertificateSignatureSpace


def test_certificate_signature_caption_keeps_only_practitioner_name():
    signature = CertificateSignatureSpace(
        font_name="Helvetica",
        signer_name="Salma Test ADMIN",
    )

    assert signature._signature_caption() == "Dr Salma Test ADMIN"
    assert "Signature manuscrite" not in signature._signature_caption()


def test_certificate_signature_caption_is_empty_without_practitioner_name():
    signature = CertificateSignatureSpace(font_name="Helvetica")

    assert signature._signature_caption() == ""
