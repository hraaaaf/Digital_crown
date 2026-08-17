from backend.services.sync_manager import SyncManager


def test_start_listening_does_not_register_cloud_sync(monkeypatch):
    manager = SyncManager()

    called = {"listen": False}

    def _unexpected_listen(*args, **kwargs):
        called["listen"] = True
        raise AssertionError("SQLAlchemy cloud-sync listeners must stay disabled")

    try:
        import sqlalchemy.event as sa_event
        monkeypatch.setattr(sa_event, "listen", _unexpected_listen)
    except Exception:
        # The local-first facade does not import sqlalchemy at all; this branch
        # only keeps the test robust if SQLAlchemy is unavailable in a narrow
        # unit-test environment.
        pass

    manager.start_listening()
    assert called["listen"] is False


def test_legacy_sync_entry_points_are_fail_closed():
    manager = SyncManager()

    assert manager._perform_bulk_sync() is None
    assert manager._perform_sync(42) is None
    assert manager._sync_single_cabinet(object(), 42) is None
