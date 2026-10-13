"""Versioned Pocket read capabilities; resource guards remain authoritative.

Staff permissions come from the existing Settings policy. Patient capabilities
are constructed only after resolving an authorized Companion context.
"""
from backend.routers.auth import has_permission


def _contract(kind: str, grants: dict[str, bool], scope: str) -> dict:
    return {
        "version": 1,
        "principal_kind": kind,
        "capabilities": {
            action: {
                "allowed": allowed,
                "scope": scope if allowed else None,
                "reason": None if allowed else "not_authorized",
            }
            for action, allowed in grants.items()
        },
    }


def staff_read_capabilities(user) -> dict:
    patients = has_permission(user, "patients")
    return _contract("staff", {
        "agenda.read": has_permission(user, "agenda"),
        "cabinet.patients.read": patients,
        "cabinet.clinical.read": patients and has_permission(user, "clinical"),
        "cabinet.finance.read": has_permission(user, ["accounting", "payments"]),
        # Shared resources use the patient-context adapter, not the staff API.
        "shares.read": False,
    }, "cabinet")


def patient_read_capabilities() -> dict:
    return _contract("patient", {
        "agenda.read": True,
        "cabinet.patients.read": False,
        "cabinet.clinical.read": False,
        "cabinet.finance.read": False,
        "shares.read": True,
    }, "patient_context")
