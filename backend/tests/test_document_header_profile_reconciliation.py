from backend.services.base_template import BaseTemplate
from backend.services.document_header_profile import resolve_header_lines


ALL_SPECIALTIES = [
    "soins",
    "endo",
    "paro",
    "ortho",
    "prothese",
    "chirurgie",
    "implant",
    "blanchiment",
    "esthetique",
]


def _legacy_config(**overrides):
    config = {
        "nom_praticien": "Benmoussa Achraf",
        "nom_praticien_ar": "بنموسى أشرف",
        "specialty_ids": ALL_SPECIALTIES,
        "custom_specialty_fr": "Pédodontie",
        "custom_specialty_ar": "طب أسنان الأطفال",
        "header_customized": False,
        # Exact shape of a stale pre-fix cabinet profile: only one pair persisted.
        "header_lines_fr": [
            "Dr. Benmoussa Achraf",
            "Chirurgien Dentiste",
            "Soins - Endodontie",
        ],
        "header_lines_ar": [
            "بنموسى أشرف .د",
            "طبيب جراح للأسنان",
            "علاج العصب - علاج",
        ],
    }
    config.update(overrides)
    return config


def test_runtime_rebuilds_full_automatic_header_from_specialty_ids():
    config = _legacy_config()

    assert resolve_header_lines(config, "header_lines_fr") == [
        "Dr. Benmoussa Achraf",
        "Chirurgien Dentiste",
        "Soins - Endodontie",
        "Parodontologie - Orthodontie",
        "Prothèse - Chirurgie",
        "Implantologie - Blanchiment",
        "Esthétique - Pédodontie",
    ]
    assert resolve_header_lines(config, "header_lines_ar") == [
        "بنموسى أشرف .د",
        "طبيب جراح للأسنان",
        "علاج العصب - علاج",
        "تقويم الأسنان - أمراض اللثة",
        "جراحة - تعويض الأسنان",
        "تبييض الأسنان - زراعة الأسنان",
        "طب أسنان الأطفال - تجميل الأسنان",
    ]


def test_base_template_uses_reconciled_lines_for_render_and_margin_reads():
    template = BaseTemplate()
    config = _legacy_config()

    assert len(template._get_val(config, "header_lines_fr")) == 7
    assert len(template._get_val(config, "header_lines_ar")) == 7


def test_customized_header_remains_authoritative():
    config = _legacy_config(
        header_customized=True,
        header_lines_fr=["Dr. Custom", "Ligne libre"],
        header_lines_ar=["د. مخصص", "سطر حر"],
    )

    assert resolve_header_lines(config, "header_lines_fr") == ["Dr. Custom", "Ligne libre"]
    assert resolve_header_lines(config, "header_lines_ar") == ["د. مخصص", "سطر حر"]


def test_legacy_profile_without_specialty_source_keeps_persisted_header():
    config = _legacy_config(
        specialty_ids=[],
        custom_specialty_fr="",
        custom_specialty_ar="",
    )

    assert resolve_header_lines(config, "header_lines_fr") == config["header_lines_fr"]
    assert resolve_header_lines(config, "header_lines_ar") == config["header_lines_ar"]


def test_unknown_specialty_ids_do_not_destroy_legacy_header():
    config = _legacy_config(
        specialty_ids=["legacy-unknown"],
        custom_specialty_fr="",
        custom_specialty_ar="",
    )

    assert resolve_header_lines(config, "header_lines_fr") == config["header_lines_fr"]
    assert resolve_header_lines(config, "header_lines_ar") == config["header_lines_ar"]
