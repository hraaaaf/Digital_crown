"""V1-07 mobile auth hardening contracts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_mobile_pairing_inputs_are_bounded_and_team_approval_is_enforced():
    source = (ROOT / "routers" / "mobile_legacy.py").read_text(encoding="utf-8")

    assert 'token: str = Field(min_length=1, max_length=128)' in source
    assert 'client_public_key_hex: Optional[str] = Field(default=None, max_length=130)' in source
    assert source.count('(approval or "approved") != "approved"') >= 2


def test_mobile_refresh_is_bounded_and_team_approval_is_enforced():
    source = (ROOT / "routers" / "mobile.py").read_text(encoding="utf-8")

    assert 'refresh_token: str = Field(min_length=1, max_length=4096)' in source
    assert '(approval or "approved") != "approved"' in source


def test_secure_lan_runtime_overrides_legacy_http_mobile_urls():
    source = (ROOT / "services" / "mobile_mdns.py").read_text(encoding="utf-8")

    assert 'legacy.get_lan_base_url = lambda: STABLE_HTTPS_ORIGIN' in source
    assert 'legacy.get_lan_frontend_url = lambda: STABLE_HTTPS_ORIGIN' in source
