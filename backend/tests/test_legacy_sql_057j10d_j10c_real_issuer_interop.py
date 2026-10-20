"""J10D interoperability: ticket issued by actual J10C Windows SCM signer.
No clinical restore; this is NOT an installed SCM consumer proof.
"""
import json
import unittest
from backend.tests.test_legacy_sql_057j10c_real_scm_bound_sqlcipher_lab import ConnectedJ10C
from backend.tests.fixtures.lot05j10d_signed_replay_lab import verify_and_burn, SignedReplayDenied

class RealIssuerToVerifier(ConnectedJ10C):
    def test_01_actual_scm_jwt_rsa_job_manifest_sqlcipher_copy(self):
        super().test_01_actual_scm_jwt_rsa_job_manifest_sqlcipher_copy()
        ticket=json.loads((self.root/"isolated-signed.json").read_text(encoding="utf-8-sig"))
        pin=(self.root/"trusted-rsa-public.fake").read_text(encoding="ascii")
        claims=dict(segment.split("=",1) for segment in ticket["body"].split("|"))
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
