from types import SimpleNamespace

from backend import models
from backend.routers import mobile, mobile_legacy, mobile_waiting_room


def test_waiting_room_status_round_trips_exactly():
    assert mobile_legacy._MOBILE_TO_BACKEND_STATUS["EN_ATTENTE"] == models.AppointmentStatus.EN_SALLE_ATTENTE
    assert mobile_legacy._BACKEND_TO_MOBILE_STATUS[models.AppointmentStatus.EN_SALLE_ATTENTE] == "EN_ATTENTE"


def test_waiting_room_facade_replaces_only_mobile_get_views():
    snapshot_gets = [
        route for route in mobile.router.routes
        if getattr(route, "path", None) == "/snapshot"
        and "GET" in (getattr(route, "methods", set()) or set())
    ]
    appointments_gets = [
        route for route in mobile.router.routes
        if getattr(route, "path", None) == "/appointments"
        and "GET" in (getattr(route, "methods", set()) or set())
    ]
    status_patches = [
        route for route in mobile.router.routes
        if getattr(route, "path", None) == "/appointments/{appointment_id}/status"
        and "PATCH" in (getattr(route, "methods", set()) or set())
    ]

    assert len(snapshot_gets) == 1
    assert len(appointments_gets) == 1
    assert len(status_patches) == 1


class _FakeQuery:
    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return [
            SimpleNamespace(id=10, ticket_number=12),
            SimpleNamespace(id=11, ticket_number=None),
        ]


class _FakeDb:
    def query(self, *_args, **_kwargs):
        return _FakeQuery()


def test_ticket_enrichment_is_informational_and_nullable():
    payload = {
        "appointments": [
            {"id": 10, "status": "EN_ATTENTE"},
            {"id": 11, "status": "PLANIFIE"},
        ]
    }

    enriched = mobile_waiting_room._enrich_tickets(payload, _FakeDb(), 42, "appointments")

    assert enriched["appointments"][0]["ticket_number"] == 12
    assert enriched["appointments"][1]["ticket_number"] is None
    assert enriched["appointments"][0]["status"] == "EN_ATTENTE"
