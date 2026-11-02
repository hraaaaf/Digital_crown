"""LOT06 B05-C1: synthetic package admission before disposable Windows SCM start.

LAB only. This does NOT constitute Authenticode, installer, TPM attestation, or
an SCM-enforced gate against administrator-initiated direct sc.exe starts.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# Reuse the parent B05-B manifest algorithm; do not create a competing schema.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from b05b_signed_package_lab import MANIFEST, SIGNATURE, SCHEMA, canonical, inventory, verify


def _check(stage: Path, pin: Path) -> tuple[Path, Path]:
    environment = {
        "GITHUB_ACTIONS": "true",
        "RUNNER_OS": "Windows",
        "ENVIRONMENT": "test",
        "DIGITALCROWN_ISOLATED_RUNTIME": "true",
        "DC06B05C1_LAB": "1",
    }
    if os.name != "nt" or any(os.environ.get(k) != v for k, v in environment.items()):
        raise ValueError("DC06B05C1_NON_LAB_ENVIRONMENT")
    program_data = Path(os.environ["ProgramData"]).resolve(strict=True)
    runner_temp = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    stage = stage.resolve(strict=True)
    # Stage is a disposable DIRECT child of ProgramData, never a clinic folder.
    if stage.parent != program_data or not stage.name.startswith("DC06B05C-LAB-"):
        raise ValueError("DC06B05C1_UNSAFE_STAGE")
    # The test pin must be outside the package, in the disposable runner temp.
    if pin.parent.resolve(strict=True) != runner_temp or not pin.name.startswith("DC06B05C-pub-"):
        raise ValueError("DC06B05C1_UNSAFE_TRUST_PIN")
    if pin.is_symlink() or getattr(pin, "is_junction", lambda: False)():
        raise ValueError("DC06B05C1_REPARSE_PIN_DENIED")
    return stage, pin


def seal(stage: Path, pin: Path) -> None:
    stage, pin = _check(stage, pin)
    if pin.exists() or (stage / MANIFEST).exists() or (stage / SIGNATURE).exists():
        raise ValueError("DC06B05C1_ALREADY_SEALED")
    signer = Ed25519PrivateKey.generate()
    record = {"schema": SCHEMA, "generation": 1, "entries": inventory(stage)}
    message = canonical(record)
    public_key = signer.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    (stage / MANIFEST).write_bytes(message)
    (stage / SIGNATURE).write_bytes(signer.sign(message))
    pin.write_bytes(public_key)
    del signer
    verify(stage, public_key, minimum_generation=1)
    print("DC06B05C1_EPHEMERAL_ED25519_SEAL_OUTSIDE_TRUST_PIN_PASS")


def admit(stage: Path, pin: Path, generation: int) -> None:
    stage, pin = _check(stage, pin)
    # No arbitrary certificate or public key may be read from stage.
    if generation < 1 or generation > 65535:
        raise ValueError("DC06B05C1_BAD_GENERATION")
    pinned = pin.read_bytes()
    verify(stage, pinned, minimum_generation=generation)
    print("DC06B05C1_VERIFIED_SAME_PACKAGE_BEFORE_SCM_START_PASS")


def main(args: list[str]) -> int:
    if len(args) not in (3, 4) or args[0] not in ("seal", "verify"):
        return 4
    try:
        if args[0] == "seal" and len(args) == 3:
            seal(Path(args[1]), Path(args[2]))
        elif args[0] == "verify" and len(args) == 4:
            admit(Path(args[1]), Path(args[2]), int(args[3]))
        else:
            return 4
    except Exception:
        # Strictly fixed code; never print keys, filenames, file hashes or paths.
        print("DC06B05C1_ADMISSION_FAIL_CLOSED")
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
