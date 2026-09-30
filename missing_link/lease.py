"""An OS-released per-database worker lease, not a second scheduling system."""
import os
from pathlib import Path


class WorkerLease:
    def __init__(self, database: Path):
        self.path = Path(str(database) + ".missing-link.lock")
        self.file = None

    def acquire(self) -> bool:
        if self.file is not None:
            return False
        stream = self.path.open("a+b")
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            stream.close()
            return False
        self.file = stream
        return True

    def release(self):
        if self.file is None:
            return
        stream, self.file = self.file, None
        try:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        finally:
            stream.close()
