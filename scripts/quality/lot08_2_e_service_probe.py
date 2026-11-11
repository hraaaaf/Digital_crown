"""LOT08.2-E disposable Windows SCM service probe.

Launched ONLY on GitHub-hosted Windows runner as NT AUTHORITY\LocalService,
with an unrestricted per-service SID enabled by sc sidtype. It proves the
service's actual OS token and opens/writes 3 synthetic SQLite files using that
service token. Not a Digital Crown production service or installer.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

if os.name != "nt":
    raise RuntimeError("WINDOWS_ONLY")

if len(sys.argv) != 5:
    raise RuntimeError("SERVICE_ARGS_REQUIRED")

service_name, root_arg, sid_expected, marker_name = sys.argv[1:]
root = Path(root_arg)
result_path = root / marker_name
if (
    not root.is_dir() or not root.name.startswith("dc08e-svc-")
    or marker_name != "service-result.json"
    or not sid_expected.startswith("S-1-5-80-")
):
    raise RuntimeError("SYNTHETIC_SERVICE_ROOT_REQUIRED")

advapi = ctypes.WinDLL("advapi32", use_last_error=True)
DWORD = wintypes.DWORD
HANDLE = wintypes.HANDLE
SERVICE_MAIN = ctypes.WINFUNCTYPE(None, DWORD, ctypes.POINTER(wintypes.LPWSTR))
HANDLER = ctypes.WINFUNCTYPE(None, DWORD)


class SERVICE_STATUS(ctypes.Structure):
    _fields_ = [
        ("dwServiceType", DWORD),
        ("dwCurrentState", DWORD),
        ("dwControlsAccepted", DWORD),
        ("dwWin32ExitCode", DWORD),
        ("dwServiceSpecificExitCode", DWORD),
        ("dwCheckPoint", DWORD),
        ("dwWaitHint", DWORD),
    ]


class SERVICE_TABLE_ENTRY(ctypes.Structure):
    _fields_ = [("lpServiceName", wintypes.LPWSTR), ("lpServiceProc", SERVICE_MAIN)]


advapi.RegisterServiceCtrlHandlerW.argtypes = (wintypes.LPCWSTR, HANDLER)
advapi.RegisterServiceCtrlHandlerW.restype = HANDLE
advapi.SetServiceStatus.argtypes = (HANDLE, ctypes.POINTER(SERVICE_STATUS))
advapi.SetServiceStatus.restype = wintypes.BOOL
advapi.StartServiceCtrlDispatcherW.argtypes = (ctypes.POINTER(SERVICE_TABLE_ENTRY),)
advapi.StartServiceCtrlDispatcherW.restype = wintypes.BOOL

service_status = SERVICE_STATUS(0x10, 2, 0, 0, 0, 1, 10000)
status_handle = None


def signal_status(state: int, exitcode: int = 0) -> None:
    service_status.dwCurrentState = state
    service_status.dwWin32ExitCode = exitcode
    service_status.dwCheckPoint = 0
    service_status.dwWaitHint = 0
    if not advapi.SetServiceStatus(status_handle, ctypes.byref(service_status)):
        raise OSError(ctypes.get_last_error(), "SCM_STATUS_FAILED")


def run_actual_service_token_probe() -> dict:
    user = subprocess.run(
        ["whoami.exe", "/user"], capture_output=True, text=True, check=True,
        timeout=15,
    ).stdout
    groups = subprocess.run(
        ["whoami.exe", "/groups"], capture_output=True, text=True, check=True,
        timeout=15,
    ).stdout
    # The Windows service must execute as LocalService *and* carry its own
    # NT SERVICE\name SID enabled by sc.exe sidtype unrestricted.
    if "S-1-5-19" not in user:
        raise RuntimeError("SERVICE_NOT_LOCAL_SERVICE")
    if sid_expected.casefold() not in groups.casefold():
        raise RuntimeError("REAL_PER_SERVICE_SID_MISSING")
    for name in ("auth-synthetic.sqlite", "devices-synthetic.sqlite", "queue-synthetic.sqlite"):
        p = root / name
        if p.is_symlink() or not p.is_file():
            raise RuntimeError("SERVICE_SYNTHETIC_FILE_MISSING")
        with sqlite3.connect(p.as_uri() + "?mode=rw", uri=True, timeout=3) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS lab_service_probe "
                "(token_marker TEXT NOT NULL)"
            )
            db.execute(
                "INSERT INTO lab_service_probe VALUES('REAL_WINDOWS_SERVICE_PROCESS')"
            )
            db.commit()
            if db.execute("SELECT count(*) FROM lab_service_probe").fetchone()[0] != 1:
                raise RuntimeError("SERVICE_SQLITE_WRITE_FAILED")
    return {
        "lot": "08.2-E",
        "status": "success",
        "account_sid_is_local_service": True,
        "per_service_sid_visible_in_actual_service_token": True,
        "sqlite_three_files_opened_written_by_real_service_token": True,
        "synthetic_only": True,
        "clinical_activation": False,
        "production_desktop_service_tested": False,
    }


@HANDLER
def control_handler(_control):
    # The disposable test has no external control surface; it completes itself.
    return


@SERVICE_MAIN
def service_main(_argc, _argv):
    global status_handle
    status_handle = advapi.RegisterServiceCtrlHandlerW(service_name, control_handler)
    if not status_handle:
        return
    try:
        signal_status(4)  # SERVICE_RUNNING
        try:
            report = run_actual_service_token_probe()
        except BaseException as exc:
            # Never expose paths, SIDs or secrets in the CI artifact.
            report = {
                "lot": "08.2-E",
                "status": "failure",
                "failure_type": type(exc).__name__,
                "synthetic_only": True,
            }
        result_path.write_text(json.dumps(report, sort_keys=True), encoding="utf-8")
        signal_status(1, 0 if report["status"] == "success" else 1)
    except BaseException:
        try:
            signal_status(1, 1)
        except BaseException:
            pass


table = (SERVICE_TABLE_ENTRY * 2)()
table[0].lpServiceName = service_name
table[0].lpServiceProc = service_main
table[1].lpServiceName = None
table[1].lpServiceProc = SERVICE_MAIN()
if not advapi.StartServiceCtrlDispatcherW(table):
    raise OSError(ctypes.get_last_error(), "SCM_DISPATCHER_REQUIRED")
