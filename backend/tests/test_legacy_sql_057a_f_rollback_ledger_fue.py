"""FUE-G05.7A-F — TEST-ONLY durable replay + independent witness model.

No clinical data, production publisher, hardware counter or real issuer.
"""
from pathlib import Path
import importlib.util
import shutil
import sys

import pytest

module_path = Path(__file__).resolve().parent / "fixtures" / "lot05_7a_f_rollback_ledger_lab.py"
spec = importlib.util.spec_from_file_location("_lot05_f_ledger_lab", module_path)
assert spec and spec.loader
f = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = f
spec.loader.exec_module(f)

INSTALL_ID = "a" * 32
NONCE_A = "1" * 32
NONCE_B = "2" * 32


class SyntheticIndependentWitness:
    """Counter survives local database backup/restore only in this CI process."""

    def __init__(self, initial=0):
        self.value = initial
        self.fail_read = False
        self.fail_advance = False
        self.advance_then_crash = False

    def current_counter(self, installation_id):
        assert installation_id == INSTALL_ID
        if self.fail_read:
            raise RuntimeError("synthetic witness unavailable")
        return self.value

    def compare_and_advance(self, installation_id, expected):
        assert installation_id == INSTALL_ID
        if self.fail_advance:
            raise RuntimeError("synthetic witness unavailable")
        if self.value != expected:
            return -1
        self.value += 1
        if self.advance_then_crash:
            raise RuntimeError("simulated crash after witness advance")
        return self.value


def ledger(tmp_path, witness, db_name="local-noop-ledger.sqlite"):
    return f.WitnessedReplayLedgerLab(tmp_path / db_name, INSTALL_ID, witness)


def test_first_consume_and_duplicate_after_reopen(tmp_path):
    witness = SyntheticIndependentWitness()
    one = ledger(tmp_path, witness)
    assert one.consume_once("publisher:tenant-a", NONCE_A) is True
    assert witness.value == 1
    assert one.consume_once("publisher:tenant-a", NONCE_A) is False
    two = ledger(tmp_path, witness)
    assert two.consume_once("publisher:tenant-a", NONCE_A) is False
    assert witness.value == 1


def test_isolation_between_ticket_namespaces(tmp_path):
    witness = SyntheticIndependentWitness()
    store = ledger(tmp_path, witness)
    assert store.consume_once("issuer:tenant-a", NONCE_A)
    assert store.consume_once("issuer:tenant-b", NONCE_A)
    assert store.consume_once("issuer:tenant-a", NONCE_A) is False
    assert witness.value == 2


def test_restored_old_local_snapshot_is_denied(tmp_path):
    witness = SyntheticIndependentWitness()
    store = ledger(tmp_path, witness)
    assert store.consume_once("tenant", NONCE_A)
    snapshot = tmp_path / "rollback-snapshot.sqlite"
    shutil.copy2(tmp_path / "local-noop-ledger.sqlite", snapshot)
    assert store.consume_once("tenant", NONCE_B)
    shutil.copy2(snapshot, tmp_path / "local-noop-ledger.sqlite")
    with pytest.raises(f.LedgerLabDenied, match="INDEPENDENT_WITNESS_MISMATCH"):
        ledger(tmp_path, witness).consume_once("tenant", NONCE_B)


def test_deleted_ledger_cannot_reset_witness(tmp_path):
    witness = SyntheticIndependentWitness()
    assert ledger(tmp_path, witness).consume_once("tenant", NONCE_A)
    (tmp_path / "local-noop-ledger.sqlite").unlink()
    with pytest.raises(f.LedgerLabDenied, match="INDEPENDENT_WITNESS_MISMATCH"):
        ledger(tmp_path, witness).consume_once("tenant", NONCE_B)


def test_cloned_older_database_cannot_consume_again(tmp_path):
    witness = SyntheticIndependentWitness()
    ledger(tmp_path, witness)
    shutil.copy2(tmp_path / "local-noop-ledger.sqlite", tmp_path / "clone.sqlite")
    assert ledger(tmp_path, witness).consume_once("tenant", NONCE_A)
    with pytest.raises(f.LedgerLabDenied, match="INDEPENDENT_WITNESS_MISMATCH"):
        ledger(tmp_path, witness, "clone.sqlite").consume_once("tenant", NONCE_A)


def test_crash_between_witness_advance_and_db_commit_is_fail_closed(tmp_path):
    witness = SyntheticIndependentWitness()
    store = ledger(tmp_path, witness)
    witness.advance_then_crash = True
    with pytest.raises(f.LedgerLabDenied, match="LEDGER_OR_WITNESS_UNAVAILABLE"):
        store.consume_once("tenant", NONCE_A)
    witness.advance_then_crash = False
    with pytest.raises(f.LedgerLabDenied, match="INDEPENDENT_WITNESS_MISMATCH"):
        ledger(tmp_path, witness).consume_once("tenant", NONCE_A)


def test_unavailable_witness_cannot_succeed(tmp_path):
    witness = SyntheticIndependentWitness()
    store = ledger(tmp_path, witness)
    witness.fail_read = True
    with pytest.raises(f.LedgerLabDenied, match="LEDGER_OR_WITNESS_UNAVAILABLE"):
        store.consume_once("tenant", NONCE_A)
    witness.fail_read = False
    witness.fail_advance = True
    with pytest.raises(f.LedgerLabDenied, match="LEDGER_OR_WITNESS_UNAVAILABLE"):
        store.consume_once("tenant", NONCE_A)
    assert witness.value == 0


def test_witness_counter_rollback_denied(tmp_path):
    witness = SyntheticIndependentWitness()
    store = ledger(tmp_path, witness)
    assert store.consume_once("tenant", NONCE_A)
    witness.value = 0  # attacker substitutes an older witness state
    with pytest.raises(f.LedgerLabDenied, match="INDEPENDENT_WITNESS_MISMATCH"):
        store.consume_once("tenant", NONCE_B)


@pytest.mark.parametrize("invalid", [None, "", "a" * 385, "\n", "\u00e9", 123])
def test_invalid_namespace_denied_without_witness_advance(tmp_path, invalid):
    witness = SyntheticIndependentWitness()
    store = ledger(tmp_path, witness)
    with pytest.raises(f.LedgerLabDenied, match="INVALID_NAMESPACE"):
        store.consume_once(invalid, NONCE_A)
    assert witness.value == 0


@pytest.mark.parametrize("invalid", ["", "a" * 31, "z" * 32, "A" * 32, True, None])
def test_invalid_nonce_denied(tmp_path, invalid):
    witness = SyntheticIndependentWitness()
    store = ledger(tmp_path, witness)
    with pytest.raises(f.LedgerLabDenied, match="INVALID_NONCE"):
        store.consume_once("tenant", invalid)
    assert witness.value == 0


def test_mismatched_installation_id_denied(tmp_path):
    witness = SyntheticIndependentWitness()
    store = ledger(tmp_path, witness)
    assert store.consume_once("tenant", NONCE_A)
    with pytest.raises(f.LedgerLabDenied, match="INSTALLATION_BINDING_MISMATCH"):
        f.WitnessedReplayLedgerLab(tmp_path / "local-noop-ledger.sqlite", "b" * 32, witness)


def test_missing_or_caller_controlled_witness_denied(tmp_path):
    with pytest.raises(f.LedgerLabDenied, match="NO_INDEPENDENT_WITNESS"):
        f.WitnessedReplayLedgerLab(tmp_path / "no-witness.sqlite", INSTALL_ID, None)


def test_symlink_ledger_denied(tmp_path):
    original = tmp_path / "original.sqlite"
    witness = SyntheticIndependentWitness()
    assert f.WitnessedReplayLedgerLab(original, INSTALL_ID, witness)
    alias = tmp_path / "alias.sqlite"
    try:
        alias.symlink_to(original)
    except (NotImplementedError, OSError):
        pytest.skip("OS disallows unprivileged symlinks")
    with pytest.raises(f.LedgerLabDenied, match="UNTRUSTED_LEDGER_PATH"):
        f.WitnessedReplayLedgerLab(alias, INSTALL_ID, witness)


def test_local_file_only_not_a_clinical_authority(tmp_path):
    witness = SyntheticIndependentWitness()
    store = ledger(tmp_path, witness)
    assert not hasattr(store, "import_clinical")
    assert not hasattr(store, "authorize")
    assert store.consume_once("synthetic-only", NONCE_A)
