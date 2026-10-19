"""J10D test-only IPC parser negative contract; NOT SCM/pipe certification."""
import json
import unittest
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("j10d_fake_ipc", Path(__file__).parent / "fixtures" / "lot05j10d_fake_ipc_envelope.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
IpcDenied, PURPOSE, parse_frame = module.IpcDenied, module.PURPOSE, module.parse_frame
OWNER = 17
JOB = "a" * 32
GEN = "g_" + "b" * 32
MANIFEST = "c" * 64
NOW = 100000
BASE = dict(purpose=PURPOSE, owner=OWNER, job=JOB, generation=GEN,
            manifest=MANIFEST, nonce="d" * 32, expires=NOW + 30)

def encoded(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")

def check(raw, **overrides):
    args=dict(expected_owner=OWNER, expected_job=JOB,
              expected_generation=GEN, expected_manifest=MANIFEST, now=NOW)
    args.update(overrides)
    return parse_frame(raw, **args)

class J10DIpcEnvelope(unittest.TestCase):
    def test_valid_synthetic_frame(self):
        self.assertEqual(check(encoded(BASE))["job"], JOB)

    def test_cross_owner_and_job_denied(self):
        for field, value in (("owner", 18), ("job", "e"*32)):
            with self.subTest(field=field), self.assertRaises(IpcDenied):
                check(encoded(dict(BASE, **{field: value})))

    def test_stale_generation_and_manifest_denied(self):
        for field, value in (("generation", "g_"+"e"*32), ("manifest", "e"*64)):
            with self.subTest(field=field), self.assertRaises(IpcDenied):
                check(encoded(dict(BASE, **{field: value})))

    def test_expiry_denied(self):
        for expires in (NOW, NOW-1, NOW+91, True, "100001"):
            with self.subTest(expires=expires), self.assertRaises(IpcDenied):
                check(encoded(dict(BASE, expires=expires)))

    def test_nonce_and_purpose_denied(self):
        for field, value in (("nonce", "bad"), ("purpose", "CLINICAL_APPLY")):
            with self.subTest(field=field), self.assertRaises(IpcDenied):
                check(encoded(dict(BASE, **{field: value})))

    def test_duplicate_key_denied(self):
        raw=encoded(BASE).replace(b'"owner":17', b'"owner":17,"owner":17')
        with self.assertRaises(IpcDenied):
            check(raw)

    def test_noncanonical_and_extra_fields_denied(self):
        with self.assertRaises(IpcDenied):
            check(json.dumps(BASE).encode())
        with self.assertRaises(IpcDenied):
            check(encoded(dict(BASE, clinical_restore=True)))

    def test_invalid_utf8_and_oversize_denied(self):
        for raw in (b"\\xff", b"x"*1025, b"", "text", b"[]"):
            with self.subTest(raw=str(raw)[:20]), self.assertRaises(IpcDenied):
                check(raw)

    def test_boolean_owner_denied(self):
        with self.assertRaises(IpcDenied):
            check(encoded(dict(BASE, owner=True)))

    def test_no_transport_authorization(self):
        # No worker, IPC endpoint, peer credential or restore action exists here.
        self.assertFalse(hasattr(module, "apply_restore"))

if __name__ == "__main__":
    unittest.main()
