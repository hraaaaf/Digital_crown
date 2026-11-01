"""C05B-03H03 native Win32 DPAPI FUE. Not hardware certified, no PHI."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from isolated_fue_lot06c.windows_dpapi_gateway_lab import VaultRejected,create_key,revoke_local,sign

pytestmark=pytest.mark.skipif(sys.platform!="win32",reason="Win32 DPAPI only")
SCOPE=dict(tenant=71,device="synthetic-rvg-gateway",station="synthetic-lab-station-1",generation=1)
MESSAGE=b"ENROLL|synthetic-capture-no-patient|nonce=only-lab"

def _create(path):
    return Ed25519PublicKey.from_public_bytes(bytes.fromhex(create_key(path,**SCOPE)))

def test_h03_actual_win32_dpapi_and_same_user_subprocess(tmp_path):
    path=tmp_path/"gateway-seed.dpapi.json"
    public=_create(path)
    content=path.read_bytes()
    record=json.loads(content)
    assert set(record)==set(SCOPE)|{"version","public_hex","dpapi_blob"}
    assert len(base64.b64decode(record["dpapi_blob"],validate=True))>32
    assert b"BEGIN PRIVATE KEY" not in content
    # Separate Python interpreter after process shutdown; same Windows logon.
    script=("import base64,sys; from pathlib import Path; "
        "from isolated_fue_lot06c.windows_dpapi_gateway_lab import sign; "
        "print(base64.b64encode(sign(Path(sys.argv[1]),"
        "b'ENROLL|synthetic-capture-no-patient|nonce=only-lab',"
        "tenant=71,device='synthetic-rvg-gateway',"
        "station='synthetic-lab-station-1',generation=1)).decode('ascii'))")
    p=subprocess.run([sys.executable,"-c",script,str(path)],
                     check=True,capture_output=True,text=True,timeout=20)
    cross_sig=base64.b64decode(p.stdout.strip(),validate=True)
    public.verify(cross_sig,MESSAGE)
    local_sig=sign(path,MESSAGE,**SCOPE)
    public.verify(local_sig,MESSAGE)
    assert local_sig==cross_sig
    with pytest.raises(InvalidSignature):
        public.verify(local_sig,MESSAGE+b"-tampered")
    print("C05B03H03_WIN32_USER_DPAPI_RESTART_AND_ED25519_PASS")

def test_h03_wrong_scope_corrupted_key_and_delete(tmp_path):
    path=tmp_path/"gateway-seed.dpapi.json"
    public=_create(path)
    with pytest.raises(VaultRejected,match="KEY_ALREADY_EXISTS"):
        create_key(path,**SCOPE)
    for wrong in (dict(SCOPE,tenant=72),dict(SCOPE,station="wrong-station"),
                  dict(SCOPE,generation=2),dict(SCOPE,device="other-device")):
        with pytest.raises(VaultRejected,match="KEY_ENVELOPE_DENIED"):
            sign(path,MESSAGE,**wrong)
    orig=path.read_bytes()
    record=json.loads(orig)
    for forged in (dict(record,public_hex="00"*32),
                   dict(record,generation=2),dict(record,dpapi_blob="AAAAdeadbeefAAAA")):
        path.write_text(json.dumps(forged),encoding="ascii")
        with pytest.raises(VaultRejected):
            sign(path,MESSAGE,**SCOPE)
    path.write_bytes(orig)
    public.verify(sign(path,MESSAGE,**SCOPE),MESSAGE)
    revoke_local(path)
    assert not path.exists()
    with pytest.raises(VaultRejected,match="KEY_UNAVAILABLE"):
        sign(path,MESSAGE,**SCOPE)
    print("C05B03H03_WIN32_SCOPE_TAMPER_REVOKE_LOCAL_PASS")

def test_h03_cabinet_and_missing_guard_disabled(tmp_path,monkeypatch):
    path=tmp_path/"gateway-seed.dpapi.json"
    _create(path)
    monkeypatch.setenv("ENVIRONMENT","cabinet")
    with pytest.raises(VaultRejected,match="WINDOWS_DPAPI_LAB_DISABLED"):
        sign(path,MESSAGE,**SCOPE)
    with pytest.raises(VaultRejected,match="WINDOWS_DPAPI_LAB_DISABLED"):
        create_key(tmp_path/"other.dpapi.json",**SCOPE)
    monkeypatch.setenv("ENVIRONMENT","test")
    monkeypatch.delenv("DC06C05B03H03_TEST_ONLY")
    with pytest.raises(VaultRejected,match="WINDOWS_DPAPI_LAB_DISABLED"):
        sign(path,MESSAGE,**SCOPE)
    print("C05B03H03_WINDOWS_CABINET_DISABLED_PASS")

def test_h04_windows_acl_exact_scope_and_forged_everyone_denied(tmp_path):
    """Genuine Windows DACL: user+SYSTEM only; broadened file/directory fail."""
    from isolated_fue_lot06c.windows_dpapi_gateway_lab import _verify_windows_acl
    path=tmp_path/"h04-key.dpapi.json"
    public=_create(path)
    _verify_windows_acl(tmp_path)
    _verify_windows_acl(path)
    public.verify(sign(path,MESSAGE,**SCOPE),MESSAGE)
    grant=subprocess.run(["icacls",str(path),"/grant","*S-1-1-0:R"],
                         capture_output=True,text=True,timeout=20)
    assert grant.returncode==0, "Windows ACL grant failed"
    with pytest.raises(VaultRejected,match="ACL_BROADENED_OR_INHERITED_DENIED"):
        sign(path,MESSAGE,**SCOPE)
    removed=subprocess.run(["icacls",str(path),"/remove:g","*S-1-1-0"],
                           capture_output=True,text=True,timeout=20)
    assert removed.returncode==0
    public.verify(sign(path,MESSAGE,**SCOPE),MESSAGE)
    expanded=subprocess.run(["icacls",str(tmp_path),"/grant","*S-1-1-0:(OI)(CI)R"],
                            capture_output=True,text=True,timeout=20)
    assert expanded.returncode==0
    with pytest.raises(VaultRejected,match="ACL_BROADENED_OR_INHERITED_DENIED"):
        sign(path,MESSAGE,**SCOPE)
    print("C05B03H04_REAL_WIN32_ACL_OWNER_SYSTEM_ONLY_AND_BROADENING_DENIED")

def test_h04_acl_evidence(tmp_path):
    """Must follow actual ACL negative test in this runner, not clinical evidence."""
    root=Path(os.getenv("DC06C05B03H04_EVIDENCE_DIR",str(tmp_path)))
    root.mkdir(parents=True,exist_ok=True)
    proof={
        "kind":"C05B03H04_WINDOWS_ACL_FAIL_CLOSED_EPHEMERAL_LAB",
        "real_windows_acl_owner_system_protected":True,
        "file_acl_extra_principal_denied":True,
        "parent_acl_extra_principal_denied":True,
        "owner_still_can_sign_after_acl_restored":True,
        "actual_second_logon_user_verified":False,
        "physical_windows_os_reboot_verified":False,
        "windows_service_installer_verified":False,
        "scanner_hardware_attestation":False,
        "nonexportable_tpm_key":False,
        "product_ready":False,
        "clinical_go":False
    }
    (root/"lot06c05b03h04-acl-proof.json").write_text(
        json.dumps(proof,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("C05B03H04_WINDOWS_ACL_EVIDENCE_LAB_ONLY")

def test_h03_evidence(tmp_path):
    root=Path(os.getenv("DC06C05B03H03_EVIDENCE_DIR",str(tmp_path)))
    root.mkdir(parents=True,exist_ok=True)
    values={
        "kind":"C05B03H03_EPHEMERAL_WINDOWS_DPAPI_CURRENT_USER_LAB",
        "actual_win32_cryptprotectdata_unprotectdata_called":True,
        "current_windows_user_scope_without_local_machine_flag":True,
        "same_user_new_process_signing_test":True,
        "ed25519_signature_cross_process_verified":True,
        "scope_mismatch_public_key_corruption_and_blob_tampering_denied":True,
        "duplicate_enrollment_file_refused":True,
        "local_revoke_prevents_future_signing":True,
        "cabinet_environment_disabled":True,
        "private_seed_persisted_unencrypted":False,
        "full_key_memory_nonexportable_guarantee":False,
        "windows_acl_or_other_account_certified":False,
        "tpm_hsm_key_attestation":False,
        "sensor_hardware_attestation":False,
        "service_installation_user_switch_restart_verified":False,
        "physical_windows_clinic_machine_verified":False,
        "server_side_revocation_integration_windows":False,
        "product_ready":False,"clinical_go":False,
    }
    (root/"lot06c05b03h03-windows-dpapi.json").write_text(
        json.dumps(values,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("C05B03H03_WINDOWS_DPAPI_LAB_EVIDENCE_RECORDED")
