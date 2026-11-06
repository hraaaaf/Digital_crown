"""J4 native Windows adversarial FUE: real ancestor rename + junction races.

Exercise the ACTUAL restore AND secure reader, with a separate attacker process
triggered at a real native NtCreateFile relative directory-open boundary.
No patients, production material, artificial PASS, or clinic activation.
"""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from f5bd4_fixed_recovery_windows_fue import modules


def _attacker_rename_and_junction(trusted: Path, moved: Path, trap: Path) -> None:
    rename = subprocess.run(
        [sys.executable, "-c",
         "import os,sys;os.rename(sys.argv[1],sys.argv[2])",
         str(trusted), str(moved)],
        capture_output=True, text=True, timeout=20,
    )
    if rename.returncode != 0 or trusted.exists() or not moved.is_dir():
        raise AssertionError(
            "DC06_J4_ANCESTOR_ATTACK_RENAME_NOT_REPRODUCED "
            f"code={rename.returncode} stderr={rename.stderr[-240:]!r} "
            f"original_exists={trusted.exists()} moved_exists={moved.is_dir()}"
        )
    junction = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(trusted), str(trap)],
        capture_output=True, text=True, timeout=20,
    )
    if junction.returncode != 0 or not trusted.is_junction():
        raise AssertionError("DC06_J4_ANCESTOR_ATTACK_JUNCTION_UNAVAILABLE")
    print("DC06_J4_ANCESTOR_RENAME_AND_JUNCTION_INDEPENDENT_PROCESS_PASS",
          flush=True)


def main() -> None:
    if (os.name != "nt"
            or os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME") != "true"
            or os.environ.get("GITHUB_JOB") != "ancestor_review"):
        raise RuntimeError("DC06_J4_ANCESTOR_REVIEW_WINDOWS_CI_ONLY")

    recovery, restore, _ = modules()
    probe = sys.modules["backend.services.windows_keyring_handle_probe"]
    data = {
        "active_media_id": "media2", "active_locator_id": "loc2",
        "media_keys": {"media1": "11" * 32, "media2": "22" * 32},
        "locator_keys": {"loc1": "33" * 32, "loc2": "44" * 32},
    }
    raw = recovery._canonical(data)
    root = Path(tempfile.mkdtemp(prefix="dc06-ancestor-review-", dir=os.environ["RUNNER_TEMP"]))
    real_dll = ctypes.WinDLL
    try:
        trusted, moved, trap = (root / x for x in ("trusted", "moved", "trap"))
        (trusted / "child").mkdir(parents=True)
        (trap / "child").mkdir(parents=True)
        target = trusted / "child" / "recovered.json"
        scenario = {"triggered": False, "trusted": trusted,
                    "moved": moved, "trap": trap}

        class NtCreateInterceptor:
            def __init__(self, original):
                object.__setattr__(self, "_original", original)

            def __getattr__(self, key):
                return getattr(self._original, key)

            def __setattr__(self, key, value):
                if key == "_original":
                    object.__setattr__(self, key, value)
                else:
                    setattr(self._original, key, value)

            def __call__(self, *args):
                # Only the one-component "child" opening below the already
                # verified trusted ANCESTOR, never the final new file.
                attrs = ctypes.cast(
                    args[2], ctypes.POINTER(probe._ObjectAttributes)).contents
                if attrs.object_name:
                    u = attrs.object_name.contents
                    leaf = ctypes.wstring_at(u.buffer, u.length // 2)
                    if leaf.casefold() == "child" and not scenario["triggered"]:
                        if not attrs.root_directory:
                            raise AssertionError("DC06_J4_RELATIVE_PARENT_HANDLE_MISSING")
                        scenario["triggered"] = True
                        _attacker_rename_and_junction(
                            scenario["trusted"], scenario["moved"], scenario["trap"])
                return self._original(*args)

        class NtdllProxy:
            def __init__(self, dll):
                self._dll = dll
                self._hook = NtCreateInterceptor(dll.NtCreateFile)

            def __getattr__(self, key):
                return self._hook if key == "NtCreateFile" else getattr(self._dll, key)

        def intercept(name, *args, **kwargs):
            dll = real_dll(name, *args, **kwargs)
            return NtdllProxy(dll) if str(name).lower() == "ntdll" else dll

        # WRITE: the adversary swaps the ancestor after its original handle
        # was obtained, before "child" is opened using NtCreateFile.
        ctypes.WinDLL = intercept
        denied = False
        try:
            restore.restore_new_private_file(str(target), raw)
        except restore.WindowsRestoreDenied:
            denied = True
        finally:
            ctypes.WinDLL = real_dll

        if not scenario["triggered"]:
            raise AssertionError("DC06_J4_WRITE_ANCESTOR_ATTACK_NOT_EXERCISED")
        outside = trap / "child" / "recovered.json"
        original = moved / "child" / "recovered.json"
        if outside.is_file():
            print("DC06_J4_UPSTREAM_ANCESTOR_JUNCTION_REDIRECT_REPRODUCED_P1",
                  flush=True)
            raise AssertionError("DC06_J4_UPSTREAM_ANCESTOR_ISOLATION_BROKEN")
        if not denied and not original.is_file():
            raise AssertionError("DC06_J4_ANCESTOR_REVIEW_UNEXPECTED_DESTINATION")
        if original.exists() and original.read_bytes() != raw:
            raise AssertionError("DC06_J4_ORIGINAL_KEYRING_CONTENT_MISMATCH")
        print("DC06_J4_UPSTREAM_ANCESTOR_NO_ESCAPE_PASS",
              "FAIL_CLOSED" if denied else "ORIGINAL_HANDLE", flush=True)

        # READ: create two DIFFERENT, valid private keyrings on separate
        # directories. The attacker switches the ancestor name to the trap,
        # then the actual native product reader must never read the trap.
        read_trusted, read_moved, read_trap = (
            root / x for x in ("read-trusted", "read-moved", "read-trap"))
        (read_trusted / "child").mkdir(parents=True)
        (read_trap / "child").mkdir(parents=True)
        alternate = dict(data)
        alternate["media_keys"] = dict(data["media_keys"])
        alternate["media_keys"]["media1"] = "55" * 32
        false_raw = recovery._canonical(alternate)
        reader_target = read_trusted / "child" / "keyring.json"
        restore.restore_new_private_file(str(reader_target), raw)
        restore.restore_new_private_file(str(read_trap / "child" / "keyring.json"),
                                         false_raw)
        scenario.update({"triggered": False, "trusted": read_trusted,
                         "moved": read_moved, "trap": read_trap})
        ctypes.WinDLL = intercept
        read_denied = False
        actual = None
        try:
            actual = probe.read_no_reparse_file(str(reader_target))
        except probe.WindowsKeyringHandleDenied:
            read_denied = True
        finally:
            ctypes.WinDLL = real_dll

        if not scenario["triggered"]:
            raise AssertionError("DC06_J4_READ_ANCESTOR_ATTACK_NOT_EXERCISED")
        if actual == false_raw:
            print("DC06_J4_READ_ANCESTOR_SPOOF_REPRODUCED_P1", flush=True)
            raise AssertionError("DC06_J4_READ_ANCESTOR_ISOLATION_BROKEN")
        if not read_denied and actual != raw:
            raise AssertionError("DC06_J4_READ_UNEXPECTED_CONTENT")
        print("DC06_J4_READ_UPSTREAM_ANCESTOR_NO_SPOOF_PASS",
              "FAIL_CLOSED" if read_denied else "ORIGINAL_HANDLE", flush=True)
    finally:
        ctypes.WinDLL = real_dll
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
