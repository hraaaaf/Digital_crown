"""LOT08.2-F disposable per-user Windows process and cold SQLite copy oracle.

This script never starts Digital Crown, reads a real profile, or accesses
production databases. Only three newly created '-synthetic.sqlite' fixtures
inside a random GitHub-hosted Windows runner ProgramData directory.
"""
from __future__ import annotations

from contextlib import closing
import ctypes
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

FILES = ("auth-synthetic.sqlite", "devices-synthetic.sqlite", "queue-synthetic.sqlite")
MARKER = "LOT08_2_F_SYNTHETIC_ONLY"


class LabRefusal(RuntimeError):
    pass


def assert_root(root: Path) -> Path:
    root = Path(root).resolve(strict=True)
    if os.name != "nt" or not root.name.startswith("dc08f-"):
        raise LabRefusal("WINDOWS_EPHEMERAL_FIXTURE_ONLY")
    if root.is_symlink() or not root.is_dir():
        raise LabRefusal("SYMLINK_OR_ROOT_REJECTED")
    return root


def run_as_owner(root: Path, expected_sid: str) -> None:
    root = assert_root(root)
    if not expected_sid.startswith("S-1-5-21-"):
        raise LabRefusal("WINDOWS_LOCAL_STANDARD_SID_REQUIRED")
    me = subprocess.run(
        ["whoami.exe", "/user"], capture_output=True, text=True, check=True, timeout=10
    ).stdout
    if expected_sid not in me:
        raise LabRefusal("OWNER_TOKEN_DOES_NOT_MATCH")
    # Each file is CREATED by the real non-administrator user process.
    for name in FILES:
        p = root / name
        if p.exists() or p.is_symlink():
            raise LabRefusal("OWNER_MUST_CREATE_NEW_ONLY")
        with closing(sqlite3.connect(p)) as db:
            db.execute("CREATE TABLE lab_epoch(id INTEGER PRIMARY KEY, epoch INTEGER NOT NULL, marker TEXT NOT NULL)")
            db.execute("INSERT INTO lab_epoch VALUES(1,0,?)", (MARKER,))
            db.commit()
    lockdb = sqlite3.connect(root / FILES[-1], isolation_level=None)
    try:
        lockdb.execute("BEGIN IMMEDIATE")
        # Marker exposes no account name, SID, credential, path or patient data.
        (root / "owner-ready.json").write_text(json.dumps({
            "lot": "08.2-F", "process_user_sid_verified": True,
            "synthetic_files_created_under_user_token": 3,
        }), encoding="utf-8")
        deadline = time.monotonic() + 75
        while not (root / "owner-stop.request").exists() and time.monotonic() < deadline:
            time.sleep(.08)
        if not (root / "owner-stop.request").exists():
            raise LabRefusal("OWNER_CONTROLLED_STOP_TIMED_OUT")
        lockdb.rollback()
    finally:
        lockdb.close()
    (root / "owner-stopped.json").write_text(
        '{"owned_sqlite_connection_closed":true}', encoding="utf-8"
    )


def validate_store(path: Path) -> int:
    if not path.name.endswith("-synthetic.sqlite") or path.is_symlink() or not path.is_file():
        raise LabRefusal("LAB_SQLITE_FILE_REQUIRED")
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise LabRefusal("SQLITE_INTEGRITY_REJECTED")
            if db.execute("PRAGMA foreign_key_check").fetchall():
                raise LabRefusal("SQLITE_FOREIGN_KEYS_REJECTED")
            row = db.execute("SELECT epoch,marker FROM lab_epoch WHERE id=1").fetchone()
    except sqlite3.DatabaseError as exc:
        raise LabRefusal("SQLITE_BAD_STRUCTURE") from exc
    if not row or type(row[0]) is not int or row[0] < 0 or row[1] != MARKER:
        raise LabRefusal("SQLITE_SYNTHETIC_EPOCH_INVALID")
    return row[0]


def cold_restore_candidate(root: Path, dest: Path) -> int:
    """Does NOT restore onto original user database: clone into fresh directory."""
    root = assert_root(root)
    dest = Path(dest)
    if dest.exists() or dest.is_symlink():
        raise LabRefusal("RESTORE_NEVER_OVERWRITE")
    if not (root / "owner-stopped.json").exists():
        raise LabRefusal("COLD_SNAPSHOT_REQUIRES_STOPPED_OWNER")
    if (root / "owner-stopped.json").read_text(encoding="utf-8") != '{"owned_sqlite_connection_closed":true}':
        raise LabRefusal("COLD_STOP_EVIDENCE_INVALID")
    files = [root / name for name in FILES]
    epochs = [validate_store(p) for p in files]
    if len(set(epochs)) != 1:
        raise LabRefusal("CROSS_STORE_EPOCH_MISMATCH")
    dest.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".dc08f-cold-", dir=dest.parent))
    try:
        for name in FILES:
            with closing(sqlite3.connect((root / name).as_uri() + "?mode=ro", uri=True)) as source:
                with closing(sqlite3.connect(stage / name)) as target:
                    source.backup(target)
        if len({validate_store(stage / name) for name in FILES}) != 1:
            raise LabRefusal("RESTORE_STAGE_MISMATCH")
        if dest.exists() or dest.is_symlink():
            raise LabRefusal("RESTORE_NEVER_OVERWRITE")
        stage.rename(dest)
        return epochs[0]
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def check_guest_denied(root: Path, guest: str, password: str) -> None:
    root = assert_root(root)
    advapi = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    W, H = ctypes.c_wchar_p, ctypes.c_void_p
    advapi.LogonUserW.argtypes = [W, W, W, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(H)]
    advapi.LogonUserW.restype = ctypes.c_int
    advapi.ImpersonateLoggedOnUser.argtypes = [H]
    advapi.ImpersonateLoggedOnUser.restype = ctypes.c_int
    advapi.RevertToSelf.argtypes = []
    advapi.RevertToSelf.restype = ctypes.c_int
    kernel.CreateFileW.argtypes = [W, ctypes.c_uint32, ctypes.c_uint32, H, ctypes.c_uint32, ctypes.c_uint32, H]
    kernel.CreateFileW.restype = H
    kernel.CloseHandle.argtypes = [H]
    kernel.CloseHandle.restype = ctypes.c_int
    token = H()
    if not advapi.LogonUserW(guest, ".", password, 2, 0, ctypes.byref(token)):
        raise LabRefusal("GUEST_TOKEN_LOGON_FAILED")
    try:
        if not advapi.ImpersonateLoggedOnUser(token):
            raise LabRefusal("GUEST_TOKEN_IMPERSONATION_FAILED")
        try:
            for name in FILES:
                for mode in (0x80000000, 0x40000000):  # READ/WRITE
                    handle = kernel.CreateFileW(str(root / name), mode, 7, None, 3, 128, None)
                    if handle != H(-1).value:
                        kernel.CloseHandle(handle)
                        raise LabRefusal("GUEST_SQLITE_ACCESS_GRANT_FORBIDDEN")
                    if ctypes.get_last_error() != 5:
                        raise LabRefusal("EXPECTED_WIN32_ACCESS_DENIED")
        finally:
            if not advapi.RevertToSelf():
                raise LabRefusal("GUEST_TOKEN_REVERT_FAILED")
    finally:
        kernel.CloseHandle(token)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "owner" and len(sys.argv) == 4:
        run_as_owner(Path(sys.argv[2]), sys.argv[3])
    elif mode == "guest" and len(sys.argv) == 4:
        check_guest_denied(Path(sys.argv[2]), sys.argv[3], os.environ["DC08F_GUEST_PASSWORD"])
        print("WINDOWS_DIFFERENT_STANDARD_USER_READ_WRITE_DENIED_PASS")
    elif mode == "cold" and len(sys.argv) == 4:
        print("LOT08F_OFFLINE_COLD_CLONE_EPOCH=" +
              str(cold_restore_candidate(Path(sys.argv[2]), Path(sys.argv[3]))))
    elif mode == "expect-refusal" and len(sys.argv) == 5:
        try:
            cold_restore_candidate(Path(sys.argv[2]), Path(sys.argv[3]))
        except LabRefusal as exc:
            if str(exc) != sys.argv[4]:
                raise
            print("LOT08F_COLD_RESTORE_REFUSED_" + str(exc) + "=PASS")
        else:
            raise LabRefusal("UNSAFE_COLD_RESTORE_WAS_ALLOWED")
    else:
        raise LabRefusal("LAB_MODE_OR_ARGUMENTS_INVALID")
