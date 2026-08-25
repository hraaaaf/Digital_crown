import inspect
from datetime import datetime
from types import SimpleNamespace

from backend.routers import mobile


def test_mobile_notification_routes_use_mobile_permission_and_tenant_scope():
    listing = inspect.getsource(mobile.get_mobile_notifications)
    reading = inspect.getsource(mobile.mark_mobile_notification_read)
    snoozing = inspect.getsource(mobile.snooze_mobile_notification)

    for source in (listing, reading, snoozing):
        assert '_legacy.require_mobile_permission("patients")' in source
        assert 'mobile_user.get_employer_id()' in source
        assert 'models.ProactiveAlert.employer_id == employer_id' in source

    assert 'models.ProactiveAlert.is_read == False' in listing
    assert 'models.ProactiveAlert.expires_at' in listing
    assert 'models.Patient.deleted_at' in listing
    assert 'models.ProactiveAlert.snoozed_until' in listing
    assert '.limit(20)' in listing


def test_mobile_notification_mutations_keep_existing_alert_row_and_snooze_24h():
    reading = inspect.getsource(mobile.mark_mobile_notification_read)
    snoozing = inspect.getsource(mobile.snooze_mobile_notification)

    assert 'alert.is_read = True' in reading
    assert 'db.commit()' in reading
    assert 'timedelta(hours=24)' in snoozing
    assert 'alert.expires_at = alert.snoozed_until + timedelta(days=1)' in snoozing
    assert 'db.commit()' in snoozing


def test_mobile_notification_serializer_is_minimal_and_patient_optional():
    alert = SimpleNamespace(
        id=7,
        patient_id=None,
        patient=None,
        alert_type='STOCK_GANTS',
        title='Stock à surveiller',
        message='Seuil atteint.',
        priority=1,
        created_at=datetime(2026, 8, 25, 12, 0, 0),
    )
    payload = mobile._serialize_mobile_notification(alert)
    assert payload == {
        'id': 7,
        'patient_id': None,
        'patient_name': None,
        'type': 'STOCK_GANTS',
        'title': 'Stock à surveiller',
        'message': 'Seuil atteint.',
        'priority': 1,
        'created_at': '2026-08-25T12:00:00',
    }
