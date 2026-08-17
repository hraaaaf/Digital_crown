import pytest

import backend.main as main


@pytest.mark.asyncio
async def test_license_status_fails_closed_when_database_check_raises(monkeypatch):
    main._license_cache.clear()

    async def _raise_db_error(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(main, "run_in_threadpool", _raise_db_error)

    is_ok, reason = await main.get_user_license_status("dentist@example.test")

    assert is_ok is False
    assert reason == "DB_ERROR"
    assert main._license_cache["dentist@example.test"][:2] == (False, "DB_ERROR")


@pytest.mark.asyncio
async def test_license_status_keeps_normal_success_contract(monkeypatch):
    main._license_cache.clear()

    async def _licensed(*args, **kwargs):
        return True, "OK"

    monkeypatch.setattr(main, "run_in_threadpool", _licensed)

    assert await main.get_user_license_status("dentist@example.test") == (True, "OK")
