"""Windows handle-relative, no-clobber encrypted offsite copy candidate.

This is security-sensitive Win32/NT interop. It is tested against synthetic
NTFS runner paths, NOT approved for SMB/NAS or clinical deployment. Each
directory child, tempfile, existing target and publication is opened relative
to a pinned parent directory HANDLE. No lexical-path fallback is allowed.

Windows native APIs: NtCreateFile (RootDirectory, OBJ_DONT_REPARSE),
GetFileInformationByHandle and SetFileInformationByHandle(FileLinkInfo).
"""
import ctypes
import errno
import hashlib
import os
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path
from ctypes import wintypes

if os.name == "nt":
    import msvcrt

FILE_SHARE_ALL = 0x7
SYNCHRONIZE = 0x00100000
FILE_READ_ATTRIBUTES = 0x80
FILE_LIST_DIRECTORY = 0x1
FILE_ADD_FILE = 0x2
FILE_ADD_SUBDIRECTORY = 0x4
FILE_TRAVERSE = 0x20
DIRECTORY_ACCESS = (SYNCHRONIZE | FILE_READ_ATTRIBUTES | FILE_LIST_DIRECTORY
                    | FILE_TRAVERSE | FILE_ADD_FILE | FILE_ADD_SUBDIRECTORY)
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
DELETE = 0x00010000
FILE_OPEN = 0x1
FILE_CREATE = 0x2
FILE_SYNCHRONOUS_IO_NONALERT = 0x20
FILE_DIRECTORY_FILE = 0x1
FILE_NON_DIRECTORY_FILE = 0x40
FILE_ATTRIBUTE_NORMAL = 0x80
FILE_ATTRIBUTE_DIRECTORY = 0x10
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
OBJ_DONT_REPARSE = 0x1000
OBJ_CASE_INSENSITIVE = 0x40
STATUS_OBJECT_NAME_NOT_FOUND = 0xC0000034
STATUS_REPARSE_POINT_ENCOUNTERED = 0xC000050B
ERROR_FILE_EXISTS = 80
ERROR_ALREADY_EXISTS = 183
FILE_LINK_INFO_CLASS = 11
FILE_DISPOSITION_INFO_CLASS = 4


class _UNICODE_STRING(ctypes.Structure):
    _fields_ = [("Length", wintypes.USHORT), ("MaximumLength", wintypes.USHORT),
                ("Buffer", ctypes.c_void_p)]


class _OBJECT_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Length", wintypes.ULONG),
                ("RootDirectory", wintypes.HANDLE),
                ("ObjectName", ctypes.POINTER(_UNICODE_STRING)),
                ("Attributes", wintypes.ULONG),
                ("SecurityDescriptor", ctypes.c_void_p),
                ("SecurityQualityOfService", ctypes.c_void_p)]


class _IO_STATUS_BLOCK(ctypes.Structure):
    _fields_ = [("Status", ctypes.c_void_p), ("Information", ctypes.c_void_p)]


class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]


class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [("dwFileAttributes", wintypes.DWORD),
                ("ftCreationTime", _FILETIME),
                ("ftLastAccessTime", _FILETIME),
                ("ftLastWriteTime", _FILETIME),
                ("dwVolumeSerialNumber", wintypes.DWORD),
                ("nFileSizeHigh", wintypes.DWORD),
                ("nFileSizeLow", wintypes.DWORD),
                ("nNumberOfLinks", wintypes.DWORD),
                ("nFileIndexHigh", wintypes.DWORD),
                ("nFileIndexLow", wintypes.DWORD)]


class _FILE_DISPOSITION_INFO(ctypes.Structure):
    _fields_ = [("DeleteFile", wintypes.BOOLEAN)]


class NativeStatusError(OSError):
    def __init__(self, status):
        self.status = status & 0xFFFFFFFF
        super().__init__(errno.EPERM, f"Native file operation denied: NTSTATUS=0x{self.status:08X}")


def _apis():
    if os.name != "nt":
        raise OSError(errno.ENOSYS, "Windows native backend unavailable")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    nt = ctypes.WinDLL("ntdll", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                   ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION)]
    kernel.GetFileInformationByHandle.restype = wintypes.BOOL
    kernel.GetFileType.argtypes = [wintypes.HANDLE]
    kernel.GetFileType.restype = wintypes.DWORD
    kernel.SetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel.SetFileInformationByHandle.restype = wintypes.BOOL
    nt.NtCreateFile.argtypes = [ctypes.POINTER(wintypes.HANDLE), wintypes.ULONG,
                               ctypes.POINTER(_OBJECT_ATTRIBUTES),
                               ctypes.POINTER(_IO_STATUS_BLOCK), ctypes.c_void_p,
                               wintypes.ULONG, wintypes.ULONG, wintypes.ULONG,
                               wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG]
    nt.NtCreateFile.restype = ctypes.c_long
    return kernel, nt


@contextmanager
def _own(handle, kernel):
    try:
        yield int(handle)
    finally:
        kernel.CloseHandle(wintypes.HANDLE(int(handle)))


def _information(kernel, handle, *, directory):
    info = _BY_HANDLE_FILE_INFORMATION()
    if not kernel.GetFileInformationByHandle(wintypes.HANDLE(handle), ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    if (info.dwFileAttributes & FILE_ATTRIBUTE_REPARSE_POINT or
        bool(info.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) != bool(directory) or
        kernel.GetFileType(wintypes.HANDLE(handle)) != 1):
        raise OSError(errno.EPERM, "Non-regular/reparse file object denied")
    return (info.dwVolumeSerialNumber, info.nFileIndexHigh, info.nFileIndexLow)


def _open_child(nt, parent, component, *, access, disposition, options, attributes=FILE_ATTRIBUTE_NORMAL):
    if not component or component in (".", "..") or "/" in component or "\\" in component:
        raise OSError(errno.EPERM, "Unsafe NT path component")
    name_bytes = component.encode("utf-16-le")
    if len(name_bytes) >= 65534:
        raise OSError(errno.ENAMETOOLONG, "Path component too long")
    buf = ctypes.create_unicode_buffer(component)
    name = _UNICODE_STRING(len(name_bytes), len(name_bytes) + 2, ctypes.addressof(buf))
    attrs = _OBJECT_ATTRIBUTES(ctypes.sizeof(_OBJECT_ATTRIBUTES), wintypes.HANDLE(parent),
                               ctypes.pointer(name), OBJ_CASE_INSENSITIVE | OBJ_DONT_REPARSE,
                               None, None)
    ios = _IO_STATUS_BLOCK()
    result_handle = wintypes.HANDLE()
    status = nt.NtCreateFile(ctypes.byref(result_handle), access, ctypes.byref(attrs),
                             ctypes.byref(ios), None, attributes, FILE_SHARE_ALL,
                             disposition, options, None, 0)
    status_int = ctypes.c_int32(status).value
    if status_int < 0:
        raise NativeStatusError(status_int)
    return int(result_handle.value)


def _walk_directory(directory, kernel, nt, *, create):
    target = Path(directory)
    if not target.is_absolute() or ".." in target.parts:
        raise OSError(errno.EPERM, "Relative or parent-traversing destination refused")
    root = target.anchor
    if not root:
        raise OSError(errno.EPERM, "Missing volume/share anchor")
    handle = kernel.CreateFileW(root, DIRECTORY_ACCESS, FILE_SHARE_ALL, None, FILE_OPEN,
                                FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT, None)
    if handle is None or int(handle) == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    current = int(handle)
    try:
        _information(kernel, current, directory=True)
        for component in target.parts[1:]:
            try:
                child = _open_child(nt, current, component, access=DIRECTORY_ACCESS,
                                    disposition=FILE_OPEN,
                                    options=FILE_DIRECTORY_FILE | FILE_SYNCHRONOUS_IO_NONALERT)
            except NativeStatusError as exc:
                if not create or exc.status != STATUS_OBJECT_NAME_NOT_FOUND:
                    raise
                child = _open_child(nt, current, component, access=DIRECTORY_ACCESS,
                                    disposition=FILE_CREATE,
                                    options=FILE_DIRECTORY_FILE | FILE_SYNCHRONOUS_IO_NONALERT,
                                    attributes=FILE_ATTRIBUTE_DIRECTORY)
            try:
                _information(kernel, child, directory=True)
            except BaseException:
                kernel.CloseHandle(wintypes.HANDLE(child))
                raise
            kernel.CloseHandle(wintypes.HANDLE(current))
            current = child
        return current
    except BaseException:
        kernel.CloseHandle(wintypes.HANDLE(current))
        raise


def _same_path(directory, original_handle, kernel, nt):
    try:
        current = _walk_directory(directory, kernel, nt, create=False)
    except OSError:
        return False
    try:
        return (_information(kernel, current, directory=True) ==
                _information(kernel, original_handle, directory=True))
    except OSError:
        return False
    finally:
        kernel.CloseHandle(wintypes.HANDLE(current))


def _file_with_same_id(nt, kernel, directory_handle, name, original_handle):
    try:
        handle = _open_child(nt, directory_handle, name, access=GENERIC_READ | SYNCHRONIZE,
                             disposition=FILE_OPEN,
                             options=FILE_NON_DIRECTORY_FILE | FILE_SYNCHRONOUS_IO_NONALERT)
    except OSError:
        return False
    try:
        return (_information(kernel, handle, directory=False) ==
                _information(kernel, original_handle, directory=False))
    except OSError:
        return False
    finally:
        kernel.CloseHandle(wintypes.HANDLE(handle))


def _link_from_handle(kernel, source_handle, parent_handle, name):
    class FILE_LINK_INFO(ctypes.Structure):
        _fields_ = [("ReplaceIfExists", wintypes.BOOLEAN),
                    ("RootDirectory", wintypes.HANDLE),
                    ("FileNameLength", wintypes.DWORD),
                    ("FileName", ctypes.c_wchar * (len(name) + 1))]
    info = FILE_LINK_INFO()
    info.ReplaceIfExists = 0
    info.RootDirectory = wintypes.HANDLE(parent_handle)
    info.FileNameLength = len(name.encode("utf-16-le"))
    info.FileName = name
    if not kernel.SetFileInformationByHandle(wintypes.HANDLE(source_handle), FILE_LINK_INFO_CLASS,
                                              ctypes.byref(info), ctypes.sizeof(info)):
        raise ctypes.WinError(ctypes.get_last_error())


def _remove_temporary_by_handle(kernel, temp_handle):
    disposition = _FILE_DISPOSITION_INFO(1)
    if not kernel.SetFileInformationByHandle(wintypes.HANDLE(temp_handle), FILE_DISPOSITION_INFO_CLASS,
                                              ctypes.byref(disposition), ctypes.sizeof(disposition)):
        raise ctypes.WinError(ctypes.get_last_error())


def _source_reader(source, kernel):
    handle = kernel.CreateFileW(str(source), GENERIC_READ, FILE_SHARE_ALL, None, FILE_OPEN,
                                FILE_FLAG_OPEN_REPARSE_POINT, None)
    if handle is None or int(handle) == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        _information(kernel, int(handle), directory=False)
        fd = msvcrt.open_osfhandle(int(handle), os.O_BINARY | os.O_RDONLY)
        return os.fdopen(fd, "rb")
    except BaseException:
        kernel.CloseHandle(wintypes.HANDLE(handle))
        raise


def _read_existing_digest(nt, kernel, parent, name):
    handle = _open_child(nt, parent, name, access=GENERIC_READ | SYNCHRONIZE,
                         disposition=FILE_OPEN,
                         options=FILE_NON_DIRECTORY_FILE | FILE_SYNCHRONOUS_IO_NONALERT)
    try:
        _information(kernel, handle, directory=False)
        fd = msvcrt.open_osfhandle(handle, os.O_BINARY | os.O_RDONLY)
    except BaseException:
        kernel.CloseHandle(wintypes.HANDLE(handle))
        raise
    digest = hashlib.sha256()
    with os.fdopen(fd, "rb") as existing:
        while True:
            chunk = existing.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def copy_one_win32(source: Path, expected_checksum: str, dest_dir: Path):
    """No unsafe lexical fallback. Returns (copied, stable_error_code, message)."""
    if os.name != "nt":
        return False, "ATOMIC_PUBLICATION_UNAVAILABLE", "Win32 handle backend on non-Windows OS"
    try:
        kernel, nt = _apis()
        directory_handle = _walk_directory(dest_dir, kernel, nt, create=True)
    except OSError as exc:
        return False, "DEST_DIRECTORY_UNSAFE", f"Destination non sécurisable : {type(exc).__name__}"

    try:
        temp_name = f".tmp_{uuid.uuid4().hex}_{source.name}"
        try:
            with _source_reader(source, kernel) as reader:
                temp_handle = _open_child(
                    nt, directory_handle, temp_name, access=GENERIC_READ | GENERIC_WRITE | DELETE | SYNCHRONIZE,
                    disposition=FILE_CREATE,
                    options=FILE_NON_DIRECTORY_FILE | FILE_SYNCHRONOUS_IO_NONALERT,
                )
                temp_fd = None
                try:
                    _information(kernel, temp_handle, directory=False)
                    temp_fd = msvcrt.open_osfhandle(temp_handle, os.O_BINARY | os.O_RDWR)
                    with os.fdopen(temp_fd, "w+b", buffering=0) as temp:
                        temp_fd = None
                        temp_handle = int(msvcrt.get_osfhandle(temp.fileno()))
                        try:
                            shutil.copyfileobj(reader, temp, length=1024 * 1024)
                            temp.flush()
                            os.fsync(temp.fileno())
                            temp.seek(0)
                            digest = hashlib.sha256()
                            while True:
                                block = temp.read(1024 * 1024)
                                if not block:
                                    break
                                digest.update(block)
                            if digest.hexdigest() != expected_checksum:
                                return False, "CHECKSUM_MISMATCH", "SHA256 du temporaire invalide"
                            if not _file_with_same_id(nt, kernel, directory_handle, temp_name, temp_handle):
                                return False, "TEMP_PATH_TAMPERED", "Nom temporaire substitué"
                            if not _same_path(dest_dir, directory_handle, kernel, nt):
                                return False, "DEST_DIRECTORY_UNSAFE", "Destination substituée"
                            try:
                                _link_from_handle(kernel, temp_handle, directory_handle, source.name)
                            except OSError as exc:
                                if getattr(exc, "winerror", None) not in (ERROR_FILE_EXISTS, ERROR_ALREADY_EXISTS):
                                    return False, "ATOMIC_PUBLICATION_UNAVAILABLE", f"Publication non-écrasante indisponible : {type(exc).__name__}"
                                try:
                                    if _read_existing_digest(nt, kernel, directory_handle, source.name) != expected_checksum:
                                        return False, "DESTINATION_NAME_COLLISION", "Destination existante différente"
                                except OSError:
                                    return False, "EXISTING_BACKUP_UNREADABLE", "Destination existante dangereuse"
                            if not _same_path(dest_dir, directory_handle, kernel, nt):
                                return False, "DEST_DIRECTORY_UNSAFE", "Destination déplacée après publication"
                            return True, None, None
                        finally:
                            # Remove this exact owned temp file by HANDLE, not by
                            # attacker-substitutable pathname.
                            try:
                                _remove_temporary_by_handle(kernel, temp_handle)
                            except OSError:
                                pass
                finally:
                    # Once open_osfhandle takes ownership, fdopen owns the
                    # native handle. Do not CloseHandle it a second time.
                    if temp_fd is not None:
                        os.close(temp_fd)
                    elif temp_handle is not None and not isinstance(temp_handle, int):
                        kernel.CloseHandle(wintypes.HANDLE(temp_handle))
        except OSError as exc:
            return False, "COPY_FAILED", f"Copie Windows par handle refusée : {type(exc).__name__}"
    finally:
        kernel.CloseHandle(wintypes.HANDLE(directory_handle))
