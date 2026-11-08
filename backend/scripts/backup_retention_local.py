"""MAJ-02: local scheduled-backup retention anchored to OS descriptors.

Only SCHEDULED_ROOT/db and /media are eligible. No offsite deletion.
POSIX: fd-relative scan and unlink, inode recheck.
Windows: hold every ancestor without FILE_SHARE_DELETE, delete by verified
file HANDLE using FileDispositionInfo. No pathname-based delete fallback.
"""
import ctypes
import errno
import importlib.util
import os
import stat
import time
from ctypes import wintypes
from pathlib import Path

_NS_DAY = 86400000000000
_WIN_EPOCH = 116444736000000000


def _policy(path, root, prefix, suffix, days, keep):
    path, root = Path(path), Path(root)
    expected = {root / "db": ("db_backup_", ".sql.enc"),
                root / "media": ("media_backup_", ".zip.enc")}
    if (not path.is_absolute() or not root.is_absolute()
            or ".." in path.parts or ".." in root.parts
            or expected.get(path) != (prefix, suffix)
            or not isinstance(days, int) or days < 0
            or not isinstance(keep, int) or keep < 0):
        raise OSError(errno.EPERM, "Unsafe local retention policy")
    return path, max(3, keep)


def _eligible(name, prefix, suffix):
    return name.startswith(prefix) and name.endswith(suffix) and len(name) > len(prefix) + len(suffix)


def _posix_dir(path):
    if (os.name != "posix" or not hasattr(os, "O_DIRECTORY")
            or not hasattr(os, "O_NOFOLLOW")
            or os.open not in os.supports_dir_fd
            or os.stat not in os.supports_dir_fd
            or os.unlink not in os.supports_dir_fd):
        raise OSError(errno.ENOTSUP, "POSIX descriptor operations unavailable")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    fd = os.open("/", flags)
    try:
        for component in path.parts[1:]:
            child = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        info = os.fstat(fd)
        if info.st_uid != os.geteuid() or info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise OSError(errno.EPERM, "Untrusted writable retention directory")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _posix_identity_unchanged(path, fd):
    try:
        fresh = _posix_dir(path)
    except OSError:
        return False
    try:
        old, new = os.fstat(fd), os.fstat(fresh)
        return (old.st_dev, old.st_ino) == (new.st_dev, new.st_ino)
    finally:
        os.close(fresh)


def _posix_scan(fd, prefix, suffix):
    result = []
    with os.scandir(fd) as entries:
        for entry in entries:
            if not _eligible(entry.name, prefix, suffix):
                continue
            info = os.stat(entry.name, dir_fd=fd, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise OSError(errno.EPERM, "Unsafe backup candidate type")
            result.append((entry.name, info.st_mtime_ns, info.st_dev, info.st_ino, info.st_size))
    return result


def _posix_delete(path, fd, row):
    name, mtime, device, inode, size = row
    if not _posix_identity_unchanged(path, fd):
        raise OSError(errno.EPERM, "Retention root substituted")
    flags = (getattr(os, "O_PATH", os.O_RDONLY) | os.O_NOFOLLOW
             | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0))
    pinned = os.open(name, flags, dir_fd=fd)
    try:
        expected = (device, inode, size, mtime)
        for info in (os.fstat(pinned), os.stat(name, dir_fd=fd, follow_symlinks=False)):
            found = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or found != expected:
                raise OSError(errno.EPERM, "Retention candidate substituted")
        if not _posix_identity_unchanged(path, fd):
            raise OSError(errno.EPERM, "Retention root remapped")
        os.unlink(name, dir_fd=fd)
        if os.fstat(pinned).st_nlink != 0:
            raise OSError(errno.EPERM, "Retention filename changed during unlink")
    finally:
        os.close(pinned)


def _windows_backend():
    if os.name != "nt":
        raise OSError(errno.ENOTSUP, "Windows native backend unavailable")
    src = Path(__file__).with_name("backup_offsite_win32.py")
    spec = importlib.util.spec_from_file_location("_dc_retention_native", src)
    if spec is None or spec.loader is None:
        raise OSError(errno.ENOTSUP, "Windows file API unavailable")
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    return native


def _win_chain(path, native, kernel, nt):
    h = kernel.CreateFileW(path.anchor, native.DIRECTORY_READ_ACCESS,
                           native.FILE_SHARE_DIRECTORY, None, native.OPEN_EXISTING,
                           native.FILE_FLAG_BACKUP_SEMANTICS | native.FILE_FLAG_OPEN_REPARSE_POINT,
                           None)
    if h is None or int(h) == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    handles = [int(h)]
    try:
        native._information(kernel, handles[-1], directory=True)
        for part in path.parts[1:]:
            child = native._open_child(
                nt, handles[-1], part, access=native.DIRECTORY_READ_ACCESS,
                disposition=native.FILE_OPEN,
                options=native.FILE_DIRECTORY_FILE | native.FILE_SYNCHRONOUS_IO_NONALERT,
            )
            handles.append(child)
            native._information(kernel, child, directory=True)
        return handles
    except BaseException:
        for item in reversed(handles):
            kernel.CloseHandle(wintypes.HANDLE(item))
        raise


def _win_open_file(native, nt, parent, name, *, delete=False):
    if not name or name in (".", "..") or any(ch in name for ch in "\\/:"):
        raise OSError(errno.EPERM, "Invalid NT filename")
    encoded = name.encode("utf-16-le")
    if len(encoded) >= 65534:
        raise OSError(errno.ENAMETOOLONG, "NT filename too long")
    buffer = ctypes.create_unicode_buffer(name)
    nt_name = native._UNICODE_STRING(len(encoded), len(encoded) + 2,
                                      ctypes.addressof(buffer))
    attrs = native._OBJECT_ATTRIBUTES(
        ctypes.sizeof(native._OBJECT_ATTRIBUTES), wintypes.HANDLE(parent),
        ctypes.pointer(nt_name), native.OBJ_CASE_INSENSITIVE | native.OBJ_DONT_REPARSE,
        None, None,
    )
    ios = native._IO_STATUS_BLOCK()
    handle = wintypes.HANDLE()
    access = native.SYNCHRONIZE | native.FILE_READ_ATTRIBUTES | (native.DELETE if delete else 0)
    status = nt.NtCreateFile(
        ctypes.byref(handle), access, ctypes.byref(attrs), ctypes.byref(ios),
        None, native.FILE_ATTRIBUTE_NORMAL, native.FILE_SHARE_DIRECTORY,
        native.FILE_OPEN, native.FILE_NON_DIRECTORY_FILE | native.FILE_SYNCHRONOUS_IO_NONALERT,
        None, 0,
    )
    if ctypes.c_int32(status).value < 0:
        raise native.NativeStatusError(status)
    return int(handle.value)


def _win_info(native, kernel, handle):
    native._information(kernel, handle, directory=False)
    info = native._BY_HANDLE_FILE_INFORMATION()
    if not kernel.GetFileInformationByHandle(wintypes.HANDLE(handle), ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    if int(info.nNumberOfLinks) != 1:
        raise OSError(errno.EPERM, "Multiple file links denied")
    last_write = ((int(info.ftLastWriteTime.dwHighDateTime) << 32) |
                  int(info.ftLastWriteTime.dwLowDateTime))
    mtime_ns = (last_write - _WIN_EPOCH) * 100
    size = (int(info.nFileSizeHigh) << 32) | int(info.nFileSizeLow)
    return (mtime_ns, int(info.dwVolumeSerialNumber),
            int(info.nFileIndexHigh), int(info.nFileIndexLow), size)


def _win_scan(path, native, kernel, nt, parent, prefix, suffix):
    records = []
    # Every ancestor is held with sharing of DELETE denied, protecting this
    # Windows pathname enumeration against junction and rename redirection.
    with os.scandir(path) as entries:
        for entry in entries:
            if not _eligible(entry.name, prefix, suffix):
                continue
            fd = _win_open_file(native, nt, parent, entry.name)
            try:
                info = _win_info(native, kernel, fd)
            finally:
                kernel.CloseHandle(wintypes.HANDLE(fd))
            records.append((entry.name, *info))
    return records


def _win_delete(path, native, kernel, nt, parent, row):
    name, *expected = row
    if not native._same_path(path, parent, kernel, nt):
        raise OSError(errno.EPERM, "Windows retention root remapped")
    h = _win_open_file(native, nt, parent, name, delete=True)
    try:
        if tuple(expected) != _win_info(native, kernel, h):
            raise OSError(errno.EPERM, "Windows candidate identity changed")
        if not native._same_path(path, parent, kernel, nt):
            raise OSError(errno.EPERM, "Windows retention root changed")
        # Actual deletion occurs on handle close, not via mutable path.
        native._remove_temporary_by_handle(kernel, h)
    finally:
        kernel.CloseHandle(wintypes.HANDLE(h))


def apply_retention_local(target_dir, prefix, suffix, retention_days,
                          dry_run, min_to_keep, *, scheduled_root):
    report = {"dir": str(target_dir), "dry_run": bool(dry_run),
              "candidates": [], "deleted": [], "status": "BLOCKED_UNSAFE_LOCAL_RETENTION"}
    try:
        path, keep = _policy(target_dir, scheduled_root, prefix, suffix,
                             retention_days, min_to_keep)
        cutoff = time.time_ns() - retention_days * _NS_DAY
        if os.name == "posix":
            try:
                fd = _posix_dir(path)
            except FileNotFoundError:
                report["status"] = "NO_DIRECTORY"
                return report
            try:
                if not _posix_identity_unchanged(path, fd):
                    raise OSError(errno.EPERM, "Directory changed")
                records = _posix_scan(fd, prefix, suffix)
                records.sort(key=lambda row: (row[1], row[0]), reverse=True)
                selected = [row for row in records[keep:] if row[1] < cutoff]
                report["candidates"] = [row[0] for row in selected]
                if not dry_run:
                    for row in selected:
                        _posix_delete(path, fd, row)
                        report["deleted"].append(row[0])
            finally:
                os.close(fd)
        elif os.name == "nt":
            native = _windows_backend()
            kernel, nt = native._apis()
            handles = _win_chain(path, native, kernel, nt)
            try:
                if not native._same_path(path, handles[-1], kernel, nt):
                    raise OSError(errno.EPERM, "Directory changed")
                records = _win_scan(path, native, kernel, nt, handles[-1],
                                    prefix, suffix)
                records.sort(key=lambda row: (row[1], row[0]), reverse=True)
                selected = [row for row in records[keep:] if row[1] < cutoff]
                report["candidates"] = [row[0] for row in selected]
                if not dry_run:
                    for row in selected:
                        _win_delete(path, native, kernel, nt, handles[-1], row)
                        report["deleted"].append(row[0])
            finally:
                for h in reversed(handles):
                    kernel.CloseHandle(wintypes.HANDLE(h))
        else:
            raise OSError(errno.ENOTSUP, "Unsupported local retention platform")
        report["status"] = "DRY_RUN" if dry_run else "SUCCESS"
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        report["status"] = "BLOCKED_UNSAFE_LOCAL_RETENTION"
        report["error_code"] = type(exc).__name__
    return report
