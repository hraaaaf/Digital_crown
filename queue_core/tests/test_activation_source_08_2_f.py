"""LOT08.2-F source contract and negative gates; no installable executed."""
from pathlib import Path

import pytest

from scripts.quality.lot08_2_f_activation_source_lab import (
    ActivationContractError,
    validate_repository,
    validate_source_contract,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sources():
    return (
        (ROOT / "installer" / "DigitalCrown.iss").read_text(encoding="utf-8"),
        (ROOT / "run.py").read_text(encoding="utf-8"),
    )


def test_current_installer_and_launcher_explicit_user_profile(sources):
    result = validate_source_contract(*sources)
    assert validate_repository(ROOT) == result
    assert result["per_user_installer_scope"]
    assert result["no_auto_launch_task_service_or_shortcut_in_installer"]
    assert result["release_identity_precedes_profile_and_configuration"]
    assert result["actual_packaged_binary_executed"] is False
    assert result["installable_certified"] is False
    assert result["clinical_go"] is False


@pytest.mark.parametrize(
    "section,directive",
    [
        ("Run", 'Filename: "{app}\\DigitalCrown.exe"'),
        ("Icons", 'Name: "{group}\\DigitalCrown"; Filename: "{app}\\DigitalCrown.exe"'),
        ("UninstallRun", 'Filename: "schtasks"; Parameters: "/delete"'),
    ],
)
def test_installer_implicit_activation_is_denied(sources, section, directive):
    installer, launcher = sources
    injected = installer.replace("[" + section + "]\n", "[" + section + "]\n" + directive + "\n", 1)
    assert injected != installer
    with pytest.raises(ActivationContractError, match="INSTALLER_IMPLICIT_ACTIVATION_FORBIDDEN"):
        validate_source_contract(injected, launcher)


def test_admin_privilege_escalation_is_denied(sources):
    installer, launcher = sources
    with pytest.raises(ActivationContractError, match="INSTALLER_USER_SCOPE_GUARD_MISSING"):
        validate_source_contract(installer.replace("PrivilegesRequired=lowest", "PrivilegesRequired=admin"), launcher)


def test_missing_installable_manifest_guard_is_denied(sources):
    installer, launcher = sources
    injected = installer.replace(
        '#if !FileExists(MyBundledProofDir + "\\installable-certification.json")',
        '#if FileExists(MyBundledProofDir + "\\installable-certification.json")',
    )
    assert injected != installer
    with pytest.raises(ActivationContractError, match="INSTALLABLE_PROOF_GUARD_MISSING"):
        validate_source_contract(injected, launcher)


def test_launcher_reordered_identity_check_is_denied(sources):
    installer, launcher = sources
    original = "_verify_frozen_release_certification()\n_select_cabinet_env_profile()\n_first_boot_bootstrap()"
    swapped = "_select_cabinet_env_profile()\n_verify_frozen_release_certification()\n_first_boot_bootstrap()"
    assert original in launcher
    with pytest.raises(ActivationContractError, match="LAUNCH_GUARD_ORDER_CHANGED"):
        validate_source_contract(installer, launcher.replace(original, swapped, 1))


def test_no_implicit_frozen_environment_load(sources):
    installer, launcher = sources
    needle = 'if getattr(sys, "frozen", False):\n    _load_launcher_environment()\n_setup_frozen_logging()'
    assert needle in launcher
    with pytest.raises(ActivationContractError, match="FROZEN_PROFILE_LOAD_ORDER_CHANGED"):
        validate_source_contract(installer, launcher.replace(needle, "_setup_frozen_logging()", 1))


def test_missing_or_symlinked_sources_fail_closed(tmp_path):
    with pytest.raises(ActivationContractError, match="SOURCE_FILE_MISSING_OR_SYMLINK"):
        validate_repository(tmp_path)
