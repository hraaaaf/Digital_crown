"""Fail-closed SQLite sidecar inspection for the synthetic Imaging LAB.

The Python stdlib SQLite VFS opens database/WAL/SHM by *path*. These checks
catch reparse and hardlink attacks before/after each connection, but do NOT
make Windows SQLite operations directory-handle-relative or race-free.
A Windows installer must enforce restricted service identity and NTFS ACLs.
"""
from __future__ import annotations

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
