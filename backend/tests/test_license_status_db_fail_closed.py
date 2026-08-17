import pytest

from backend import main


@pytest.mark.asyncio
async def test_license_status_db_failure_never_grants_access(monkeypatch):
    async def broken_threadpool(*args, **kwargs):
        raise RuntimeError("database unavailable")

    main._license_cache.clear()
    monkeypatch.setattr(main, "run_in_threadpool", broken_threadpool)

    is_ok, reason = await main.get_user_license_status("dentist@example.test")

    assert is_ok is False
    assert reason == "LICENSE_STATUS_UNAVAILABLE"


@pytest.mark.asyncio
async def test_license_status_db_failure_is_cached_as_denial(monkeypatch):
    calls = 0

    async def broken_threadpool(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise RuntimeError("database unavailable")

    main._license_cache.clear()
    monkeypatch.setattr(main, "run_in_threadpool", broken_threadpool)

    first = await main.get_user_license_status("dentist@example.test")
    second = await main.get_user_license_status("dentist@example.test")

    assert first == (False, "LICENSE_STATUS_UNAVAILABLE")
    assert second == first
    assert calls == 1
