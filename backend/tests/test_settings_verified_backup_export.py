from unittest.mock import patch

from backend import models


def _make_admin(dentiste, db):
    dentiste.role = models.UserRole.ADMIN
    dentiste.permissions = {**(dentiste.permissions or {}), "admin": True}
    db.commit()


def test_manual_export_downloads_exact_verified_backup_filename(client, db, dentiste, auth_headers, tmp_path):
    _make_admin(dentiste, db)
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    filename = "db_backup_20260817_120000.sql.enc"
    payload = b"encrypted-backup-bytes"
    (backups_dir / filename).write_bytes(payload)

    result = {
        "engine": "postgresql",
        "status": "SUCCESS",
        "backup_filename": filename,
        "size_bytes": len(payload),
        "checksum": "abc123",
    }

    with patch("backend.routers.admin.BackupService.backup_active_database", return_value=result), \
         patch("backend.routers.admin.AppPaths.get_user_data_dir", return_value=tmp_path):
        response = client.get("/api/admin/export-db", headers=auth_headers)

    assert response.status_code == 200
    assert response.content == payload
    disposition = response.headers.get("content-disposition", "")
    assert filename in disposition
    assert response.headers.get("content-type", "").startswith("application/octet-stream")


def test_manual_export_fails_closed_when_backup_service_fails(client, db, dentiste, auth_headers):
    _make_admin(dentiste, db)
    result = {
        "engine": "postgresql",
        "status": "FAILED",
        "backup_filename": None,
        "size_bytes": 0,
        "checksum": None,
        "error_code": "PG_DUMP_FAILED",
    }

    with patch("backend.routers.admin.BackupService.backup_active_database", return_value=result):
        response = client.get("/api/admin/export-db", headers=auth_headers)

    assert response.status_code == 500
    assert "sauvegarde chiffrée" in response.json()["detail"].lower()


def test_manual_export_refuses_missing_or_empty_verified_file(client, db, dentiste, auth_headers, tmp_path):
    _make_admin(dentiste, db)
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    filename = "db_backup_20260817_120000.db.enc"
    (backups_dir / filename).write_bytes(b"")

    result = {
        "engine": "sqlite",
        "status": "SUCCESS",
        "backup_filename": filename,
        "size_bytes": 0,
        "checksum": "empty",
    }

    with patch("backend.routers.admin.BackupService.backup_active_database", return_value=result), \
         patch("backend.routers.admin.AppPaths.get_user_data_dir", return_value=tmp_path):
        response = client.get("/api/admin/export-db", headers=auth_headers)

    assert response.status_code == 500
    assert "introuvable" in response.json()["detail"].lower()
