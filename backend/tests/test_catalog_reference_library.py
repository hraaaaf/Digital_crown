from backend.services.catalog_reference_library import (
    REFERENCE_CATALOG,
    REFERENCE_CATALOG_VERSION,
    reference_catalog_counts,
)


def test_reference_catalog_is_broad_and_price_free():
    specialties, acts = reference_catalog_counts()
    assert REFERENCE_CATALOG_VERSION
    assert specialties >= 14
    assert acts >= 150
    assert all(
        float(act.get("base_price", 0)) == 0
        for specialty in REFERENCE_CATALOG
        for act in specialty["acts"]
    )


def test_reference_catalog_spans_core_dental_workflows():
    names = {
        act["name"]
        for specialty in REFERENCE_CATALOG
        for act in specialty["acts"]
    }
    expected = {
        "Consultation initiale",
        "Radiographie panoramique",
        "Composite 1 face",
        "Traitement canalaire molaire",
        "Surfaçage radiculaire par quadrant / secteur",
        "Extraction simple dent permanente",
        "Bridge définitif",
        "Prothèse partielle métallique / stellite",
        "Pose d'implant",
        "Pulpotomie dent temporaire",
        "Traitement orthodontique complet",
        "Dépose des points de suture",
    }
    assert expected <= names


def test_every_reference_act_has_unique_internal_code():
    codes = [
        act["code"]
        for specialty in REFERENCE_CATALOG
        for act in specialty["acts"]
    ]
    assert len(codes) == len(set(codes))
    assert all(code.startswith("DC-") for code in codes)
