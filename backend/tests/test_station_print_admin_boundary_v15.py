"""04.8-B2c privileged boundary tests, no real users, PINs or printers."""
import pytest

from backend.services.station_print_admin_boundary import (
    StationPrintAdminDenied,
    require_cabinet_root_owner,
    require_same_origin_mutation,
)


def owner(user_id=10, employer=None, tenant=10):
    require_cabinet_root_owner(
        actor_user_id=user_id, actor_employer_id=employer,
        tenant_id=tenant,
    )


def origin(origin_value="https://cabinet.example", fetch_site="same-origin",
           cookie=True, bearer=False, expected="https://cabinet.example/"):
    require_same_origin_mutation(
        expected_base=expected, origin=origin_value,
        fetch_site=fetch_site,
        has_auth_cookie=cookie, has_bearer_token=bearer,
    )


def test_only_root_owner_can_configure_printing():
    owner()
    for user_id, employer, tenant in (
        (11, 10, 10), (10, 10, 10), (999, None, 10),
        (10, None, 20), (True, None, 10),
        (10, None, True), (10, None, -1),
    ):
        with pytest.raises(StationPrintAdminDenied, match="OWNER_REQUIRED"):
            owner(user_id=user_id, employer=employer, tenant=tenant)


@pytest.mark.parametrize("bad_origin", [
    "http://cabinet.example",
    "https://evil.example",
    "https://cabinet.example.evil.test",
    "https://cabinet.example:444",
    "https://cabinet.example/other",
    "https://cabinet.example?token=1",
    "https://user:pass@cabinet.example",
    "not-an-origin",
])
def test_wrong_browser_origin_denied(bad_origin):
    with pytest.raises(StationPrintAdminDenied):
        origin(origin_value=bad_origin)


@pytest.mark.parametrize("bad_site", ["cross-site", "same-site", "nonesense"])
def test_cross_site_browser_request_denied_even_with_bearer(bad_site):
    with pytest.raises(StationPrintAdminDenied, match="CROSS_SITE_FORBIDDEN"):
        origin(fetch_site=bad_site, bearer=True)


def test_cookie_mutation_requires_explicit_same_origin_header():
    with pytest.raises(StationPrintAdminDenied, match="ORIGIN_REQUIRED"):
        origin(origin_value=None, cookie=True, bearer=True)
    origin(origin_value="https://cabinet.example", cookie=True, bearer=True)


def test_bearer_only_cli_can_omit_origin_but_is_still_authenticated():
    origin(origin_value=None, cookie=False, bearer=True, fetch_site=None)
    with pytest.raises(StationPrintAdminDenied, match="AUTH_REQUIRED"):
        origin(origin_value=None, cookie=False, bearer=False, fetch_site=None)
    with pytest.raises(StationPrintAdminDenied, match="CROSS_SITE_FORBIDDEN"):
        origin(origin_value="https://evil.example", cookie=False, bearer=True)


@pytest.mark.parametrize("bad_base", [
    "https://", "not-a-url", "https://staff:secret@cabinet.example",
    "ftp://cabinet.example",
])
def test_untrusted_server_base_url_never_authorizes_mutation(bad_base):
    with pytest.raises(StationPrintAdminDenied, match="TRUSTED_ORIGIN_REQUIRED"):
        origin(expected=bad_base)
