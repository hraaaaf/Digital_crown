"""OS lifetime lock for one synthetic Bridge owner per marked TEMP fixture.

flock / msvcrt.locking are advisory and do not form a commercial Windows ACL
or protect against a malicious same-user process. The parent holds the fd.
The OS releases the lock when that parent dies, without stale PID cleanup.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path


class LabOwnerLockError(RuntimeError):
    pass


class LabOwnerLock:
    def __init__(self, fd: int):
        self._fd = fd

    @classmethod
    def acquire(cls, root: Path):
        lockfile = Path(root) / ".bridge-parent.lock"
        try:
            meta = lockfile.lstat()
            if not stat.S_ISREG(meta.st_mode) or stat.S_ISLNK(meta.st_mode):
                raise LabOwnerLockError("IMAGING_LAB_OWNER_LOCK_UNSAFE")
            if os.name == "nt" and bool(getattr(meta, "st_file_attributes", 0) &
                                        getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)):
                raise LabOwnerLockError("IMAGING_LAB_OWNER_LOCK_UNSAFE")
        except FileNotFoundError:
            pass
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(lockfile, flags, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise LabOwnerLockError("IMAGING_LAB_OWNER_LOCK_UNSAFE")
            if os.name == "nt":
                import msvcrt
                # A single byte is the locking range on Windows.
                if info.st_size == 0:
                    os.write(fd, b"1")
                os.lseek(fd, 0, os.SEEK_SET)
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                except OSError:
                    raise LabOwnerLockError("IMAGING_LAB_OWNER_ALREADY_ACTIVE") from None
            else:
                import fcntl
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError:
                    raise LabOwnerLockError("IMAGING_LAB_OWNER_ALREADY_ACTIVE") from None
            return cls(fd)
        except BaseException:
            os.close(fd)
            raise

    def close(self):
        fd, self._fd = self._fd, None
        if fd is not None:
            os.close(fd)
