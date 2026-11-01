"""Fail-closed SQLite sidecar inspection for the synthetic Imaging LAB.

The Python stdlib SQLite VFS opens database/WAL/SHM by *path*. These checks
catch reparse and hardlink attacks before/after each connection, but do NOT
make Windows SQLite operations directory-handle-relative or race-free.
A Windows installer must enforce restricted service identity and NTFS ACLs.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import os
import stat

from tools.imaging_gateway.windows_scoped_read_lab import directory_identity


class SQLiteBoundaryError(RuntimeError):
    pass


def inspect_sqlite_boundary(
    private: Path, database: Path, expected_directory: tuple[int, int],
    expected_windows_directory=None,
) -> dict[str, tuple[int, int]]:
    """Check root and all SQLite file names, without following any sidecar link.

    Capture identity of each existing file (including -wal, -shm, -journal)
    to spot root or database replacement. Legitimate SQLite sidecars can be
    created/deleted by the engine between inspections, so their identities
    are not treated as durable across independently opened connections.
    """
    try:
        root = private.lstat()
    except OSError as error:
        raise SQLiteBoundaryError("SQLITE_PRIVATE_ROOT_MISSING") from error
    if (not stat.S_ISDIR(root.st_mode) or stat.S_ISLNK(root.st_mode)
            or (os.name == "nt" and bool(
                getattr(root, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            )) or (root.st_dev, root.st_ino) != expected_directory):
        raise SQLiteBoundaryError("SQLITE_PRIVATE_ROOT_CHANGED")
    if os.name == "nt":
        try:
            if directory_identity(private) != expected_windows_directory:
                raise SQLiteBoundaryError("SQLITE_NATIVE_ROOT_CHANGED")
        except OSError as error:
            raise SQLiteBoundaryError("SQLITE_NATIVE_ROOT_UNAVAILABLE") from error

    if database.parent != private:
        raise SQLiteBoundaryError("SQLITE_DATABASE_OUTSIDE_PRIVATE")
    names = ("", "-wal", "-shm", "-journal")
    identities = {}
    for suffix in names:
        file = private / (database.name + suffix)
        try:
            metadata = file.lstat()
        except FileNotFoundError:
            continue
        except OSError as error:
            raise SQLiteBoundaryError("SQLITE_FILE_STAT_FAILED") from error
        if (not stat.S_ISREG(metadata.st_mode)
                or stat.S_ISLNK(metadata.st_mode)
                or metadata.st_nlink != 1
                or (os.name == "nt" and bool(
                    getattr(metadata, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
                ))):
            raise SQLiteBoundaryError("SQLITE_FILE_UNSAFE")
        identities[suffix] = (metadata.st_dev, metadata.st_ino)
    return identities


@contextmanager
def pin_windows_sqlite_path(private: Path, expected_windows_directory, *, database: Path | None = None, require_database: bool = False):
    """Temporarily prevent rename of Windows SQLite directory ancestors.

    Ancestor directory handles (and the existing main DB file if provided)
    are opened WITHOUT FILE_SHARE_DELETE and held until SQLite closes.
    This blocks ordinary Windows rename/delete sharing of those objects.
    The WAL/SHM/journal leaves, in-place writes, alternate hardlink actors,
    installer ACL and malicious same-user interference remain uncontained.
    This is partial LAB hardening, NOT a custom SQLite VFS.
    """
    if os.name != "nt":
        yield
        return

    from tools.imaging_gateway.windows_scoped_read_lab import _win_api
    ctypes, _, kernel, _, FileInfo, *_ = _win_api()
    private = Path(private).absolute()
    if expected_windows_directory is None:
        raise SQLiteBoundaryError("SQLITE_EXPECTED_WINDOWS_DIRECTORY_MISSING")
    handles = []
    try:
        for directory in (*reversed(private.parents), private):
            handle = kernel.CreateFileW(
                str(directory), 0x80,  # FILE_READ_ATTRIBUTES
                0x1 | 0x2,  # SHARE_READ | SHARE_WRITE; intentionally NO SHARE_DELETE
                None, 3,  # OPEN_EXISTING
                0x02000000 | 0x00200000,  # BACKUP_SEMANTICS | OPEN_REPARSE_POINT
                None,
            )
            if handle in (None, ctypes.c_void_p(-1).value):
                raise SQLiteBoundaryError("SQLITE_PATH_PIN_OPEN_DENIED")
            handles.append(handle)
            info = FileInfo()
            if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
                raise SQLiteBoundaryError("SQLITE_PATH_PIN_ID_UNAVAILABLE")
            if not info.attributes & 0x10 or info.attributes & 0x400:
                raise SQLiteBoundaryError("SQLITE_PATH_PIN_UNSAFE_COMPONENT")
            if directory == private:
                observed = (info.volume, (info.index_high << 32) | info.index_low)
                if observed != expected_windows_directory:
                    raise SQLiteBoundaryError("SQLITE_PATH_PIN_PRIVATE_ID_CHANGED")
        if database is not None:
            database = Path(database).absolute()
            if database.parent != private:
                raise SQLiteBoundaryError("SQLITE_PATH_PIN_DB_OUTSIDE_PRIVATE")
            # Opening the main database for attributes without SHARE_DELETE
            # prevents rename/unlink of this leaf during sqlite3 VFS activity.
            # First trusted bootstrap may create a truly missing database;
            # once identity is pinned, a missing database is always fatal.
            file_handle = kernel.CreateFileW(
                str(database), 0x80,  # FILE_READ_ATTRIBUTES
                0x1 | 0x2,  # SHARE_READ | SHARE_WRITE; NO SHARE_DELETE
                None, 3,  # OPEN_EXISTING, never create
                0x00200000,  # FILE_FLAG_OPEN_REPARSE_POINT
                None,
            )
            if file_handle in (None, ctypes.c_void_p(-1).value):
                err = ctypes.get_last_error()
                if require_database or err != 2:  # ERROR_FILE_NOT_FOUND
                    raise SQLiteBoundaryError("SQLITE_PATH_PIN_DB_OPEN_DENIED")
            else:
                handles.append(file_handle)
                details = FileInfo()
                if not kernel.GetFileInformationByHandle(file_handle, ctypes.byref(details)):
                    raise SQLiteBoundaryError("SQLITE_PATH_PIN_DB_ID_UNAVAILABLE")
                if (details.attributes & (0x10 | 0x400) or details.links != 1):
                    raise SQLiteBoundaryError("SQLITE_PATH_PIN_DB_UNSAFE")
        yield
    finally:
        for handle in reversed(handles):
            kernel.CloseHandle(handle)
