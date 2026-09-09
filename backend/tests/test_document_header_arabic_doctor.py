from backend.services.document_header_profile import _normalize_doctor_ar, resolve_header_lines


def test_arabic_doctor_title_is_prefixed_for_new_name():
    assert _normalize_doctor_ar("بنموسى أشرف") == "د. بنموسى أشرف"


def test_arabic_doctor_title_normalizes_legacy_suffix():
    assert _normalize_doctor_ar("بنموسى أشرف .د") == "د. بنموسى أشرف"


def test_automatic_header_normalizes_stored_legacy_doctor_line():
    config = {
        "header_lines_ar": ["بنموسى أشرف .د", "طبيب جراح للأسنان"],
        "header_lines_fr": ["Dr. Benmoussa Achraf", "Chirurgien Dentiste"],
        "specialty_ids": ["soins"],
        "header_customized": False,
    }
    lines = resolve_header_lines(config, "header_lines_ar")
    assert lines[0] == "د. بنموسى أشرف"
