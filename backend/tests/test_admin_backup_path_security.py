"""Security contract for admin backup downloads."""

from pathlib import Path


def test_backup_download_is_confined_to_backup_root():
    source = (
        Path(__file__).resolve().parents[1] / "routers" / "admin_legacy.py"
    ).read_text(encoding="utf-8")
    start = source.index('@router.get("/backups/download/{filename}")')
    block = source[start:start + 1400]

    assert '"/" in filename' in block
    assert '"\\\\" in filename' in block
    assert '(AppPaths.get_user_data_dir() / "backups").resolve()' in block
    assert '(backups_dir / filename).resolve()' in block
    assert 'file_path.parent != backups_dir' in block
    assert 'file_path.is_file()' in block
