"""LOT06 C05B-03K — REAL source-byte handoff from #909 into SQLCipher LAB.

All captures, identities, staff approval, device keys and media are synthetic.
No FastAPI product route, DICOM device, Windows SCM install, clinic migration,
real human verification or clinical authority is exercised.
"""
from __future__ import annotations

import asyncio
import base64
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import secrets

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.models_media_core import ClinicalAsset
from backend.services.clinical_asset_service import create_clinical_asset
from backend.services.clinical_asset_storage import (
    read_clinical_asset_bytes, store_clinical_asset_bytes,
)
from backend.services.imaging_acquisition_preflight_v15 import (
    resolve_acquisition_preflight,
)
from isolated_fue_lot06c.test_sqlcipher_real_staff_station_bridge_v15 import (
    BridgeRejected, approvals, audit, bridge as synthetic_sqlcipher_bridge,
    devices, outbox, receipts, _counts, _issue,
)
from tools.imaging_gateway import HotFolder
from tools.imaging_gateway.bridge_background_lab import (
    BridgeLabConfigurationError, make_lab_collector,
    start_if_enabled, stop_bridge_lab,
)
from tools.imaging_gateway.gateway import GatewayError


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91Jpz"
    "AAAAFklEQVR4nGPkEpFjYGBgYmBgYGBgAAAC5gBAXKUgWwAAAABJRU5ErkJggg=="
)


def _isolated_hotfolder(tmp_path: Path):
    root = tmp_path / "real-hotfolder-bridge-test"
    root.mkdir()
    incoming = root / "incoming"
    incoming.mkdir()
    (root / ".digitalcrown-imaging-lab-only").write_text(
        "DIGITALCROWN_IMAGING_LAB_ONLY_V1\n", encoding="utf-8"
    )
    env = {
        "DC_V15_06_BRIDGE_LAB": "1",
        "ENVIRONMENT": "test",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "DC_V15_06_BRIDGE_LAB_ROOT": str(root),
        "DC_V15_06_BRIDGE_LAB_KEY_HEX": secrets.token_hex(32),
    }
    source = incoming / "unlinked-synthetic-capture.png"
    source.write_bytes(PNG)
    source.with_name(source.name + ".ready").write_text(
        json.dumps({
            "version": 1, "size": len(PNG),
            "sha256": hashlib.sha256(PNG).hexdigest(),
        }), encoding="utf-8"
    )
    return root, source, env


def _collector_bytes(collector):
    assert collector.scan_once()["unstable"] == 1
    assert collector.scan_once()["staged"] == 1
    items = collector.items()
    assert len(items) == 1
    assert items[0]["state"] == "PENDING_CONFIRMATION"
    assert items[0]["mime"] == "image/png"
    assert items[0]["digest"] == hashlib.sha256(PNG).hexdigest()
    assert collector.read_verified(items[0]["id"]) == PNG
    blob = next(collector.spool.glob("*.dc6"))
    assert PNG not in blob.read_bytes()
    return items[0], collector.read_verified(items[0]["id"])


def test_c05b03k_verified_hotfolder_to_actual_sqlcipher_asset_receipt_and_replay(
    synthetic_sqlcipher_bridge, tmp_path, monkeypatch,
):
    monkeypatch.setenv("DC06C05B03K_TEST_ONLY", "1")
    engine, claim, device_token, station_token, media_root, _ = synthetic_sqlcipher_bridge
    assert _counts(engine) == (0, 0, 0)
    root, source, env = _isolated_hotfolder(tmp_path)
    assert make_lab_collector({}) is None
    collector = make_lab_collector(env)
    item, actual_bytes = _collector_bytes(collector)
    assert item["state"] != "CONFIRMED"
    assert source.read_bytes() == actual_bytes
    decision = resolve_acquisition_preflight(
        Session(engine), employer_id=claim.tenant, patient_id=claim.patient,
    )
    assert decision.status == "STAFF_CONFIRMATION_REQUIRED"
    assert decision.patient_id == claim.patient

    # The existing synthetic SQLCipher fixture has pre-approved the capture.
    # This is NOT a trusted product staff/human approval ceremony.
    # Handoff the ACTUAL DECRYPTED spool bytes into a *new* clinical asset,
    # then update only the synthetic authority's already-consented fixture.
    with Session(engine) as db:
        asset = create_clinical_asset(
            db, employer_id=claim.tenant, patient_id=claim.patient,
            asset_type="PHOTO", source_kind="DEVICE_CAPTURE",
            mime_type="image/png", created_by=claim.staff,
            provenance_json={
                "ingestion_channel": "C05B03E_SYNTHETIC_ONLY",
                "capture_id": claim.capture, "device": claim.device,
            },
        )
        store_clinical_asset_bytes(
            db, employer_id=claim.tenant, patient_id=claim.patient,
            asset_id=asset.id, content=actual_bytes, media_root=media_root,
        )
        incoming_claim = replace(
            claim, asset_id=asset.id, digest=hashlib.sha256(actual_bytes).hexdigest(),
            byte_size=len(actual_bytes),
        )
        db.execute(update(approvals).where(
            approvals.c.tenant == claim.tenant,
            approvals.c.device == claim.device,
            approvals.c.capture == claim.capture,
        ).values(
            asset_id=incoming_claim.asset_id, digest=incoming_claim.digest,
            byte_size=incoming_claim.byte_size,
        ))
        db.commit()

    with Session(engine) as db:
        clinical = db.get(ClinicalAsset, incoming_claim.asset_id)
        assert clinical.patient_id == claim.patient
        assert clinical.employer_id == claim.tenant
        assert clinical.storage_format == "AESGCM_V1"
        assert read_clinical_asset_bytes(
            db, employer_id=claim.tenant, patient_id=claim.patient,
            asset_id=incoming_claim.asset_id, media_root=media_root,
        ) == actual_bytes

    args = (engine, incoming_claim, device_token, station_token, media_root)
    for bad in (
        replace(incoming_claim, patient=incoming_claim.patient + 100000),
        replace(incoming_claim, digest="0" * 64),
        replace(incoming_claim, device="foreign-device"),
    ):
        with pytest.raises(BridgeRejected):
            _issue(engine, bad, device_token, station_token, media_root)
        assert _counts(engine) == (0, 0, 0)

    with pytest.raises(BridgeRejected, match="INJECTED_TRANSACTION_ROLLBACK"):
        _issue(*args, fail_at="after_audit")
    assert _counts(engine) == (0, 0, 0)
    rid = _issue(*args)
    assert rid.startswith("LAB-ONLY-")
    assert _counts(engine) == (1, 1, 1)
    # Lost ACK: server already committed; replay is the same immutable receipt.
    assert _issue(*args) == rid
    assert _counts(engine) == (1, 1, 1)
    with Session(engine) as db:
        receipt = db.execute(select(receipts).where(
            receipts.c.tenant == claim.tenant,
            receipts.c.capture == claim.capture,
        )).mappings().one()
        assert receipt["asset_id"] == incoming_claim.asset_id
        assert receipt["digest"] == item["digest"]
        assert db.execute(select(audit.c.event).where(
            audit.c.receipt_id == rid
        )).scalar_one() == "CAPTURE_COMMITTED"
        assert db.execute(select(outbox.c.event).where(
            outbox.c.receipt_id == rid
        )).scalar_one() == "MEDIA_READY"

    # Agent restart never creates a second capture; cannot claim server ACK.
    restarted = HotFolder(collector.config)
    assert restarted.scan_once()["unstable"] == 1
    assert restarted.scan_once()["duplicate"] == 1
    assert len(restarted.items()) == 1
    assert restarted.read_verified(item["id"]) == PNG
    assert restarted.items()[0]["state"] == "PENDING_CONFIRMATION"
    assert _issue(*args) == rid
    assert _counts(engine) == (1, 1, 1)
    print("C05B03K_REAL_HOTFOLDER_TO_SQLCIPHER_CLINICAL_ASSET_RECEIPT_LAB_PASS")


def test_c05b03k_corrupt_spool_refused_without_receipt(
    synthetic_sqlcipher_bridge, tmp_path,
):
    engine, _claim, _token, _station, _media, _ = synthetic_sqlcipher_bridge
    root, _source, env = _isolated_hotfolder(tmp_path)
    collector = make_lab_collector(env)
    item, _data = _collector_bytes(collector)
    spool = next(collector.spool.glob("*.dc6"))
    payload = spool.read_bytes()
    spool.write_bytes(payload[:-1] + bytes([payload[-1] ^ 1]))
    with pytest.raises(GatewayError):
        collector.read_verified(item["id"])
    assert _counts(engine) == (0, 0, 0)


def test_c05b03k_production_or_untrusted_runtime_never_opens_fixture(tmp_path):
    root, _source, env = _isolated_hotfolder(tmp_path)
    with pytest.raises(BridgeLabConfigurationError, match="TEST_ISOLATION_REQUIRED"):
        make_lab_collector({**env, "ENVIRONMENT": "production"})
    with pytest.raises(BridgeLabConfigurationError, match="BACKEND_TEST_REQUIRED"):
        start_if_enabled(env, trusted_environment="production")
    assert not (root / "private").exists()


@pytest.mark.asyncio
async def test_c05b03k_supervised_isolated_process_stages_then_reaps(tmp_path):
    root, source, env = _isolated_hotfolder(tmp_path)
    handle = start_if_enabled(env, trusted_environment="test")
    assert handle is not None and handle.process is not None
    collector = make_lab_collector(env)
    try:
        async def staged():
            for _ in range(120):
                rows = collector.items()
                if rows:
                    assert rows[0]["state"] == "PENDING_CONFIRMATION"
                    return rows[0]
                await asyncio.sleep(0.05)
            raise AssertionError("supervised LAB process did not stage fixture")
        staged_item = await asyncio.wait_for(staged(), timeout=9)
        assert collector.read_verified(staged_item["id"]) == PNG
    finally:
        stopped = await stop_bridge_lab(handle)
    assert stopped
    assert handle.process.poll() is not None
    assert source.read_bytes() == PNG
    assert len(HotFolder(collector.config).items()) == 1
    print("C05B03K_SUPERVISED_ISOLATED_CAPTURE_ONLY_PASS")
