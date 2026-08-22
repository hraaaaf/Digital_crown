"""Thirteenth batch — NotificationService whatsapp mock path,
rate_limit check_rate_limit with mocked Request."""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException


# ── NotificationService send_whatsapp_via_whatsmate ───────────────────────────

class TestNotificationServiceWhatsapp:
    def _svc(self):
        from backend.services.notification_service import NotificationService
        return NotificationService()

    def test_invalid_short_number_returns_false(self):
        svc = self._svc()
        result = svc.send_whatsapp_via_whatsmate("12345", "message")
        assert result is False

    def test_empty_number_returns_false(self):
        svc = self._svc()
        result = svc.send_whatsapp_via_whatsmate("", "message")
        assert result is False

    def test_none_number_returns_false(self):
        svc = self._svc()
        result = svc.send_whatsapp_via_whatsmate(None, "message")
        assert result is False

    def test_valid_number_with_mock_keys_returns_true(self):
        # Default keys contain "mock" → mock mode → returns True without HTTP
        svc = self._svc()
        result = svc.send_whatsapp_via_whatsmate("+212612345678", "rappel rdv")
        assert result is True

    def test_mock_mode_detected_when_key_contains_mock(self):
        svc = self._svc()
        # Explicitly confirm keys contain "mock"
        assert "mock" in svc.whatsmate_client_id or "mock" in svc.whatsmate_api_key
        result = svc.send_whatsapp_via_whatsmate("+33612345678", "test")
        assert result is True

    def test_returns_bool(self):
        svc = self._svc()
        result = svc.send_whatsapp_via_whatsmate("+212612345678", "msg")
        assert isinstance(result, bool)


# ── rate_limit check_rate_limit with mocked Request ───────────────────────────

class TestCheckRateLimit:
    def _req(self, ip: str = "10.99.0.1"):
        req = MagicMock()
        req.client.host = ip
        return req

    def test_first_call_does_not_raise(self, tmp_path):
        import backend.utils.rate_limit as rl
        original = rl._store_path
        try:
            rl._store_path = str(tmp_path / "rl.json")
            rl.check_rate_limit(self._req("10.1.1.1"))  # should not raise
        finally:
            rl._store_path = original

    def test_calls_below_limit_do_not_raise(self, tmp_path):
        import backend.utils.rate_limit as rl
        original = rl._store_path
        try:
            rl._store_path = str(tmp_path / "rl2.json")
            for _ in range(4):
                rl.check_rate_limit(self._req("10.2.2.2"))
        finally:
            rl._store_path = original

    def test_exceeding_max_attempts_raises_429(self, tmp_path):
        import backend.utils.rate_limit as rl
        original = rl._store_path
        try:
            rl._store_path = str(tmp_path / "rl3.json")
            # Call MAX_ATTEMPTS (5) times without raising
            for _ in range(5):
                rl.check_rate_limit(self._req("10.3.3.3"))
            # 6th call should trigger rate limit
            with pytest.raises(HTTPException) as exc_info:
                rl.check_rate_limit(self._req("10.3.3.3"))
            assert exc_info.value.status_code == 429
        finally:
            rl._store_path = original

    def test_no_client_host_uses_unknown(self, tmp_path):
        import backend.utils.rate_limit as rl
        original = rl._store_path
        try:
            rl._store_path = str(tmp_path / "rl4.json")
            req = MagicMock()
            req.client = None
            rl.check_rate_limit(req)  # "unknown" IP — should not raise
        finally:
            rl._store_path = original

    def test_different_ips_tracked_independently(self, tmp_path):
        import backend.utils.rate_limit as rl
        original = rl._store_path
        try:
            rl._store_path = str(tmp_path / "rl5.json")
            for _ in range(5):
                rl.check_rate_limit(self._req("10.4.4.4"))
            # Different IP should not be blocked
            rl.check_rate_limit(self._req("10.5.5.5"))  # should not raise
        finally:
            rl._store_path = original
