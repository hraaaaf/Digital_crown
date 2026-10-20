"""J10D interoperability: ticket issued by actual J10C Windows SCM signer.
No clinical restore; this is NOT an installed SCM consumer proof.
"""
import json
import unittest
import os
import sys
import subprocess
from pathlib import Path
from backend.tests.test_legacy_sql_057j10c_real_scm_bound_sqlcipher_lab import ConnectedJ10C
from backend.tests.fixtures.lot05j10d_signed_replay_lab import verify_and_burn, SignedReplayDenied

class RealIssuerToVerifier(ConnectedJ10C):
    def test_01_actual_scm_jwt_rsa_job_manifest_sqlcipher_copy(self):
        super().test_01_actual_scm_jwt_rsa_job_manifest_sqlcipher_copy()
        ticket=json.loads((self.root/"isolated-signed.json").read_text(encoding="utf-8-sig"))
        pin=(self.root/"trusted-rsa-public.fake").read_text(encoding="ascii")
        claims=dict(segment.split("=",1) for segment in ticket["body"].split("|"))
        # Actual Windows ServiceBase consumes the J10C real SCM ticket first.
        script=Path(__file__).resolve().parent/"fixtures"/"lot05j10d_real_issuer_to_installed_consumer_probe.ps1"
        env=dict(os.environ,LOT05J10D_FAKE_SCM_INTEROP_ONLY="1",
                 LOT05J10D_SOURCE_ROOT=str(self.root),LOT05J10D_OWNER=claims["owner"],
                 LOT05J10D_JOB=claims["job"],LOT05J10D_GENERATION=claims["generation"],
                 LOT05J10D_MANIFEST=claims["manifest"])
        process=subprocess.run(["pwsh","-NoProfile","-File",str(script)],
                                capture_output=True,text=True,timeout=180,env=env)
        proof=process.stdout+"\\n"+process.stderr
        self.assertEqual(process.returncode,0,proof[-5000:])
        for marker in (
           "J10D_SCM_ISSUED_TICKET_AND_PIN_ACL_PROTECTED",
           "J10D_REAL_ISSUER_TICKET_VERIFIED_IN_INSTALLED_SCM_CONSUMER_DENY_ONLY_PASS",
           "J10D_ACTUAL_SCM_RESTART_REPLAY_DENIED_PASS",
           "J10D_REAL_SCM_TAMPER_DENIED_PASS",
           "J10D_SAME_ACCOUNT_OTHER_SERVICE_SID_CANNOT_READ_PIN_OR_WRITE_LEDGER_PASS",
           "J10D_NO_CLINICAL_APPLY_PASS"):
            self.assertIn(marker,proof)
        ledger=self.root/"j10d-consumer-synthetic-ledger"
        ledger.mkdir()
        scope=dict(owner=int(claims["owner"]),job=claims["job"],
                   generation=claims["generation"],manifest=claims["manifest"],ledger_dir=ledger)
        self.assertEqual(verify_and_burn(ticket,pin,**scope),
                         "DENY_J10D_SIGNED_NONCE_BURNED")
        with self.assertRaisesRegex(SignedReplayDenied,"NONCE_REPLAY"):
            verify_and_burn(ticket,pin,**scope)
        tampered=dict(ticket,body=ticket["body"].replace("manifest="+claims["manifest"],
                                                        "manifest="+("f"*64)))
        with self.assertRaises(SignedReplayDenied):
            verify_and_burn(tampered,pin,**scope)
        print("J10D_J10C_REAL_SCM_RSA_TO_DENY_ONLY_VERIFIER_PASS")

if __name__=="__main__":
    unittest.main(verbosity=2)
