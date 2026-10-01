"""Explicit-path SQLite connections with the existing transaction lifecycle."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def database_connection(path: Path | str) -> Iterator[sqlite3.Connection]:
    """Open the supplied path lazily, commit/roll back and always close."""
    connection = sqlite3.connect(path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
