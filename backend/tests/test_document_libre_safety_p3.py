from datetime import date
from types import SimpleNamespace

import fitz
import pytest

from backend.schemas.documents import LibreData
from backend.services.base_template import NAVY_BLUE
from backend.services.generators.libre_gen import (
    LibreGenerator,
    _config_owner_id,
    _normalize_and_validate_libre_data,
    _safe_filename_component,
    _sanitize_inline_markup,
)


def _libre(**kwargs):
    defaults = {
        "titre": "Lettre médicale",
        "contenu": "Contenu du praticien",
        "page_size": "A5",
        "alignment": "justify",
        "custom_patient": None,
        "custom_date": None,
        "hide_patient_header": False,
        "doc_date": date(2026, 8, 16),
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_api_defaults_do_not_create_a_document_without_explicit_title_and_content():
    data = LibreData()
    with pytest.raises(ValueError, match="titre.*explicitement"):
        _normalize_and_validate_libre_data(data)


def test_api_requires_explicit_content_even_when_title_is_sent():
    data = LibreData(title="Lettre")
    with pytest.raises(ValueError, match="contenu.*explicitement"):
        _normalize_and_validate_libre_data(data)


def test_blank_title_or_content_is_rejected():
    with pytest.raises(ValueError, match="titre.*requis"):
        _normalize_and_validate_libre_data(_libre(titre="   "))
    with pytest.raises(ValueError, match="contenu.*requis"):
        _normalize_and_validate_libre_data(_libre(contenu="\n  \t"))


@pytest.mark.parametrize("page_size", ["A3", "Letter", ""])
def test_unknown_page_size_is_rejected(page_size):
    with pytest.raises(ValueError, match="A4 ou A5"):
        _normalize_and_validate_libre_data(_libre(page_size=page_size))


@pytest.mark.parametrize("alignment", ["middle", "auto", "diagonal"])
def test_unknown_alignment_is_rejected(alignment):
    with pytest.raises(ValueError, match="alignement.*invalide"):
        _normalize_and_validate_libre_data(_libre(alignment=alignment))


def test_toolbar_markup_is_preserved_but_arbitrary_markup_is_escaped():
    rendered = _sanitize_inline_markup(
        '<b>Gras</b> <i>italique</i> <u>souligné</u> '
        '<font size="16">titre</font> <script>alert(1)</script> & texte'
    )
    assert '<b>Gras</b>' in rendered
    assert '<i>italique</i>' in rendered
    assert '<u>souligné</u>' in rendered
    assert '<font size="16">titre</font>' in rendered
    assert '<script>' not in rendered
    assert '&lt;script&gt;' in rendered
    assert '&amp; texte' in rendered


def test_unbalanced_supported_markup_is_made_well_formed():
    rendered = _sanitize_inline_markup('<b><i>Texte</b>')
    assert rendered == '<b><i>Texte&lt;/b&gt;</i></b>'


def test_filename_component_neutralizes_path_separators_and_controls():
    component = _safe_filename_component('EL/ALAMI\\Youssef\x00:*?')
    assert '/' not in component
    assert '\\' not in component
    assert '\x00' not in component
    assert ':' not in component
    assert '*' not in component
    assert '?' not in component


def test_age_uses_document_date_not_runtime_date(tmp_path):
    generator = LibreGenerator(str(tmp_path))
    born = date(2000, 8, 20)
    assert generator._calculate_age(born, date(2026, 8, 16)) == 25
    assert generator._calculate_age(born, date(2026, 8, 20)) == 26


def test_config_owner_uses_employer_for_sub_dentist():
    user = SimpleNamespace(id=91, employer_id=12, get_employer_id=lambda: 12)
    assert _config_owner_id(user, 91) == 12


def test_hide_patient_header_keeps_document_date_visible(tmp_path):
    generator = LibreGenerator(str(tmp_path))
    patient = SimpleNamespace(nom="EL ALAMI", prenom="Youssef", date_naissance=date(1990, 5, 12))
    data = _libre(hide_patient_header=True, doc_date=date(2026, 8, 16))
    header = generator._create_header(patient, data, NAVY_BLUE, 12 * 28.3465)
    right_paragraph = header._cellvalues[0][1]
    assert "16/08/2026" in right_paragraph.text


def test_long_document_stays_multipage_instead_of_being_compressed_to_one_page(tmp_path):
    generator = LibreGenerator(str(tmp_path))
    patient = SimpleNamespace(
        nom="EL ALAMI",
        prenom="Youssef",
        date_naissance=date(1990, 5, 12),
    )
    paragraph = "Texte clinique libre rédigé par le praticien. " * 30
    content = "\n\n".join(paragraph for _ in range(30))
    data = _libre(contenu=content, page_size="A5")

    path = generator.generate(patient, data)
    pdf = fitz.open(path)
    try:
        assert pdf.page_count > 1
        font_sizes = []
        for page in pdf:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if "Texte clinique libre" in span.get("text", ""):
                            font_sizes.append(span["size"])
        assert font_sizes
        assert min(font_sizes) >= 10.5
    finally:
        pdf.close()
