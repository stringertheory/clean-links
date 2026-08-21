"""The fetcher seam: resolution talks to the network only through a
``fetch(url, method) -> FetchResult`` object, so the whole engine can be
driven deterministically by a fake in tests and by a real client (or the
caller's own injected fetcher) in production.
"""

import ssl
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

DEFAULT_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "en-US,en;q=0.9",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


class FetchError(Exception):
    """A hop could not be fetched (connection/timeout/transport error)."""


@dataclass
class FetchResult:
    status_code: int
    location: str | None  # absolute redirect target, or None
    url: str
    retry_after: float | None = None  # seconds, from Retry-After


def _parse_retry_after(value: str | None) -> float | None:
    """Seconds to wait, from a Retry-After header. Accepts both forms of
    RFC 7231: delta-seconds (an integer) and an HTTP-date, which is converted
    to seconds from now (clamped at 0 for a past instant)."""
    if value is None:
        return None
    value = value.strip()
    if value.isdigit():
        return float(value)
    try:
        # TypeError on <3.10, ValueError on >=3.10 for an unparseable date.
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:  # a "-0000" (unknown zone) date parses as naive
        when = when.replace(tzinfo=timezone.utc)
    delta = (when - datetime.now(timezone.utc)).total_seconds()
    return max(0.0, delta)


class FakeFetcher:
    """Serve a declarative redirect topology.

    ``routes`` maps a URL to ``(status, location[, retry_after])`` or to a
    *list* of such tuples consumed one per call (the last repeats). Unknown
    URLs resolve as a 200 Endpoint. URLs in ``fail`` raise ``FetchError``.
    ``calls`` records every ``(url, method)`` for assertions.
    """

    def __init__(
        self,
        routes: dict | None = None,
        fail: Iterable[str] | None = None,
    ) -> None:
        # Copy list-valued specs: fetch() consumes them with pop(), which
        # would otherwise drain the caller's dict (and any sibling fetcher
        # built from the same routes).
        self.routes = {
            url: list(spec) if isinstance(spec, list) else spec
            for url, spec in (routes or {}).items()
        }
        self.fail = set(fail or ())
        self.calls: list[tuple[str, str]] = []

    async def fetch(self, url: str, method: str) -> FetchResult:
        self.calls.append((url, method))
        if url in self.fail:
            raise FetchError("simulated connection failure: " + url)
        spec = self.routes.get(url)
        if spec is None or spec == []:
            return FetchResult(200, None, url)
        if isinstance(spec, list):
            item = spec[0] if len(spec) == 1 else spec.pop(0)
        else:
            item = spec
        status = item[0]
        location = item[1] if len(item) > 1 else None
        retry_after = item[2] if len(item) > 2 else None
        if location is not None:
            location = urljoin(url, location)
        return FetchResult(status, location, url, retry_after)


class HttpxFetcher:
    """Default fetcher, backed by a reusable ``httpx.AsyncClient``.

    Native async (no threadpool), so concurrency across hosts scales with the
    event loop rather than a thread pool. Holds a connection pool -- call
    ``aclose()`` when finished; the ``Engine`` and the module-level helpers do
    this automatically for the fetcher they create.
    """

    def __init__(
        self,
        verify: bool = True,
        timeout: float = 9.0,
        headers: dict | None = None,
    ) -> None:
        import httpx

        self._httpx = httpx
        self._client = httpx.AsyncClient(
            verify=verify,
            timeout=timeout,
            headers=headers or DEFAULT_HEADERS,
            follow_redirects=False,
        )

    async def fetch(self, url: str, method: str) -> FetchResult:
        # Stream so the body is never downloaded: we only need status +
        # Location + Retry-After from the response head.
        try:
            async with self._client.stream(method, url) as response:
                status = response.status_code
                location = response.headers.get("location")
                retry_after = _parse_retry_after(
                    response.headers.get("retry-after")
                )
        except (
            self._httpx.HTTPError,
            self._httpx.InvalidURL,
            ssl.SSLError,
        ) as exc:
            # InvalidURL is NOT an HTTPError subclass, so a malformed URL or
            # redirect Location (control char / bad host) would otherwise
            # escape as a raw exception and abort the whole group() batch.
            # ssl.SSLError likewise: a TLS handshake failure (e.g. a host that
            # serves an incomplete cert chain) can surface as a raw ssl error
            # rather than an httpx.ConnectError, so catch it here too -- else it
            # escapes uncaught and is never negatively cached (retried forever).
            msg = f"{type(exc).__name__}: {exc}"
            raise FetchError(msg) from exc
        if location is not None:
            location = urljoin(url, location)
        return FetchResult(status, location, url, retry_after)

    async def aclose(self) -> None:
        await self._client.aclose()
