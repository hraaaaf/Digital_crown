"""LOT08.2-F SOURCE-ONLY activation contract; cannot authorize an installer.

This reads two repository text files. It DOES NOT execute run.py, install a
service, initialize cabinets, read configuration, decrypt SQLCipher or launch
any production process. Windows user/ACL and cold restore are separate CI LABs.
"""
from __future__ import annotations

import ast
from pathlib import Path
import re


class ActivationContractError(RuntimeError):
    """Fail closed on unexpected source activation behavior."""


REQUIRED_RELEASE_PROOFS = (
    "release-certification.json",
    ".digitalcrown-release-sha",
    "release-content.sha256",
    "installable-certification.json",
    "runtime-assets-certification.json",
    "runtime-assets-content.sha256",
    "github-attestation-verification.json",
)


def _section(source: str, name: str) -> str:
    sections = list(re.finditer(r"(?m)^\[([A-Za-z]+)\]\s*$", source))
    for i, entry in enumerate(sections):
        if entry.group(1).lower() == name.lower():
            end = sections[i + 1].start() if i + 1 < len(sections) else len(source)
            return source[entry.end():end]
    raise ActivationContractError("SOURCE_SECTION_MISSING_" + name.upper())


def _directives(source: str, section: str) -> list[str]:
    return [line.strip() for line in _section(source, section).splitlines()
            if line.strip() and not line.lstrip().startswith(";")]


def validate_source_contract(installer: str, launcher: str) -> dict:
    setup = _directives(installer, "Setup")
    expected = ("PrivilegesRequired=lowest", "CloseApplications=no", "RestartApplications=no")
    if any(required not in setup for required in expected):
        raise ActivationContractError("INSTALLER_USER_SCOPE_GUARD_MISSING")
    if "DefaultDirName={localappdata}" not in installer:
        raise ActivationContractError("INSTALLER_LOCALAPPDATA_GUARD_MISSING")
    if any(_directives(installer, name) for name in ("Run", "UninstallRun", "Icons")):
        raise ActivationContractError("INSTALLER_IMPLICIT_ACTIVATION_FORBIDDEN")
    for name in REQUIRED_RELEASE_PROOFS:
        if not re.search(r"#if\s+!FileExists\([^\n]*" + re.escape(name), installer):
            raise ActivationContractError("INSTALLABLE_PROOF_GUARD_MISSING")
    if "AppId=DigitalCrown-{#CabinetInstanceId}" not in installer:
        raise ActivationContractError("ISOLATED_INSTANCE_NAMESPACE_MISSING")

    tree = ast.parse(launcher)
    funcs = {x.name: x for x in tree.body if isinstance(x, ast.FunctionDef)}
    needed = ("_verify_frozen_release_certification", "_select_cabinet_env_profile",
              "_first_boot_bootstrap", "_load_launcher_environment")
    if any(name not in funcs for name in needed):
        raise ActivationContractError("LAUNCH_GUARDS_MISSING")
    for name in (
        "verify_installable_release_identity(bundle_root)",
        'os.environ["DIGITALCROWN_ENV_FILE"]',
        '"--initialize-new-cabinet"',
        "os.O_EXCL",
        "New cabinet requires five explicit absolute isolated paths",
    ):
        if name not in launcher:
            raise ActivationContractError("LAUNCH_FAIL_CLOSED_MARKER_MISSING")

    def called(stmt):
        return stmt.value.func.id if (
            isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Name)
        ) else None

    top_calls = [called(stmt) for stmt in tree.body]
    order = ["_verify_frozen_release_certification", "_select_cabinet_env_profile",
             "_first_boot_bootstrap", "_setup_frozen_logging", "_maybe_run_guided_restore_worker"]
    try:
        positions = [top_calls.index(name) for name in order]
    except ValueError as exc:
        raise ActivationContractError("LAUNCH_TOP_LEVEL_GUARD_MISSING") from exc
    if positions != sorted(positions):
        raise ActivationContractError("LAUNCH_GUARD_ORDER_CHANGED")
    # A packaged process loads the selected env before any logging.
    if not re.search(
        r'if getattr\(sys, "frozen", False\):\s+_load_launcher_environment\(\)\s+_setup_frozen_logging\(\)',
        launcher,
    ):
        raise ActivationContractError("FROZEN_PROFILE_LOAD_ORDER_CHANGED")

    # This is explicitly NOT a certificate for any actual runtime.
    return {
        "contract": "LOT08.2-F-USER-EXPLICIT-PROFILE-SOURCE-ONLY",
        "seven_installable_proof_guards_present": True,
        "per_user_installer_scope": True,
        "no_auto_launch_task_service_or_shortcut_in_installer": True,
        "release_identity_precedes_profile_and_configuration": True,
        "explicit_absolute_profile_and_new_cabinet_only": True,
        "actual_packaged_binary_executed": False,
        "cabinet_data_touched": False,
        "clinical_go": False,
        "installable_certified": False,
    }


def validate_repository(root: Path) -> dict:
    root = Path(root)
    for part in ("installer/DigitalCrown.iss", "run.py"):
        p = root / part
        if not p.is_file() or p.is_symlink():
            raise ActivationContractError("SOURCE_FILE_MISSING_OR_SYMLINK")
    return validate_source_contract(
        (root / "installer/DigitalCrown.iss").read_text(encoding="utf-8"),
        (root / "run.py").read_text(encoding="utf-8"),
    )
