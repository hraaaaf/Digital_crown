"""04.8-B isolated tests: no API, printer, PDF or patient data."""
from dataclasses import replace

import pytest

from backend.services.station_document_print_configuration import (
    PrintConfigurationRejected,
    TrustedPrinter,
    TrustedStation,
    compile_owner_print_config,
    default_disabled_print_config,
)
from backend.services.station_document_print_policy import CabinetPrintPolicy


@pytest.fixture
def inventory():
    stations = {
        "station-a": TrustedStation("station-a", 10, "station"),
        "station-b": TrustedStation("station-b", 10, "station"),
        "foreign": TrustedStation("foreign", 20, "station"),
        "desk": TrustedStation("desk", 10, "cabinet"),
        "revoked": TrustedStation("revoked", 10, "station", revoked=True),
    }
    printers = {
        "reception-1": TrustedPrinter("reception-1", 10, "reception", enabled=True, staff_supervised=True),
        "near-1": TrustedPrinter(
            "near-1", 10, "near_station", station_id="station-a",
            enabled=True, secure_release_verified=True,
            private_channel_verified=True,
        ),
        "foreign-printer": TrustedPrinter("foreign-printer", 20, "reception", enabled=True, staff_supervised=True),
        "offline": TrustedPrinter("offline", 10, "reception", enabled=False, staff_supervised=True),
    }
    return stations, printers


def proposal(mode="disabled", station_ids=(), printer_ids=()):
    return {
        "schemaVersion": 1,
        "mode": mode,
        "stationIds": list(station_ids),
        "printerIds": list(printer_ids),
    }


def compile_config(inventory, raw, **overrides):
    stations, printers = inventory
    params = dict(
        tenant_id=10, actor_user_id=10, actor_employer_id=None,
        raw=raw, trusted_stations=stations, trusted_printers=printers,
    )
    params.update(overrides)
    return compile_owner_print_config(**params)


def test_disabled_is_default_and_has_no_devices(inventory):
    assert default_disabled_print_config(10) == CabinetPrintPolicy(tenant_id=10)
    assert compile_config(inventory, proposal()) == default_disabled_print_config(10)


@pytest.mark.parametrize("owner,employer", [
    (11, 10), (20, None), (10, 10), (0, None), (True, None),
])
def test_only_exact_cabinet_owner_may_compose_settings(inventory, owner, employer):
    with pytest.raises(PrintConfigurationRejected, match="OWNER_REQUIRED"):
        compile_config(inventory, proposal(), actor_user_id=owner, actor_employer_id=employer)


@pytest.mark.parametrize("invalid_tenant", [0, -1, True, "10", None])
def test_invalid_tenant_fails_closed(inventory, invalid_tenant):
    with pytest.raises(PrintConfigurationRejected, match="INVALID_TENANT"):
        compile_config(inventory, proposal(), tenant_id=invalid_tenant)
    with pytest.raises(PrintConfigurationRejected, match="INVALID_TENANT"):
        default_disabled_print_config(invalid_tenant)


@pytest.mark.parametrize("raw", [
    None, {}, [], "disabled",
    {"mode": "disabled", "stationIds": [], "printerIds": []},
    {**proposal(), "tenantId": 20},
    {**proposal(), "secureReleaseVerified": True},
    {**proposal(), "staffSupervised": True},
    {**proposal(), "pdfUrl": "/api/secret.pdf"},
    {**proposal(), "schemaVersion": 2},
    {**proposal(), "schemaVersion": True},
    {**proposal(), "mode": "ALL"},
    {**proposal(), "mode": None},
    proposal("disabled", ["station-a"], []),
    proposal("disabled", [], ["reception-1"]),
])
def test_unrecognized_client_fields_and_corrupt_settings_rejected(inventory, raw):
    with pytest.raises(PrintConfigurationRejected):
        compile_config(inventory, raw)


@pytest.mark.parametrize("station_ids", [
    [], ["unknown"], ["foreign"], ["desk"], ["revoked"],
    ["station-a", "station-a"], ["station-a|forgery"],
    [" station-a"], ["station-a", None], [123],
    ["station-a"] * 51,
])
def test_station_allowlist_is_exact_and_trusted(inventory, station_ids):
    with pytest.raises(PrintConfigurationRejected):
        compile_config(inventory, proposal("reception", station_ids, ["reception-1"]))


@pytest.mark.parametrize("printer_ids", [
    [], ["unknown"], ["foreign-printer"], ["offline"],
    ["reception-1", "reception-1"], ["near-1"], ["near-1", "reception-1"],
    [None], [22], ["reception|test"], ["reception-1"] * 51,
])
def test_reception_only_explicit_inventory_and_destination(inventory, printer_ids):
    with pytest.raises(PrintConfigurationRejected):
        compile_config(inventory, proposal("reception", ["station-a"], printer_ids))


def test_reception_creates_tenant_scoped_policy(inventory):
    value = compile_config(inventory, proposal("reception", ["station-a"], ["reception-1"]))
    assert value.tenant_id == 10
    assert value.mode == "reception"
    assert value.allowed_stations == ("station-a",)
    assert len(value.printers) == 1
    assert value.printers[0].tenant_id == 10
    assert value.printers[0].staff_supervised is True


def test_both_destinations_require_all_hardware_and_no_fallback(inventory):
    value = compile_config(inventory, proposal("both", ["station-a"], ["near-1", "reception-1"]))
    assert value.mode == "both"
    assert {p.location for p in value.printers} == {"near_station", "reception"}
    assert {p.printer_id for p in value.printers} == {"near-1", "reception-1"}

    for printers in (["near-1"], ["reception-1"]):
        with pytest.raises(PrintConfigurationRejected, match="DESTINATIONS_INCOMPLETE"):
            compile_config(inventory, proposal("both", ["station-a"], printers))


@pytest.mark.parametrize("change", [
    {"enabled": False},
    {"tenant_id": 99},
    {"secure_release_verified": False},
    {"private_channel_verified": False},
    {"station_id": "station-b"},
    {"location": "reception", "station_id": "station-a"},
])
def test_public_printer_requires_independent_verified_inventory(inventory, change):
    stations, printers = inventory
    forged = dict(printers, **{"near-1": replace(printers["near-1"], **change)})
    with pytest.raises(PrintConfigurationRejected):
        compile_config((stations, forged), proposal("near_station", ["station-a"], ["near-1"]))


def test_unsupervised_reception_never_becomes_eligible(inventory):
    stations, printers = inventory
    forged = dict(printers, **{"reception-1": replace(printers["reception-1"], staff_supervised=False)})
    with pytest.raises(PrintConfigurationRejected, match="RECEPTION_NOT_SUPERVISED"):
        compile_config((stations, forged), proposal("reception", ["station-a"], ["reception-1"]))


def test_inventory_key_id_mismatch_fails_closed(inventory):
    stations, printers = inventory
    forged_stations = dict(stations, **{"station-a": replace(stations["station-a"], station_id="foreign")})
    with pytest.raises(PrintConfigurationRejected, match="STATION_NOT_TRUSTED"):
        compile_config((forged_stations, printers), proposal("reception", ["station-a"], ["reception-1"]))
    forged_printers = dict(printers, **{"reception-1": replace(printers["reception-1"], printer_id="other")})
    with pytest.raises(PrintConfigurationRejected, match="PRINTER_NOT_TRUSTED"):
        compile_config((stations, forged_printers), proposal("reception", ["station-a"], ["reception-1"]))


def test_rejected_edit_does_not_mutate_existing_configuration(inventory):
    stable = compile_config(inventory, proposal("reception", ["station-a"], ["reception-1"]))
    with pytest.raises(PrintConfigurationRejected):
        compile_config(inventory, {**proposal("reception", ["station-a"], ["reception-1"]), "tenantId": 99})
    assert stable.mode == "reception"
    assert stable.printers[0].printer_id == "reception-1"


def test_compiled_configuration_interoperates_with_existing_eligibility_gate(inventory):
    """Contract integration, synthetic only: no real Station, route or printer."""
    from datetime import datetime, timedelta, timezone

    from backend.services.station_document_eligibility import (
        SelfServiceDocumentCandidate, StationEligibilityContext,
    )
    from backend.services.station_document_print_policy import can_offer_print

    now = datetime(2026, 10, 12, tzinfo=timezone.utc)
    context = StationEligibilityContext(
        tenant_id=10, patient_id=77, station_id="station-a", session_id="demo-session",
        session_tenant_id=10, session_patient_id=77, session_station_id="station-a",
        session_created_at=now - timedelta(seconds=40),
        session_claimed_at=now - timedelta(seconds=20),
        session_expires_at=now + timedelta(seconds=80),
        session_purged_at=None, station_tenant_id=10,
        station_experience="station", station_revoked_at=None, now=now,
    )
    candidate = SelfServiceDocumentCandidate(
        document_id="fake-document-1", tenant_id=10, patient_id=77,
        kind="care_sheet", is_active=True, is_latest_version=True,
        finalized=True, withdrawal_authorized=True,
    )
    policy = compile_config(inventory, proposal(
        "both", ["station-a"], ["reception-1", "near-1"],
    ))
    assert can_offer_print(context, candidate, policy, "reception-1").allowed
    assert can_offer_print(context, candidate, policy, "near-1").allowed
    assert not can_offer_print(context, candidate, policy, "unlisted").allowed
    assert not can_offer_print(
        context, replace(candidate, withdrawal_authorized=False), policy, "near-1"
    ).allowed
    assert not can_offer_print(
        replace(context, session_expires_at=now), candidate, policy, "reception-1"
    ).allowed
    assert not can_offer_print(
        replace(context, tenant_id=20), candidate, policy, "reception-1"
    ).allowed
    disabled = default_disabled_print_config(10)
    assert not can_offer_print(context, candidate, disabled, "near-1").allowed


def test_compiled_near_only_policy_requires_explicit_certified_printer(inventory):
    policy = compile_config(inventory, proposal(
        "near_station", ["station-a"], ["near-1"],
    ))
    assert policy.mode == "near_station"
    assert policy.printers[0].private_channel_verified
    assert policy.printers[0].secure_release_verified
    assert not policy.printers[0].staff_supervised
