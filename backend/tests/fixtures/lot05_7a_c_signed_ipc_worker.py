"""LOT05.7A-C disposable Windows SCM signed-ticket verifier subprocess.

This fixture is called ONLY by a CI Windows ServiceBase test service. It
does not install/provision the product, mint keys, enable imports or open SQL.
The service supplies its ACL-protected fixture config, NOT a requester's pin.
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


class DisposableNonceLedger:
    """Atomic temp-tree nonce gate; NOT certified anti-rollback storage."""

    def __init__(self, root: Path):
        self.root = root

    def consume_once(self, namespace: str, nonce: str) -> bool:
        if not self.root.is_dir() or self.root.is_symlink():
            raise RuntimeError("LEDGER_ROOT_INVALID")
        key = hashlib.sha256((namespace + ":" + nonce).encode("ascii")).hexdigest()
        dest = self.root / (key + ".consumed")
        fd = os.open(str(dest), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            with os.fdopen(fd, "wb") as out:
                out.write(b"LOT05C_SYNTHETIC_ONLY\n")
                out.flush()
                os.fsync(out.fileno())
        except BaseException:
            raise
        return True


def main() -> int:
    if os.getenv("LOT05_7A_C_FAKE_ONLY") != "1" or len(sys.argv) != 4:
        return 61
    config_path, ledger_path, verifier_path = map(Path, sys.argv[1:])
    if (not config_path.is_file() or config_path.is_symlink()
            or not ledger_path.is_dir() or ledger_path.is_symlink()
            or not verifier_path.is_file() or verifier_path.is_symlink()):
        return 62
    config_bytes = config_path.read_bytes()
    if len(config_bytes) > 4096:
        return 63
    cfg = json.loads(config_bytes.decode("utf-8"))
    if type(cfg) is not dict or set(cfg) != {"provisioned", "expected"}:
        return 64

    module_spec = importlib.util.spec_from_file_location("_lot05c_auth_verifier", str(verifier_path))
    if module_spec is None or module_spec.loader is None:
        return 65
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)

    verifier_options = dict(cfg["provisioned"])
    encoded_public = verifier_options.pop("public_key_raw_b64")
    verifier_options["public_key_raw"] = base64.b64decode(encoded_public, validate=True)
    provisioned = module.ProvisionedVerifier(**verifier_options)
    expected = module.ExpectedSyntheticContext(**cfg["expected"])
    request = sys.stdin.buffer.readline(8193)
    if not request.endswith(b"\n") or len(request) > 8192:
        return 66
    request = request[:-1]
    receipt = module.verify_synthetic_noop_ticket(
        request, provisioned=provisioned, expected=expected,
        now_epoch=int(time.time()), replay_ledger=DisposableNonceLedger(ledger_path))
    if receipt.verified_noop and receipt.clinical_import_permitted is False:
        sys.stdout.write("ALLOW_SYNTHETIC_NOOP_ONLY\n")
        sys.stdout.flush()
        return 0
    return 67


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FileExistsError:
        print("DENY_REPLAY", file=sys.stderr)
        sys.exit(71)
    except Exception as exc:
        # Never leak config, ticket, payload, token, private material to stdout.
        print("DENY_" + type(exc).__name__, file=sys.stderr)
        sys.exit(72)
