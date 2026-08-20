"""Structural interfaces for the injectable seams (fetcher, store, rate
limiter). Any object with the right async methods satisfies these."""

from typing import AsyncContextManager, Optional, Protocol, Tuple

from clean_links.fetcher import FetchResult


class Fetcher(Protocol):
    async def fetch(self, url: str, method: str) -> FetchResult: ...


class Store(Protocol):
    async def get_hop(self, url: str) -> Optional[Tuple]: ...

    async def put_hop(
        self,
        url: str,
        status: Optional[int],
        location: Optional[str],
        kind: str,
        fetched_at: float,
    ) -> None: ...

    async def get_resolved(self, url: str) -> Optional[Tuple]: ...

    async def put_resolved(
        self, url: str, endpoint: str, key: str, fetched_at: float
    ) -> None: ...

    async def close(self) -> None: ...


class RateLimiter(Protocol):
    def note_retry_after(self, url: str, seconds: float) -> None: ...

    def slot(self, url: str) -> AsyncContextManager[None]: ...
