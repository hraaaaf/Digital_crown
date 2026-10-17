"""Windows-only process lifetime guard for the isolated Imaging LAB.

A private, unnamed Job Object with KILL_ON_JOB_CLOSE is retained exclusively
in the backend parent. Windows closes the handle if that parent dies, killing
the assigned child. This is *not* a clinical service/installer certification.
"""
from __future__ import annotations

import os

class WindowsLabJob:
    def __init__(self, handle: int):
        self._handle = handle

    @classmethod
    def assign(cls, process):
        if os.name != "nt":
            return None

        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimits),
                ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        api.CreateJobObjectW.restype = wintypes.HANDLE
        api.SetInformationJobObject.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
        ]
        api.SetInformationJobObject.restype = wintypes.BOOL
        api.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        api.AssignProcessToJobObject.restype = wintypes.BOOL
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        api.CloseHandle.restype = wintypes.BOOL

        handle = api.CreateJobObjectW(None, None)
        if not handle:
            raise OSError(ctypes.get_last_error(), "IMAGING_LAB_JOB_CREATE_FAILED")
        try:
            info = ExtendedLimits()
            info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not api.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
                raise OSError(ctypes.get_last_error(), "IMAGING_LAB_JOB_LIMIT_FAILED")
            # The child is held at a blocking stdin GO handshake until assigned.
            if not api.AssignProcessToJobObject(handle, wintypes.HANDLE(process._handle)):
                raise OSError(ctypes.get_last_error(), "IMAGING_LAB_JOB_ASSIGN_FAILED")
            return cls(handle)
        except BaseException:
            api.CloseHandle(handle)
            raise

    def close(self):
        if self._handle is None:
            return
        import ctypes
        from ctypes import wintypes
        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        api.CloseHandle.restype = wintypes.BOOL
        handle, self._handle = self._handle, None
        if not api.CloseHandle(handle):
            raise OSError(ctypes.get_last_error(), "IMAGING_LAB_JOB_CLOSE_FAILED")
