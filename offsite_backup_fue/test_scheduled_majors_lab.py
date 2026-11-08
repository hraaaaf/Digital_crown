"""Regression for MAJ-01 lock/archive collision and MAJ-02 unsafe local retention.

Tests use the real, AST-selected stdlib function bodies from the repository.
Only disposable synthetic directories are touched; no backend/clinical imports.
"""
import ast
import logging
import os
import stat
from pathlib import Path
import uuid


SOURCE = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "scheduled_backup.py"
DB_SOURCE = Path(__file__).resolve().parents[1] / "backend" / "services" / "backup_service.py"
MEDIA_SOURCE = Path(__file__).resolve().parents[1] / "backend" / "scripts" / "backup_media.py"


def _functions(*names, root):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), str(SOURCE))
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in nodes} == set(names)
    namespace = {
        "os": os, "stat": stat, "Path": Path, "logger": logging.getLogger("maj-test"),
        "SCHEDULED_ROOT": root,
        "LOCK_PATH": root / ".backup.lock",
        "_LOCK_FD": None, "MIN_BACKUPS_TO_KEEP": 3, "time": __import__("time"),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(SOURCE), "exec"), namespace)
    return namespace


def test_maj01_kernel_lock_two_independent_callers_and_crash_recovery(tmp_path):
    root = tmp_path / "scheduled"
    a = _functions("_acquire_lock", "_release_lock", root=root)
    b = _functions("_acquire_lock", "_release_lock", root=root)
    acquired, _ = a["_acquire_lock"]()
    assert acquired is True
    assert b["_acquire_lock"]()[0] is False, "concurrent second run must not own the lock"
    a["_release_lock"]()
    assert (root / ".backup.lock").exists(), "persistent lock inode must not be unlinked"
    assert b["_acquire_lock"]()[0] is True, "kernel released lock should be reusable"
    b["_release_lock"]()


def test_maj01_stale_json_is_not_a_stale_lock(tmp_path):
    root = tmp_path / "scheduled"
    root.mkdir()
    (root / ".backup.lock").write_text('{"pid":123,"started_at_epoch":0}', encoding="utf-8")
    mod = _functions("_acquire_lock", "_release_lock", root=root)
    assert mod["_acquire_lock"]()[0] is True, "stale metadata alone must not prevent recovery"
    mod["_release_lock"]()


def test_maj01_archive_writers_do_not_use_destructive_replace():
    """Static oracle: the real producer bodies, not a mock, must have no os.replace."""
    sources = (
        (DB_SOURCE, "_backup_postgres"),
        (MEDIA_SOURCE, "_build_media_archive"),
    )
    for path, method in sources:
        root = ast.parse(path.read_text(encoding="utf-8"), str(path))
        calls = []
        for n in ast.walk(root):
            if isinstance(n, ast.FunctionDef) and n.name == method:
                calls = [sub for sub in ast.walk(n) if isinstance(sub, ast.Call)]
                break
        assert calls, f"{method} must be present"
        assert not any(isinstance(call.func, ast.Attribute) and
                       isinstance(call.func.value, ast.Name) and
                       call.func.value.id == "os" and call.func.attr == "replace"
                       for call in calls), f"{method} must never overwrite final backup"
        assert any(isinstance(call.func, ast.Attribute) and
                   isinstance(call.func.value, ast.Name) and
                   call.func.value.id == "os" and call.func.attr == "link"
                   for call in calls), f"{method} requires atomic no-clobber publication"


def test_maj01_no_clobber_preserves_first_archive(tmp_path):
    target = tmp_path / "db_backup_same-second.sql.enc"
    first = tmp_path / "a.tmp"
    second = tmp_path / "b.tmp"
    first.write_bytes(b"FAKE-ENCRYPTED-DB-A")
    second.write_bytes(b"FAKE-ENCRYPTED-DB-B")
    os.link(first, target)
    try:
        os.link(second, target)
    except FileExistsError:
        pass
    else:
        raise AssertionError("os.link must not replace an existing archive")
    assert target.read_bytes() == b"FAKE-ENCRYPTED-DB-A"


def test_maj02_symlink_retention_must_not_delete_outside(tmp_path):
    root = tmp_path / "scheduled"
    outside = tmp_path / "other_archives"
    outside.mkdir()
    for i in range(5):
        (outside / f"db_backup_old{i}.sql.enc").write_bytes(b"DO_NOT_DELETE")
    root.mkdir()
    redirect = root / "db"
    try:
        redirect.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        import pytest
        pytest.skip(f"symlink privilege unavailable: {type(exc).__name__}")
    mod = _functions("_apply_retention", root=root)
    result = mod["_apply_retention"](redirect, "db_backup_", ".sql.enc", 0, False, 3)
    assert result["status"] == "BLOCKED_UNCERTIFIED_LOCAL_DELETE"
    assert result["deleted"] == []
    assert len(list(outside.iterdir())) == 5


def test_maj02_local_retention_delete_is_disabled_even_on_normal_directory(tmp_path):
    root = tmp_path / "scheduled"
    target = root / "db"
    target.mkdir(parents=True)
    for i in range(5):
        (target / f"db_backup_old{i}.sql.enc").write_bytes(b"FAKE_ARCHIVE")
    mod = _functions("_apply_retention", root=root)
    result = mod["_apply_retention"](target, "db_backup_", ".sql.enc", 0, False, 3)
    assert result["status"] == "BLOCKED_UNCERTIFIED_LOCAL_DELETE"
    assert result["deleted"] == []
    assert len(list(target.iterdir())) == 5



def _hold_lock_in_child(root, queue, release):
    """Spawn-safe worker: a different OS process must own the kernel lock."""
    mod = _functions("_acquire_lock", "_release_lock", root=Path(root))
    try:
        queue.put(mod["_acquire_lock"]()[0])
        release.wait(timeout=15)
    finally:
        mod["_release_lock"]()


def test_maj01_real_spawned_process_cannot_take_locked_archive_root(tmp_path):
    import multiprocessing

    ctx = multiprocessing.get_context("spawn")
    queue, release = ctx.Queue(), ctx.Event()
    p = ctx.Process(target=_hold_lock_in_child, args=(str(tmp_path / "scheduled"), queue, release))
    p.start()
    try:
        assert queue.get(timeout=20) is True
        contender = _functions("_acquire_lock", "_release_lock", root=tmp_path / "scheduled")
        assert contender["_acquire_lock"]()[0] is False
        release.set()
        p.join(timeout=20)
        assert p.exitcode == 0, "child process should release its OS-owned fd"
        assert contender["_acquire_lock"]()[0] is True
        contender["_release_lock"]()
    finally:
        release.set()
        if p.is_alive():
            p.terminate()
            p.join(timeout=10)


def test_maj01_real_postgres_writer_collision_keeps_first_encrypted_archive(tmp_path):
    """Execute the actual PG backup method body with a synthetic cipher and pg_dump."""
    import builtins
    import hashlib
    import subprocess
    from types import SimpleNamespace

    source = ast.parse(DB_SOURCE.read_text(encoding="utf-8"), str(DB_SOURCE))
    klass = next(x for x in source.body if isinstance(x, ast.ClassDef) and x.name == "BackupService")
    method = next(x for x in klass.body if isinstance(x, ast.FunctionDef) and x.name == "_backup_postgres")
    method.decorator_list = []
    original_import = builtins.__import__
    settings = SimpleNamespace(DATABASE_URL="postgresql://FAKE_NO_NETWORK")
    dump = {"bytes": b"FAKE_DUMP_A"}

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "backend.config":
            return SimpleNamespace(settings=settings)
        if name == "backend.scripts.backup_db":
            return SimpleNamespace(
                find_pg_binary=lambda name: "synthetic-pg-dump",
                _parse_postgres_url=lambda url: ("synthetic", "fake", "localhost", 5432, "fake"),
                get_cipher=lambda: SimpleNamespace(encrypt=lambda data: b"SYNTHETIC_ENC_" + data),
            )
        return original_import(name, globals, locals, fromlist, level)

    namespace = {
        "__builtins__": {**vars(builtins), "__import__": fake_import},
        "os": os, "uuid": uuid, "Path": Path,
        "logger": logging.getLogger("maj-test"), "hashlib": hashlib,
        "subprocess": SimpleNamespace(run=lambda *a, **kw: SimpleNamespace(returncode=0, stdout=dump["bytes"])),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), str(DB_SOURCE), "exec"), namespace)
    writer = namespace["_backup_postgres"]
    first = writer(tmp_path, "fixed")
    assert first["status"] == "SUCCESS"
    original = (tmp_path / first["backup_filename"]).read_bytes()
    dump["bytes"] = b"FAKE_DUMP_B"
    second = writer(tmp_path, "fixed")
    assert second["status"] == "FAILED" and second["error_code"] == "WRITE_FAILED"
    assert (tmp_path / first["backup_filename"]).read_bytes() == original
    assert not list(tmp_path.glob(".tmp_*")), "failed contender must clean its own temp"


def test_maj01_real_media_writer_collision_keeps_first_encrypted_archive(tmp_path):
    """Execute the actual media writer with synthetic media and no clinical imports."""
    import builtins
    import hashlib
    import io
    import zipfile
    from types import SimpleNamespace

    media_root = tmp_path / "FAKE_MEDIA"
    media_root.mkdir()
    (media_root / "synthetic.txt").write_text("A", encoding="utf-8")
    dest = tmp_path / "archives"
    source = ast.parse(MEDIA_SOURCE.read_text(encoding="utf-8"), str(MEDIA_SOURCE))
    method = next(x for x in source.body if isinstance(x, ast.FunctionDef) and x.name == "_build_media_archive")
    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "backend.core.media_paths":
            return SimpleNamespace(get_media_root=lambda: media_root,
                                   get_real_media_root=lambda: tmp_path / "REAL_NOT_USED",
                                   is_rehearsal_environment=lambda: False)
        if name == "backend.scripts.backup_db":
            return SimpleNamespace(get_cipher=lambda: SimpleNamespace(encrypt=lambda data: b"SYNTHETIC_ENC_" + data))
        return orig_import(name, globals, locals, fromlist, level)

    namespace = {
        "__builtins__": {**vars(builtins), "__import__": fake_import},
        "os": os, "uuid": uuid, "Path": Path,
        "logger": logging.getLogger("maj-test"), "hashlib": hashlib,
        "zipfile": zipfile, "io": io,
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), str(MEDIA_SOURCE), "exec"), namespace)
    writer = namespace["_build_media_archive"]
    first = writer(dest, "fixed")
    assert first["status"] == "SUCCESS"
    original = (dest / first["backup_filename"]).read_bytes()
    (media_root / "synthetic.txt").write_text("B", encoding="utf-8")
    second = writer(dest, "fixed")
    assert second["status"] == "FAILED" and second["error_code"] == "WRITE_FAILED"
    assert (dest / first["backup_filename"]).read_bytes() == original
    assert not list(dest.glob(".tmp_*"))


def test_maj02_no_file_enumeration_on_requested_delete(tmp_path, monkeypatch):
    root = tmp_path / "scheduled"
    target = root / "db"
    target.mkdir(parents=True)
    def forbidden(*args, **kwargs):
        raise AssertionError("MAJ-02: no path enumeration at all during destructive retention")
    monkeypatch.setattr(Path, "glob", forbidden)
    mod = _functions("_apply_retention", root=root)
    result = mod["_apply_retention"](target, "db_backup_", ".sql.enc", 0, False, 3)
    assert result["status"] == "BLOCKED_UNCERTIFIED_LOCAL_DELETE"
    assert result["deleted"] == []
