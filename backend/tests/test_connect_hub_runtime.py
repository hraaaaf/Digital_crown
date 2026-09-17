from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from backend.routers import connect_hub


class FakeUser:
    def __init__(self, employer_id=42):
        self._employer_id = employer_id

    def get_employer_id(self):
        return self._employer_id


def _query_with_alerts(alerts):
    query = MagicMock()
    query.outerjoin.return_value = query
    query.options.return_value = query
    query.filter.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = alerts
    return query


def test_alert_source_is_tenant_scoped_and_read_only():
    db = MagicMock()
    db.query.return_value = _query_with_alerts([])
    user = FakeUser(employer_id=314)

    with patch.object(connect_hub, "has_permission", return_value=True):
        assert connect_hub._alert_items(db, user) == []

    db.query.assert_called_once_with(connect_hub.models.ProactiveAlert)
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.delete.assert_not_called()

    # Runtime SQL expression must bind the authenticated user's tenant id.
    filter_args = db.query.return_value.filter.call_args.args
    assert any(
        getattr(expr, "right", None) is not None
        and getattr(getattr(expr, "right", None), "value", object()) == 314
        for expr in filter_args
    )


def test_patient_permission_denial_short_circuits_alert_query():
    db = MagicMock()
    user = FakeUser()

    with patch.object(connect_hub, "has_permission", return_value=False):
        assert connect_hub._alert_items(db, user) == []

    db.query.assert_not_called()


def test_accounting_permission_denial_short_circuits_treasury_service():
    db = MagicMock()
    user = FakeUser()

    with (
        patch.object(connect_hub, "has_permission", return_value=False),
        patch.object(connect_hub.accounting_service, "get_treasury_summary") as summary,
    ):
        assert connect_hub._treasury_item(db, user) == []
        summary.assert_not_called()


def test_treasury_service_receives_authenticated_tenant_only():
    db = MagicMock()
    user = FakeUser(employer_id=2718)

    with (
        patch.object(connect_hub, "has_permission", return_value=True),
        patch.object(
            connect_hub.accounting_service,
            "get_treasury_summary",
            return_value={"pending_count": 2, "proactive_alerts": [{}]},
        ) as summary,
    ):
        items = connect_hub._treasury_item(db, user)

    summary.assert_called_once_with(db, 2718)
    assert len(items) == 1
    assert items[0]["delivery_verified"] is False
    assert items[0]["delivery_state"] == "source_state"


def test_runtime_aggregation_never_invokes_transport_or_persistence():
    db = MagicMock()
    user = FakeUser(employer_id=7)

    with (
        patch.object(connect_hub, "_alert_items", return_value=[{"id": "alert:1"}]),
        patch.object(connect_hub, "_treasury_item", return_value=[{"id": "treasury:pending"}]),
    ):
        payload = connect_hub.get_connect_hub(db=db, current_user=user)

    assert payload == {
        "total": 2,
        "requires_attention": 2,
        "items": [{"id": "alert:1"}, {"id": "treasury:pending"}],
        "delivery_semantics": "source_state_only",
    }
    db.add.assert_not_called()
    db.commit.assert_not_called()
    db.delete.assert_not_called()


def test_connect_hub_route_is_mounted_under_intelligence_surface():
    from backend.main import app

    paths = [route.path for route in app.routes]
    assert paths.count("/api/intelligence/connect-hub") == 1
