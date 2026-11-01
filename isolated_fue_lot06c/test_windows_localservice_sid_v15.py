"""H05: real different Windows LocalService SID must fail file read AND DPAPI unseal."""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from isolated_fue_lot06c.windows_dpapi_gateway_lab import (
    create_key,sign,_entropy,_scope,
)
pytestmark=pytest.mark.skipif(sys.platform!="win32",reason="Windows service token only")
SCOPE=dict(tenant=705,device="synthetic-h05-device",station="synthetic-h05-station",generation=1)
MESSAGE=b"LOT06 H05 synthetic no-PHI signature"
def _pwsh(script,env):
    return subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-Command",script],
                          env=env,capture_output=True,text=True,timeout=40)
def test_h05_localservice_real_other_sid_denies_acl_and_dpapi(tmp_path):
    assert os.getenv("ENVIRONMENT")=="test"
    assert os.getenv("DIGITALCROWN_ISOLATED_RUNTIME")=="true"
    assert os.getenv("DC06C05B03H03_TEST_ONLY")=="1"
    assert os.getenv("DC06C05B03H05_TEST_ONLY")=="1"
    import win32api,win32con,win32security
    token=win32security.OpenProcessToken(win32api.GetCurrentProcess(),win32con.TOKEN_QUERY)
    owner=win32security.ConvertSidToStringSid(
        win32security.GetTokenInformation(token,win32security.TokenUser)[0])
    assert owner!="S-1-5-19"
    folder=tmp_path/"owner-vault"
    folder.mkdir()
    key_file=folder/"test-only-key.dpapi.json"
    pub=Ed25519PublicKey.from_public_bytes(bytes.fromhex(create_key(key_file,**SCOPE)))
    pub.verify(sign(key_file,MESSAGE,**SCOPE),MESSAGE)
    private_blob=json.loads(key_file.read_text(encoding="ascii"))
    shared=Path(tempfile.mkdtemp(prefix="dc_h05_",dir=os.environ["ProgramData"]))
    name="DC06H05Lab"+uuid.uuid4().hex[:12]
    script=shared/"probe.ps1"
    inputs=shared/"synthetic.json"
    results=shared/"result.json"
    env=dict(os.environ,DC_H05_TASK=name,DC_H05_SCRIPT=str(script),DC_H05_INPUT=str(inputs))
    scheduled=False
    try:
        # The shared exchange contains only public scope, encrypted blob and entropy.
        grant=subprocess.run(["icacls",str(shared),"/grant","*S-1-5-19:(OI)(CI)M"],
                             capture_output=True,text=True,timeout=20)
        assert grant.returncode==0,"H05_EXCHANGE_NOT_ACCESSIBLE_TO_SERVICE"
        script.write_bytes(Path(__file__).with_name("h05_localservice_probe.ps1").read_bytes())
        inputs.write_text(json.dumps({
            "owner_sid":owner,"vault_file":str(key_file),
            "ciphertext":private_blob["dpapi_blob"],
            "entropy":base64.b64encode(_entropy(_scope(**SCOPE))).decode("ascii"),
            "output":str(results)
        }),encoding="ascii")
        launch=(
            "$ErrorActionPreference='Stop';"
            "$pr=New-ScheduledTaskPrincipal -UserId 'NT AUTHORITY\\LOCAL SERVICE' "
            "-LogonType ServiceAccount -RunLevel Limited;"
            "$ac=New-ScheduledTaskAction -Execute 'powershell.exe' "
            "-Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ' + "
            "'\"' + $env:DC_H05_SCRIPT + '\" -InputPath \"' + $env:DC_H05_INPUT + '\"');"
            "$tr=New-ScheduledTaskTrigger -Once -At (Get-Date).AddHours(2);"
            "Register-ScheduledTask -TaskName $env:DC_H05_TASK "
            "-Action $ac -Principal $pr -Trigger $tr -Force | Out-Null;"
            "Start-ScheduledTask -TaskName $env:DC_H05_TASK -ErrorAction Stop"
        )
        scheduled=True
        run=_pwsh(launch,env)
        assert run.returncode==0,"H05_WINDOWS_SERVICE_TASK_NOT_AVAILABLE"
        proof=None
        for _ in range(80):
            if results.is_file():
                proof=json.loads(results.read_text(encoding="ascii"))
                break
            time.sleep(0.5)
        assert proof is not None,"H05_SERVICE_TASK_NO_RESULT"
        assert proof=={"identity_sid":"S-1-5-19","distinct":True,
                       "file_denied":True,"dpapi_denied":True},proof
        pub.verify(sign(key_file,MESSAGE,**SCOPE),MESSAGE)
        out=Path(os.environ["DC06C05B03H05_EVIDENCE_DIR"])
        out.mkdir(parents=True,exist_ok=True)
        (out/"lot06c05b03h05-localservice.json").write_text(json.dumps({
            "identity_sid":"S-1-5-19",
            "native_localservice_separate_token_verified":True,
            "owner_only_vault_access_rejected_by_second_sid":True,
            "native_dpapi_currentuser_unseal_rejected_by_second_sid":True,
            "owner_signing_after_second_identity_preserved":True,
            "non_interactive_service_identity_only":True,
            "independent_interactive_second_user_verified":False,
            "full_os_reboot_verified":False,
            "actual_device_or_dental_driver_verified":False,
            "production_service_installer_verified":False,
            "product_ready":False,
            "clinical_go":False
        },sort_keys=True,indent=2)+"\n",encoding="utf8")
        print("C05B03H05_ACTUAL_LOCALSERVICE_SID_ACL_AND_DPAPI_REFUSALS_PASS")
    finally:
        if scheduled:
            _pwsh("Unregister-ScheduledTask -TaskName $env:DC_H05_TASK "
                  "-Confirm:$false -ErrorAction SilentlyContinue",env)
        shutil.rmtree(shared,ignore_errors=True)
