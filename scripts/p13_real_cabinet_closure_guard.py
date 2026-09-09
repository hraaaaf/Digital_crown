from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
P13_SCRIPT = HERE / "p13_real_cabinet_evidence.py"
SPEC = importlib.util.spec_from_file_location("p13_real_cabinet_evidence", P13_SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {P13_SCRIPT}")
p13 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p13)

SCHEMA = "digital-crown-p13-context-v1"
EXECUTION_CONTEXTS = {"cabinet_local", "remote_bare_metal_rehearsal"}
OFF_MACHINE_KINDS = {"usb", "removable", "nas", "independent_network_storage"}
WINDOWS_FINAL_KINDS = {"usb", "removable", "nas"}


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))


def _by_platform(documents: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    windows = None
    macos = None
    for document in documents:
        platform_name = document.get("machine", {}).get("platform") if isinstance(document.get("machine"), dict) else None
        if platform_name == "Windows":
            windows = document
        elif platform_name == "Darwin":
            macos = document
    return windows, macos


def _validate_destination(label: str, entry: Any, allowed_kinds: set[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(entry, dict):
        return [f"{label}.dr_destination must be an object"]
    kind = entry.get("kind")
    if kind not in allowed_kinds:
        errors.append(f"{label}.dr_destination.kind must be one of {sorted(allowed_kinds)}, got {kind!r}")
    if not str(entry.get("description", "")).strip():
        errors.append(f"{label}.dr_destination.description is required")
    if entry.get("source_machine_independent") is not True:
        errors.append(f"{label}.dr_destination.source_machine_independent must be true")
    return errors


def _validate_remote_bare_metal(label: str, entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not str(entry.get("provider", "")).strip():
        errors.append(f"{label}.provider is required for remote bare-metal rehearsal")
    instance_type = str(entry.get("instance_type", "")).strip()
    if not instance_type:
        errors.append(f"{label}.instance_type is required for remote bare-metal rehearsal")
    elif not instance_type.lower().endswith(".metal"):
        errors.append(f"{label}.instance_type must identify a bare-metal instance ending in .metal")
    return errors


def validate_context(context: dict[str, Any], *, closure: bool, windows_doc: dict[str, Any], macos_doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if context.get("schema") != SCHEMA:
        errors.append(f"context.schema must be {SCHEMA}")

    for label in ("windows", "macos"):
        entry = context.get(label)
        if not isinstance(entry, dict):
            errors.append(f"context.{label} must be an object")
            continue
        execution_context = entry.get("execution_context")
        if execution_context not in EXECUTION_CONTEXTS:
            errors.append(f"{label}.execution_context must be one of {sorted(EXECUTION_CONTEXTS)}")
        if entry.get("operator_attested") is not True:
            errors.append(f"{label}.operator_attested must be true")
        errors.extend(_validate_destination(label, entry.get("dr_destination"), OFF_MACHINE_KINDS))
        if execution_context == "remote_bare_metal_rehearsal":
            errors.extend(_validate_remote_bare_metal(label, entry))

    if closure:
        windows_ctx = context.get("windows") if isinstance(context.get("windows"), dict) else {}
        if windows_ctx.get("execution_context") != "cabinet_local":
            errors.append("final closure requires windows.execution_context=cabinet_local")
        errors.extend(_validate_destination("windows", windows_ctx.get("dr_destination"), WINDOWS_FINAL_KINDS))

        os_info = windows_doc.get("machine", {}).get("windows_os") if isinstance(windows_doc.get("machine"), dict) else None
        caption = str(os_info.get("Caption", "")) if isinstance(os_info, dict) else ""
        if "Windows 11" not in caption:
            errors.append(f"final closure requires a real Windows 11 cabinet target, got {caption!r}")

        mac_ctx = context.get("macos") if isinstance(context.get("macos"), dict) else {}
        if mac_ctx.get("execution_context") == "remote_bare_metal_rehearsal":
            architecture = str(macos_doc.get("machine", {}).get("architecture", "")).lower()
            if architecture not in {"arm64", "aarch64"}:
                errors.append(f"remote macOS closure evidence must be Apple Silicon architecture, got {architecture!r}")

    try:
        p13.assert_no_secrets(context)
    except SystemExit as exc:
        errors.append(str(exc))
    return errors


def validate_pair_with_context(first: dict[str, Any], second: dict[str, Any], context: dict[str, Any], *, closure: bool) -> list[str]:
    errors: list[str] = []
    documents = [first, second]
    for index, document in enumerate(documents, start=1):
        errors.extend(f"evidence[{index}]: {error}" for error in p13.validate_document(document, require_pass=True))

    windows, macos = _by_platform(documents)
    if windows is None or macos is None:
        errors.append("pair must contain exactly one Windows and one macOS evidence document")
        return errors

    release_ids = {str(first.get("release_id", "")), str(second.get("release_id", ""))}
    if len(release_ids) != 1 or "" in release_ids:
        errors.append("both evidence files must share the same non-empty release_id")

    errors.extend(validate_context(context, closure=closure, windows_doc=windows, macos_doc=macos))
    return errors


def run_validation(args: argparse.Namespace, *, closure: bool) -> int:
    first = _load(args.first)
    second = _load(args.second)
    context = _load(args.context)
    errors = validate_pair_with_context(first, second, context, closure=closure)
    if errors:
        prefix = "P13_CLOSURE_GUARD_ERROR" if closure else "P13_REHEARSAL_ERROR"
        for error in errors:
            print(f"{prefix}={error}", file=sys.stderr)
        return 2
    release_id = str(first.get("release_id", ""))
    if closure:
        print(f"P13_CLOSURE_GUARD_VALID=PASS_ATTESTED release_id={release_id}")
    else:
        print(f"P13_REMOTE_BARE_METAL_REHEARSAL_VALID=PASS_ATTESTED release_id={release_id}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Guard P13 rehearsal versus final real-cabinet closure evidence.")
    sub = root.add_subparsers(dest="command", required=True)
    for name, closure in (("validate-rehearsal", False), ("validate-closure", True)):
        p = sub.add_parser(name)
        p.add_argument("--first", required=True)
        p.add_argument("--second", required=True)
        p.add_argument("--context", required=True)
        p.set_defaults(func=lambda args, closure=closure: run_validation(args, closure=closure))
    return root


def main() -> int:
    args = parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
