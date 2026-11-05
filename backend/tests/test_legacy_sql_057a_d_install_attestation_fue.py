"""LOT05.7A-D FUE: signed installation manifest verifier, synthetic binary only.

No production publisher key, actual installer, Windows OS runtime attestation,
TPM/DPAPI anti-rollback root, clinical import or real patients are used.
"""
import base64
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

module_file = Path(__file__).resolve().parents[1] / "services" / "legacy_migration_install_attestation_v15.py"
spec = importlib.util.spec_from_file_location("_lot05d_manifest_under_test", module_file)
assert spec and spec.loader
d = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = d
spec.loader.exec_module(d)

_DOMAIN = b"DIGITAL-CROWN-LOT05-INSTALL-MANIFEST-V1\x00"
_SID = "S-1-5-80-111111-222222-333333-444444-555555"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("ascii")


def fixture(tmp_path):
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(serialization.Encoding.Raw,
                                         serialization.PublicFormat.Raw)
    root = d.PublisherRoot("fixture-vendor-root", pub, hashlib.sha256(pub).hexdigest(), 30)
    binary = tmp_path / "synthetic-lab-service.exe"
    binary.write_bytes(b"SYNTHETIC_SERVICE_BINARY_NOT_PRODUCT" + secrets.token_bytes(32))
    facts = d.ObservedService(
        "DigitalCrownSvcLab", _SID, "1.5.7.0", binary,
        "a" * 32, "fixture-ticket-key", "b" * 64, 3)
    body = {
        "schema_version": 1,
        "publisher": "Digital Crown",
        "publisher_root_id": root.key_id,
        "service_name": facts.service_name,
        "service_sid": facts.service_sid,
        "service_version": facts.service_version,
        "executable_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "installation_id": facts.installation_id,
        "ipc_audience": "digital-crown:lot05:synthetic-noop:v1",
        "authorized_operation": "SYNTHETIC_NOOP",
        "ticket_issuer_key_id": facts.ticket_issuer_key_id,
        "ticket_issuer_fingerprint_sha256": facts.ticket_issuer_fingerprint_sha256,
        "policy_version": facts.policy_version,
        "manifest_serial": 30,
        "not_before": 1000,
        "expires_at": 1100,
    }
    return key, root, facts, body


def signed(key, body):
    sig = key.sign(_DOMAIN + canonical(body))
    return canonical({"body": body, "signature":
                      base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")})


def verify(envelope, root, facts, now=1050):
    return d.verify_synthetic_installer_manifest(
        envelope, publisher_root=root, observed_service=facts, now_epoch=now)


def test_signed_manifest_approves_only_synthetic_noop(tmp_path):
    key, root, facts, body = fixture(tmp_path)
    receipt = verify(signed(key, body), root, facts)
    assert receipt.authorized_operation == "SYNTHETIC_NOOP"
    assert receipt.clinical_import_permitted is False
    assert receipt.service_sid == _SID
    assert receipt.executable_sha256 == body["executable_sha256"]


@pytest.mark.parametrize("field,value", [
    ("schema_version", 2),
    ("publisher", "Impostor"),
    ("publisher_root_id", "attacker"),
    ("service_name", "FakeService"),
    ("service_sid", "S-1-5-80-1-2-3-4-5"),
    ("service_version", "1.5.6.0"),
    ("executable_sha256", "f" * 64),
    ("installation_id", "b" * 32),
    ("ipc_audience", "digital-crown:clinical-import:v1"),
    ("authorized_operation", "CLINICAL_IMPORT"),
    ("ticket_issuer_key_id", "attacker-key"),
    ("ticket_issuer_fingerprint_sha256", "c" * 64),
    ("policy_version", 4),
    ("policy_version", True),
])
def test_validly_signed_wrong_claim_denied(tmp_path, field, value):
    key, root, facts, body = fixture(tmp_path)
    body[field] = value
    with pytest.raises(d.SyntheticInstallationDenied, match="MANIFEST_BINDING"):
        verify(signed(key, body), root, facts)


@pytest.mark.parametrize("field,changed", [
    ("service_name", "DifferentSvc"),
    ("service_sid", "S-1-5-80-1-2-3-4-5"),
    ("service_version", "1.5.8.0"),
    ("installation_id", "f" * 32),
    ("ticket_issuer_key_id", "other-issuer"),
    ("ticket_issuer_fingerprint_sha256", "f" * 64),
    ("policy_version", 4),
])
def test_replaced_os_observation_denied(tmp_path, field, changed):
    key, root, facts, body = fixture(tmp_path)
    with pytest.raises(d.SyntheticInstallationDenied):
        verify(signed(key, body), root, replace(facts, **{field: changed}))


def test_binary_mutation_after_signing_denied(tmp_path):
    key, root, facts, body = fixture(tmp_path)
    facts.executable_path.write_bytes(b"ATTACKER-REPLACED-EXECUTABLE")
    with pytest.raises(d.SyntheticInstallationDenied, match="MANIFEST_BINDING_EXECUTABLE_SHA256"):
        verify(signed(key, body), root, facts)


def test_symlink_to_binary_denied(tmp_path):
    key, root, facts, body = fixture(tmp_path)
    link = tmp_path / "alias.exe"
    try:
        link.symlink_to(facts.executable_path)
    except (NotImplementedError, OSError):
        pytest.skip("OS disallows unprivileged symlink creation")
    with pytest.raises(d.SyntheticInstallationDenied):
        verify(signed(key, body), root, replace(facts, executable_path=link))


def test_forged_manifest_signer_denied(tmp_path):
    _, root, facts, body = fixture(tmp_path)
    attacker = Ed25519PrivateKey.generate()
    with pytest.raises(d.SyntheticInstallationDenied, match="INVALID_PUBLISHER_SIGNATURE"):
        verify(signed(attacker, body), root, facts)


def test_swapped_root_public_key_with_old_pin_denied(tmp_path):
    key, root, facts, body = fixture(tmp_path)
    attacker_pub = Ed25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    with pytest.raises(d.SyntheticInstallationDenied, match="PUBLISHER_PIN_MISMATCH"):
        verify(signed(key, body), replace(root, public_key_raw=attacker_pub), facts)


def test_new_root_with_changed_fingerprint_cannot_verify_old_manifest(tmp_path):
    key, root, facts, body = fixture(tmp_path)
    attacker_pub = Ed25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    replaced_root = replace(root, public_key_raw=attacker_pub,
                            pinned_fingerprint_sha256=hashlib.sha256(attacker_pub).hexdigest())
    with pytest.raises(d.SyntheticInstallationDenied, match="INVALID_PUBLISHER_SIGNATURE"):
        verify(signed(key, body), replaced_root, facts)


def test_altered_manifest_without_resigning_denied(tmp_path):
    key, root, facts, body = fixture(tmp_path)
    envelope = json.loads(signed(key, body))
    envelope["body"]["executable_sha256"] = "0" * 64
    with pytest.raises(d.SyntheticInstallationDenied, match="INVALID_PUBLISHER_SIGNATURE"):
        verify(canonical(envelope), root, facts)


@pytest.mark.parametrize("serial,minimum", [(29,30), (0,30), (30,31), (True,30)])
def test_manifest_serial_rollback_denied(tmp_path, serial, minimum):
    key, root, facts, body = fixture(tmp_path)
    body["manifest_serial"] = serial
    with pytest.raises(d.SyntheticInstallationDenied, match="MANIFEST_SERIAL_ROLLBACK"):
        verify(signed(key, body), replace(root, minimum_manifest_serial=minimum), facts)


@pytest.mark.parametrize("dates,now", [
    ({"not_before": 1001}, 1000),
    ({"expires_at": 1050}, 1050),
    ({"not_before": -10000000, "expires_at": 50000000}, 1050),
    ({"expires_at": False}, 1050),
    ({"not_before": True}, 1050),
])
def test_manifest_time_invalid(tmp_path, dates, now):
    key, root, facts, body = fixture(tmp_path)
    body.update(dates)
    with pytest.raises(d.SyntheticInstallationDenied, match="INVALID_MANIFEST_TIME"):
        verify(signed(key, body), root, facts, now=now)


@pytest.mark.parametrize("scenario", [
    "unknown_field", "missing_field", "invalid_signature", "noncanonical",
    "duplicate", "oversize", "nan", "wrong_envelope", "empty",
])
def test_malformed_manifest_fail_closed(tmp_path, scenario):
    key, root, facts, body = fixture(tmp_path)
    if scenario == "unknown_field":
        body["extra"] = "not-allowed"
        data = signed(key, body)
    elif scenario == "missing_field":
        del body["installation_id"]
        data = signed(key, body)
    elif scenario == "invalid_signature":
        msg = json.loads(signed(key, body))
        msg["signature"] = "bad"
        data = canonical(msg)
    elif scenario == "noncanonical":
        data = json.dumps(json.loads(signed(key, body))).encode("ascii")
    elif scenario == "duplicate":
        data = signed(key, body).replace(b'"body":', b'"body":{},"body":', 1)
    elif scenario == "oversize":
        data = signed(key, body) + b" " * 8192
    elif scenario == "nan":
        data = signed(key, body).replace(b'"schema_version":1', b'"schema_version":NaN', 1)
    elif scenario == "wrong_envelope":
        data = canonical({"body": body})
    else:
        data = b""
    with pytest.raises(d.SyntheticInstallationDenied):
        verify(data, root, facts)


def test_missing_root_and_os_service_facts_denied(tmp_path):
    key, root, facts, body = fixture(tmp_path)
    data = signed(key, body)
    with pytest.raises(d.SyntheticInstallationDenied, match="MISSING_PUBLISHER_ROOT"):
        d.verify_synthetic_installer_manifest(data, publisher_root=None, observed_service=facts, now_epoch=1050)
    with pytest.raises(d.SyntheticInstallationDenied, match="MISSING_OS_SERVICE_FACTS"):
        d.verify_synthetic_installer_manifest(data, publisher_root=root, observed_service=None, now_epoch=1050)


def test_unknown_root_floor_is_denied(tmp_path):
    key, root, facts, body = fixture(tmp_path)
    with pytest.raises(d.SyntheticInstallationDenied, match="MISSING_ROLLBACK_FLOOR"):
        verify(signed(key, body), replace(root, minimum_manifest_serial=0), facts)


def test_file_vanishes_fail_closed(tmp_path):
    key, root, facts, body = fixture(tmp_path)
    facts.executable_path.unlink()
    with pytest.raises(d.SyntheticInstallationDenied):
        verify(signed(key, body), root, facts)


def test_bogus_clock_denied(tmp_path):
    key, root, facts, body = fixture(tmp_path)
    with pytest.raises(d.SyntheticInstallationDenied, match="INVALID_CLOCK"):
        verify(signed(key, body), root, facts, now=True)
