"""LOT06 B05-B disposable Windows signed package admission test. Not product."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

SCHEMA = "DC06_B05B_LAB_PACKAGE_V1"
MANIFEST = "b05b-manifest.json"
SIGNATURE = "b05b-manifest.sig"


def guard(root: Path) -> Path:
    if (
        os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true"
        or os.environ.get("RUNNER_OS") != "Windows"
        or os.environ.get("ENVIRONMENT") != "test"
        or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
        or os.environ.get("DC06B05B_SIGNED_PACKAGE_LAB") != "1"
    ):
        raise ValueError("DC06B05B_HOSTED_WINDOWS_ONLY")
    temp = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    stage = root.resolve(strict=True)
    if not stage.is_relative_to(temp) or not stage.name.startswith("DC06B05B-LAB-"):
        raise ValueError("DC06B05B_STAGE_NOT_DISPOSABLE")
    return stage


def digest(path: Path) -> dict:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
            size += len(block)
    return {"size": size, "sha256": h.hexdigest()}


def inventory(stage: Path) -> list[dict]:
    entries = []
    for path in stage.rglob("*"):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError("DC06B05B_REPARSE_DENIED")
        if path.is_dir():
            continue
        if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
            raise ValueError("DC06B05B_NONREGULAR_FILE")
        relative = path.relative_to(stage).as_posix()
        if relative in (MANIFEST, SIGNATURE):
            continue
        if relative.startswith("/") or ".." in Path(relative).parts or "\\" in relative:
            raise ValueError("DC06B05B_BAD_RELATIVE_PATH")
        if not path.resolve(strict=True).is_relative_to(stage):
            raise ValueError("DC06B05B_PATH_ESCAPE")
        entries.append({"path": relative, **digest(path)})
    entries.sort(key=lambda item: item["path"])
    names = {item["path"] for item in entries}
    if len(names) != len(entries):
        raise ValueError("DC06B05B_DUPLICATE")
    required = {
        "ScmPipeFixture.exe",
        "scm_spool_read_b03.py",
        "tools/imaging_gateway/gateway.py",
        "tools/imaging_gateway/windows_scoped_read_lab.py",
    }
    if not required.issubset(names):
        raise ValueError("DC06B05B_PACKAGE_INCOMPLETE")
    if any(n.endswith((".pem", ".key", ".pfx")) for n in names):
        raise ValueError("DC06B05B_PRIVATE_KEY_IN_PACKAGE")
    return entries


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def verify(stage: Path, trusted_key: bytes, minimum_generation: int = 1) -> None:
    if len(trusted_key) != 32:
        raise ValueError("DC06B05B_BAD_PUBLIC_KEY")
    message = (stage / MANIFEST).read_bytes()
    signature = (stage / SIGNATURE).read_bytes()
    if len(message) > 2000000 or len(signature) != 64:
        raise ValueError("DC06B05B_BAD_MANIFEST_LENGTH")
    Ed25519PublicKey.from_public_bytes(trusted_key).verify(signature, message)
    document = json.loads(message)
    if (
        type(document) is not dict
        or set(document) != {"schema", "generation", "entries"}
        or document["schema"] != SCHEMA
        or type(document["generation"]) is not int
        or document["generation"] < minimum_generation
        or type(document["entries"]) is not list
        or message != canonical(document)
    ):
        raise ValueError("DC06B05B_MANIFEST_REJECTED")
    if document["entries"] != inventory(stage):
        raise ValueError("DC06B05B_FILESET_OR_DIGEST_MISMATCH")


def expect_denial(label: str, action) -> None:
    try:
        action()
    except (InvalidSignature, ValueError, OSError, json.JSONDecodeError):
        print("DC06B05B_" + label + "_FAIL_CLOSED_PASS")
        return
    raise AssertionError("DC06B05B_UNEXPECTED_ACCEPT_" + label)


def flip(path: Path, action) -> None:
    with path.open("r+b") as stream:
        first = stream.read(1)
        if not first:
            raise AssertionError("DC06B05B_EMPTY_FILE")
        stream.seek(0)
        stream.write(bytes([first[0] ^ 1]))
    try:
        action()
    finally:
        with path.open("r+b") as stream:
            stream.write(first)


def exercise(stage: Path) -> None:
    stage = guard(stage)
    if (stage / MANIFEST).exists() or (stage / SIGNATURE).exists():
        raise ValueError("DC06B05B_ATTESTATION_ALREADY_EXISTS")
    signer = Ed25519PrivateKey.generate()
    pinned = signer.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    record = {"schema": SCHEMA, "generation": 1, "entries": inventory(stage)}
    message = canonical(record)
    (stage / MANIFEST).write_bytes(message)
    (stage / SIGNATURE).write_bytes(signer.sign(message))
    del signer  # Private key never persisted; trust pin is outside package.
    good = lambda: verify(stage, pinned)
    good()
    print("DC06B05B_SELF_CONTAINED_DOTNET_AND_HELPER_ED25519_MANIFEST_PASS")
    flip(stage / "ScmPipeFixture.exe", lambda: expect_denial("SERVICE_EXE_TAMPER", good))
    flip(stage / "scm_spool_read_b03.py", lambda: expect_denial("HELPER_TAMPER", good))
    flip(stage / MANIFEST, lambda: expect_denial("MANIFEST_TAMPER", good))
    flip(stage / SIGNATURE, lambda: expect_denial("SIGNATURE_TAMPER", good))
    extra = stage / "unsigned-extra.ps1"
    try:
        extra.write_text("synthetic\n", encoding="ascii")
        expect_denial("EXTRA_FILE", good)
    finally:
        extra.unlink(missing_ok=True)
    helper = stage / "scm_spool_read_b03.py"
    snapshot = helper.read_bytes()
    try:
        helper.unlink()
        expect_denial("MISSING_FILE", good)
    finally:
        helper.write_bytes(snapshot)
    fake_public = Ed25519PrivateKey.generate().public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    expect_denial("WRONG_TRUST_ANCHOR", lambda: verify(stage, fake_public))
    expect_denial("GENERATION_DOWNGRADE", lambda: verify(stage, pinned, 2))
    good()
    print("DC06B05B_RESTORED_SIGNED_PACKAGE_STILL_VALID_PASS")
    print("DC06B05B_EPHEMERAL_SIGNATURE_NOT_CLINICAL_AUTHORITY_PASS")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] != "exercise":
        raise SystemExit(4)
    exercise(Path(sys.argv[2]))
