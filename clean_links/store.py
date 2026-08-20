"""Persistence: the redirect graph as a cache.

``hop`` is the source of truth -- raw network observations (from-URL ->
to-URL, status). ``resolved`` is a derived memo (URL -> Endpoint + Canonical
key) that can be recomputed from hops plus the policy without re-crawling.
Two implementations behind one interface: in-memory (default) and SQLite.

Records are plain tuples:
  hop:      (status, location, kind, fetched_at)
  resolved: (endpoint, key, fetched_at)
"""

import asyncio
from typing import Dict, Optional, Tuple


class InMemoryStore:
    def __init__(self) -> None:
        self._hops: Dict[str, Tuple] = {}
        self._resolved: Dict[str, Tuple] = {}

    async def get_hop(self, url: str) -> Optional[Tuple]:
        return self._hops.get(url)

    async def put_hop(
        self,
        url: str,
        status: Optional[int],
        location: Optional[str],
        kind: str,
        fetched_at: float,
    ) -> None:
        self._hops[url] = (status, location, kind, fetched_at)

    async def get_resolved(self, url: str) -> Optional[Tuple]:
        return self._resolved.get(url)

    async def put_resolved(
        self, url: str, endpoint: str, key: str, fetched_at: float
    ) -> None:
        self._resolved[url] = (endpoint, key, fetched_at)

    async def close(self) -> None:
        pass


class SqliteStore:
    """Single-file, single-process cache. WAL mode; writes serialized by an
    asyncio lock (SQLite calls are fast/local for this workload)."""

    def __init__(self, path: str) -> None:
        import sqlite3

        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS hop ("
            "url TEXT PRIMARY KEY, status INTEGER, location TEXT, "
            "kind TEXT, fetched_at REAL)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS resolved ("
            "url TEXT PRIMARY KEY, endpoint TEXT, key TEXT, fetched_at REAL)"
        )
        self._conn.commit()
        self._lock = asyncio.Lock()

    async def get_hop(self, url: str) -> Optional[Tuple]:
        cursor = self._conn.execute(
            "SELECT status, location, kind, fetched_at FROM hop WHERE url=?",
            (url,),
        )
        row = cursor.fetchone()
        return tuple(row) if row is not None else None

    async def put_hop(
        self,
        url: str,
        status: Optional[int],
        location: Optional[str],
        kind: str,
        fetched_at: float,
    ) -> None:
        async with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO hop "
                "(url, status, location, kind, fetched_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (url, status, location, kind, fetched_at),
            )
            self._conn.commit()

    async def get_resolved(self, url: str) -> Optional[Tuple]:
        cursor = self._conn.execute(
            "SELECT endpoint, key, fetched_at FROM resolved WHERE url=?",
            (url,),
        )
        row = cursor.fetchone()
        return tuple(row) if row is not None else None

    async def put_resolved(
        self, url: str, endpoint: str, key: str, fetched_at: float
    ) -> None:
        async with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO resolved "
                "(url, endpoint, key, fetched_at) VALUES (?, ?, ?, ?)",
                (url, endpoint, key, fetched_at),
            )
            self._conn.commit()

    async def close(self) -> None:
        self._conn.close()
