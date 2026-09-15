from pathlib import Path


def test_pyinstaller_spec_embeds_both_medication_catalog_sources():
    root = Path(__file__).resolve().parents[2]
    spec = (root / "DigitalCrown.spec").read_text(encoding="utf-8")

    required = (
        "backend/data/medications_ma.json",
        "backend/data/medications_ma_ammps_2026.json",
    )
    for relative_path in required:
        assert (root / relative_path).is_file(), f"Missing medication catalog source: {relative_path}"
        assert f"('{relative_path}', 'backend/data')" in spec, (
            f"DigitalCrown.spec does not package {relative_path} into backend/data"
        )
