from pathlib import Path

from backend.models_media_core import ClinicalAsset


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "alembic" / "versions" / "c2a55e700002_add_clinical_asset_storage.py"


def test_c2_storage_migration_is_chained_from_c1():
    text = MIGRATION.read_text(encoding="utf-8")
    assert 'revision: str = "c2a55e700002"' in text
    assert 'down_revision: Union[str, None] = "c1a55e700001"' in text
    assert '"storage_key"' in text
    assert '"storage_format"' in text
    assert '"stored_at"' in text


def test_c2_model_exposes_storage_binding_and_tenant_digest_index():
    columns = ClinicalAsset.__table__.columns
    assert columns["storage_key"].nullable is True
    assert columns["storage_format"].nullable is True
    assert columns["stored_at"].nullable is True

    indexes = {index.name: tuple(column.name for column in index.columns) for index in ClinicalAsset.__table__.indexes}
    assert indexes["ix_clinical_assets_tenant_sha256"] == ("employer_id", "sha256")
