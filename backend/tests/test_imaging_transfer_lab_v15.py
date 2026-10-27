"""LOT06-B transfer remains disabled outside isolated tests."""
import pytest
from backend.services.imaging_acquisition_transfer_lab_v15 import TransferLabRejected, guard


def test_transfer_is_disabled_in_production(db, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DC_V15_06_TRANSFER_LAB", "1")
    with pytest.raises(TransferLabRejected, match="ISOLATED_TRANSFER_DISABLED"):
        guard(db)
