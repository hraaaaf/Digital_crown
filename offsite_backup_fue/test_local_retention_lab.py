"""MAJ-02 negative and positive scenarios on disposable synthetic archives."""
import importlib.util
import os
import time
from pathlib import Path
import pytest

SRC = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "backup_retention_local.py"
spec = importlib.util.spec_from_file_location("_retention_test", SRC)
retention = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retention)


def _files(tmp_path, folder="db"):
    root = tmp_path / "scheduled"
    dest = root / folder
    dest.mkdir(parents=True)
    prefix, suffix = (("db_backup_", ".sql.enc") if folder == "db"
                      else ("media_backup_", ".zip.enc"))
    paths = []
    for i in range(5):
        p = dest / f"{prefix}fake_{i}{suffix}"
        p.write_bytes(b"FAKE_ENCRYPTED_ARCHIVE")
        old = time.time() - (40+i) * 86400
        os.utime(p, (old, old))
        paths.append(p)
    return root, dest, prefix, suffix, paths


def _run(root, dest, prefix, suffix, *, dry_run=False):
    return retention.apply_retention_local(
        dest, prefix, suffix, 30, dry_run, 3, scheduled_root=root)


def test_maj02_positive_deletion_keeps_newest_three(tmp_path):
    root, dest, prefix, suffix, paths = _files(tmp_path)
    result = _run(root, dest, prefix, suffix)
    assert result["status"] == "SUCCESS", result
    assert len(result["deleted"]) == 2
    assert [p.exists() for p in paths] == [True, True, True, False, False]


def test_maj02_dry_run_does_not_delete(tmp_path):
    root, dest, prefix, suffix, paths = _files(tmp_path, folder="media")
    result = _run(root, dest, prefix, suffix, dry_run=True)
    assert result["status"] == "DRY_RUN", result
    assert len(result["candidates"]) == 2 and result["deleted"] == []
    assert all(p.exists() for p in paths)


def test_maj02_outside_local_root_rejected(tmp_path):
    root, _, prefix, suffix, _ = _files(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    victim = external / f"{prefix}victim{suffix}"
    victim.write_bytes(b"DO_NOT_DELETE")
    result = _run(root, external, prefix, suffix)
    assert result["status"] == "BLOCKED_UNSAFE_LOCAL_RETENTION"
    assert victim.read_bytes() == b"DO_NOT_DELETE"


def test_maj02_wrong_prefix_policy_rejected(tmp_path):
    root, dest, prefix, suffix, paths = _files(tmp_path)
    result = _run(root, dest, "other_", suffix)
    assert result["status"] == "BLOCKED_UNSAFE_LOCAL_RETENTION"
    assert all(p.exists() for p in paths)


def test_maj02_external_symlink_candidate_preserved(tmp_path):
    root, dest, prefix, suffix, paths = _files(tmp_path)
    external = tmp_path / "external"
    external.write_bytes(b"KEEP")
    try:
        (dest / f"{prefix}linked{suffix}").symlink_to(external)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink not permitted: {type(exc).__name__}")
    result = _run(root, dest, prefix, suffix)
    assert result["status"] == "BLOCKED_UNSAFE_LOCAL_RETENTION"
    assert external.read_bytes() == b"KEEP"
    assert all(p.exists() for p in paths)


@pytest.mark.skipif(os.name != "posix", reason="POSIX path swap")
def test_maj02_posix_directory_swap_after_scan_prevents_delete(tmp_path, monkeypatch):
    root, dest, prefix, suffix, paths = _files(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    victim = external / f"{prefix}victim{suffix}"
    victim.write_bytes(b"KEEP")
    moved = root / "db_previous"
    original = retention._posix_identity_unchanged
    count = {"n": 0}
    def substitute(path, fd):
        count["n"] += 1
        if count["n"] == 2:
            dest.rename(moved)
            dest.symlink_to(external, target_is_directory=True)
        return original(path, fd)
    monkeypatch.setattr(retention, "_posix_identity_unchanged", substitute)
    result = _run(root, dest, prefix, suffix)
    assert count["n"] >= 2
    assert result["status"] == "BLOCKED_UNSAFE_LOCAL_RETENTION", result
    assert victim.read_bytes() == b"KEEP"
    assert len(list(moved.iterdir())) == 5


@pytest.mark.skipif(os.name != "posix", reason="POSIX final unlink race")
def test_maj02_posix_swap_just_before_unlink_cannot_delete_external(tmp_path, monkeypatch):
    root, dest, prefix, suffix, paths = _files(tmp_path)
    external = tmp_path / "external"
    external.write_bytes(b"KEEP")
    raw_unlink = retention.os.unlink
    once = {"done": False}
    def replace_name(name, *, dir_fd):
        if not once["done"]:
            once["done"] = True
            original = dest / name
            original.rename(dest / (name + ".moved"))
            original.symlink_to(external)
        return raw_unlink(name, dir_fd=dir_fd)
    monkeypatch.setattr(retention.os, "unlink", replace_name)
    # The capability oracle checks callable identity; preserve the mocked
    # dir_fd capability, otherwise fail-closed preflight stops before injection.
    monkeypatch.setattr(retention.os, "supports_dir_fd",
                        set(retention.os.supports_dir_fd) | {replace_name})
    result = _run(root, dest, prefix, suffix)
    assert once["done"], result
    assert result["status"] == "BLOCKED_UNSAFE_LOCAL_RETENTION", result
    assert external.read_bytes() == b"KEEP"


@pytest.mark.skipif(os.name != "nt", reason="Windows junction")
def test_maj02_windows_junction_path_is_rejected(tmp_path):
    import subprocess
    root = tmp_path / "scheduled"
    root.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    for i in range(5):
        (external / f"db_backup_external{i}.sql.enc").write_bytes(b"KEEP")
    target = root / "db"
    command = subprocess.run(["cmd", "/c", "mklink", "/J", str(target), str(external)],
                             capture_output=True, text=True)
    if command.returncode != 0:
        pytest.skip("Junction creation restricted")
    result = _run(root, target, "db_backup_", ".sql.enc")
    assert result["status"] == "BLOCKED_UNSAFE_LOCAL_RETENTION", result
    assert all(p.read_bytes() == b"KEEP" for p in external.iterdir())


@pytest.mark.skipif(os.name != "nt", reason="Windows pinned HANDLE")
def test_maj02_windows_directory_rename_denied_while_scanning(tmp_path, monkeypatch):
    root, dest, prefix, suffix, paths = _files(tmp_path)
    original = retention.os.scandir
    denied = {"yes": False}
    def attack(path):
        if Path(path) == dest:
            try:
                dest.rename(root / "db_moved")
            except OSError:
                denied["yes"] = True
            else:
                raise AssertionError("Directory rename was not blocked")
        return original(path)
    monkeypatch.setattr(retention.os, "scandir", attack)
    result = _run(root, dest, prefix, suffix)
    assert denied["yes"]
    assert result["status"] == "SUCCESS", result
    assert len(result["deleted"]) == 2
