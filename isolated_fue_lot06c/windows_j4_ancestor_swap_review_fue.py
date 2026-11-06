"""J4 security REVIEW FUE: intermediate-ancestor rename+junction race.

This is an independently structured adversarial test, NOT a clinical approval.
It exercises REAL production restore_new_private_file and triggers a separately
executing attacker process at the exact Windows CreateFileW parent-open boundary.
It must FAIL if restore writes into a trap outside the previously verified chain.

No patient data, production keys, external drive or actual cabinet paths.
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
        raise AssertionError("DC06_J4_ANCESTOR_ATTACK_RENAME_NOT_REPRODUCED")
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
        armed = {"triggered": False}

        class CreateFileInterceptor:
            def __init__(self, original):
                object.__setattr__(self, "_original", original)

            def __getattr__(self, key):
                return getattr(self._original, key)

            def __setattr__(self, key, value):
                if key == "_original":
                    object.__setattr__(self, key, value)
                else:
                    setattr(self._original, key, value)

            def __call__(self, name, *args):
                # Trigger ONLY before opening the final directory child.
                # Production has already checked and retained a handle for its
                # ancestor 'trusted'. The attacker now replaces its PATH.
                if (str(name).casefold() == str(target.parent).casefold()
                        and not armed["triggered"]):
                    armed["triggered"] = True
                    _attacker_rename_and_junction(trusted, moved, trap)
                return self._original(name, *args)

        class KernelProxy:
            def __init__(self, dll):
                self._dll = dll
                self._hook = CreateFileInterceptor(dll.CreateFileW)

            def __getattr__(self, key):
                return self._hook if key == "CreateFileW" else getattr(self._dll, key)

        def intercept(name, *args, **kwargs):
            dll = real_dll(name, *args, **kwargs)
            return KernelProxy(dll) if str(name).lower() == "kernel32" else dll

        ctypes.WinDLL = intercept
        denied = False
        try:
            restore.restore_new_private_file(str(target), raw)
        except restore.WindowsRestoreDenied:
            denied = True
        finally:
            ctypes.WinDLL = real_dll

        if not armed["triggered"]:
            raise AssertionError("DC06_J4_ANCESTOR_REVIEW_NOT_EXERCISED")
        outside = trap / "child" / "recovered.json"
        original = moved / "child" / "recovered.json"
        if outside.is_file():
            print("DC06_J4_UPSTREAM_ANCESTOR_JUNCTION_REDIRECT_REPRODUCED_P1",
                  flush=True)
            raise AssertionError("DC06_J4_UPSTREAM_ANCESTOR_ISOLATION_BROKEN")
        if not denied and not original.is_file():
            raise AssertionError("DC06_J4_ANCESTOR_REVIEW_UNEXPECTED_DESTINATION")
        print("DC06_J4_UPSTREAM_ANCESTOR_NO_ESCAPE_PASS",
              "FAIL_CLOSED" if denied else "ORIGINAL_HANDLE", flush=True)
    finally:
        ctypes.WinDLL = real_dll
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    main()
