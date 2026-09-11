from pathlib import Path

from backend.models_media_core import ClinicalAsset


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "alembic" / "versions" / "c1a55e700001_add_clinical_assets.py"


def test_clinical_asset_migration_is_chained_from_current_head():
    text = MIGRATION.read_text(encoding="utf-8")
    assert 'revision: str = "c1a55e700001"' in text
    assert 'down_revision: Union[str, None] = "f7a8b9c0d1e2"' in text
    assert '"clinical_assets"' in text


def test_clinical_asset_table_has_tenant_patient_composite_index():
    indexes = {index.name: tuple(column.name for column in index.columns) for index in ClinicalAsset.__table__.indexes}
    assert indexes["ix_clinical_assets_tenant_patient_created"] == (
        "employer_id",
        "patient_id",
        "created_at",
    )
