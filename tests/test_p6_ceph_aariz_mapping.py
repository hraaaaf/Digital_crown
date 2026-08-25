from __future__ import annotations

import pytest

from scripts.p6_ceph_aariz_mapping import (
    AARIZ_OFFICIAL_TITLES,
    AARIZ_TITLE_TO_DC,
    DC_DIRECT_CANONICAL_POINTS,
    DC_UNSUPPORTED_OCCLUSAL_POINTS,
    adapt_aariz29_to_digital_crown,
)


def _coordinate_book():
    return {
        title: (float(index + 1), float(100 + index))
        for index, title in enumerate(AARIZ_OFFICIAL_TITLES)
    }


def test_direct_contract_is_exactly_20_and_never_synthesizes_wits_points():
    assert len(AARIZ_TITLE_TO_DC) == 20
    assert len(DC_DIRECT_CANONICAL_POINTS) == 20
    assert DC_UNSUPPORTED_OCCLUSAL_POINTS == {"Occ_Ant", "Occ_Post"}
    assert not (DC_DIRECT_CANONICAL_POINTS & DC_UNSUPPORTED_OCCLUSAL_POINTS)


def test_mapping_is_title_based_and_order_independent():
    book = _coordinate_book()
    # Reverse the official repository order on purpose. A position-based adapter
    # would now be wrong; a title-based adapter must remain exact.
    titles = tuple(reversed(AARIZ_OFFICIAL_TITLES))
    coords = tuple(book[title] for title in titles)

    mapped = adapt_aariz29_to_digital_crown(titles, coords)

    for source_title, dc_name in AARIZ_TITLE_TO_DC.items():
        assert mapped[dc_name] == book[source_title]

    assert mapped["Prn"] == book["Pronasale"]
    assert mapped["Pog_soft"] == book["Soft Tissue Pogonion"]
    assert mapped["Sn"] == book["Subnasale"]


def test_mapping_fails_closed_on_ontology_change():
    book = _coordinate_book()
    titles = list(AARIZ_OFFICIAL_TITLES)
    titles[-1] = "Unknown Landmark"
    coords = [book.get(title, (0.0, 0.0)) for title in titles]

    with pytest.raises(ValueError, match="ontology mismatch"):
        adapt_aariz29_to_digital_crown(titles, coords)


def test_mapping_fails_closed_on_duplicate_titles():
    book = _coordinate_book()
    titles = list(AARIZ_OFFICIAL_TITLES)
    titles[-1] = titles[0]
    coords = [book.get(title, (0.0, 0.0)) for title in titles]

    with pytest.raises(ValueError, match="must be unique"):
        adapt_aariz29_to_digital_crown(titles, coords)
