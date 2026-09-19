import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

import backend.main  # noqa: F401
from backend.routers import superadmin


def _context():
    user = MagicMock()
    user.id = 42
    user.email = "lot3-superadmin@example.com"
    user.nom_complet = "Pack Test"
    user.telephone_mobile = None
    user.telephone_fixe = None

    admin = MagicMock()
    admin.id = 1

    query = MagicMock()
    query.filter.return_value.first.return_value = user
    db = MagicMock()
    db.query.return_value = query
    return db, user, admin


def test_renewal_without_phone_is_error_not_success():
    db, user, admin = _context()

    with (
        patch.object(superadmin, "add_license_history") as history,
        patch.object(superadmin.notification_service, "send_whatsapp_via_whatsmate") as send,
    ):
        with pytest.raises(HTTPException) as exc:
            superadmin.send_renewal_email(
                42,
                superadmin.SendRenewalEmailRequest(message="Renouvellement"),
                db,
                admin,
            )

    assert exc.value.status_code == 409
    assert "Aucun numéro" in exc.value.detail
    send.assert_not_called()
    history.assert_called_once_with(db, 42, 1, "renewal_whatsapp_skipped_no_phone")
    db.commit.assert_called_once()


def test_renewal_transport_failure_is_error_not_success():
    db, user, admin = _context()
    user.telephone_mobile = "0600000000"

    with (
        patch.object(superadmin, "add_license_history") as history,
        patch.object(
            superadmin.notification_service,
            "send_whatsapp_via_whatsmate",
            return_value=False,
        ) as send,
    ):
        with pytest.raises(HTTPException) as exc:
            superadmin.send_renewal_email(
                42,
                superadmin.SendRenewalEmailRequest(message="Renouvellement"),
                db,
                admin,
            )

    assert exc.value.status_code == 502
    assert "Échec de l'envoi WhatsApp" in exc.value.detail
    send.assert_called_once()
    history.assert_called_once_with(db, 42, 1, "renewal_whatsapp_failed")
    db.commit.assert_called_once()


def test_renewal_success_requires_confirmed_send():
    db, user, admin = _context()
    user.telephone_mobile = "0600000000"

    with (
        patch.object(superadmin, "add_license_history") as history,
        patch.object(
            superadmin.notification_service,
            "send_whatsapp_via_whatsmate",
            return_value=True,
        ) as send,
    ):
        result = superadmin.send_renewal_email(
            42,
            superadmin.SendRenewalEmailRequest(message="Renouvellement"),
            db,
            admin,
        )

    assert result["status"] == "success"
    assert "WhatsApp de relance envoyé avec succès" in result["message"]
    send.assert_called_once()
    history.assert_called_once_with(db, 42, 1, "renewal_whatsapp_sent")
    db.commit.assert_called_once()
