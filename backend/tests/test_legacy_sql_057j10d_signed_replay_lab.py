"""Synthetic RSA fixture is format-compatible with actual J10C issuer, not an SCM integration test."""
import base64
import concurrent.futures
import importlib.util
from pathlib import Path
import tempfile
import unittest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

p = Path(__file__).parent / "fixtures" / "lot05j10d_signed_replay_lab.py"
s = importlib.util.spec_from_file_location("j10d_signed_replay", p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
OWNER, JOB, GEN, MAN = 17, "a"*32, "g_"+"b"*32, "c"*64
NOW = 100000

class SignedReplayLab(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ledger = Path(self.temp.name)/"protected-consumer-ledger"
        self.ledger.mkdir()
        self.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        numbers = self.key.public_key().public_numbers()
        self.pin = "\n".join((base64.b64encode(numbers.n.to_bytes(256,"big")).decode(),
          base64.b64encode(numbers.e.to_bytes(3,"big")).decode(),str(OWNER)))+"\n"
        self.ticket = self.sign()

    def sign(self, *, nonce="d"*32, expires=NOW+30, job=JOB):
        body=f"owner={OWNER}|audience={m.AUDIENCE}|job={job}|generation={GEN}|manifest={MAN}|nonce={nonce}|expires={expires}"
        signature=self.key.sign(body.encode("ascii"),padding.PKCS1v15(),hashes.SHA256())
        return {"body":body,"signature":base64.b64encode(signature).decode("ascii"),"signer_pid":123}

    def burn(self, ticket=None, **kw):
        args=dict(owner=OWNER,job=JOB,generation=GEN,manifest=MAN,ledger_dir=self.ledger,now=NOW)
        args.update(kw)
        return m.verify_and_burn(self.ticket if ticket is None else ticket,self.pin,**args)

    def test_valid_signature_is_still_deny_only(self):
        self.assertEqual(self.burn(),"DENY_J10D_SIGNED_NONCE_BURNED")
        self.assertEqual(list(self.ledger.glob("*.nonce"))[0].stat().st_size,64)
        self.assertFalse(hasattr(m,"apply_restore"))

    def test_replay_remains_denied_after_new_call(self):
        self.burn()
        with self.assertRaisesRegex(m.SignedReplayDenied,"NONCE_REPLAY"):
            self.burn()

    def test_wrong_scope_denied_without_burn(self):
        for kw in (dict(owner=18),dict(job="e"*32),dict(generation="g_"+"f"*32),dict(manifest="e"*64)):
            with self.subTest(kw=kw), self.assertRaises(m.SignedReplayDenied): self.burn(**kw)
        self.assertEqual(list(self.ledger.iterdir()),[])

    def test_tampering_denied_before_nonce(self):
        ticket=dict(self.ticket)
        ticket["body"]=ticket["body"].replace("nonce="+"d"*32,"nonce="+"e"*32)
        with self.assertRaisesRegex(m.SignedReplayDenied,"SIGNED_RSA_DENY"):
            self.burn(ticket)
        self.assertEqual(list(self.ledger.iterdir()),[])

    def test_expiration_denied(self):
        for expiry in (NOW,NOW-100,NOW+91):
            with self.subTest(expiry=expiry),self.assertRaisesRegex(m.SignedReplayDenied,"SIGNED_EXPIRED"):
                self.burn(self.sign(expires=expiry))

    def test_wrong_trust_pin_denied(self):
        self.pin=self.pin.replace("\n17\n","\n18\n")
        with self.assertRaises(m.SignedReplayDenied): self.burn()
        self.assertEqual(list(self.ledger.iterdir()),[])

    def test_ledger_missing_or_symlink_denies(self):
        self.ledger.rmdir()
        with self.assertRaises(m.SignedReplayDenied): self.burn()
        try:
            self.ledger.symlink_to(self.temp.name, target_is_directory=True)
        except OSError:
            # Windows runner can lack symlink creation privilege. No reparse proof.
            return
        with self.assertRaisesRegex(m.SignedReplayDenied,"LEDGER_DIRECTORY"): self.burn()

    def test_concurrent_same_nonce_burn_one_only(self):
        def one(_):
            try: return self.burn()
            except m.SignedReplayDenied as e: return str(e)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            result=list(ex.map(one,range(6)))
        self.assertEqual(result.count("DENY_J10D_SIGNED_NONCE_BURNED"),1)
        self.assertEqual(result.count("NONCE_REPLAY"),5)

    def test_malformed_signature_and_pin_denied(self):
        t=dict(self.ticket,signature="!!")
        with self.assertRaises(m.SignedReplayDenied): self.burn(t)
        self.pin="NOT_A_TRUSTED_PIN"
        with self.assertRaises(m.SignedReplayDenied): self.burn()
        self.assertEqual(list(self.ledger.iterdir()),[])

if __name__=="__main__": unittest.main()
