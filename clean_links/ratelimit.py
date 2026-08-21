"""Per-host politeness: unbounded concurrency across hosts, throttled per
registrable domain -- a low max-in-flight plus a minimum interval between
requests, and Retry-After backoff. Single-process, in-memory default.
"""

import asyncio
import ipaddress
import time
from collections import OrderedDict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

# Compact, approximate public-suffix set: the multi-label TLDs and the
# user-content platforms where each subdomain is a separate site. Good
# enough to fold www./bare and keep every *.blogspot.com distinct; swap in
# a real PSL library for exhaustive coverage.
_MULTI_SUFFIXES = frozenset({
    "co.uk",
    "org.uk",
    "gov.uk",
    "ac.uk",
    "me.uk",
    "com.au",
    "net.au",
    "org.au",
    "edu.au",
    "gov.au",
    "co.jp",
    "or.jp",
    "ne.jp",
    "ac.jp",
    "go.jp",
    "co.nz",
    "com.br",
    "com.mx",
    "co.in",
    "co.za",
    "com.sg",
    "com.hk",
    "co.kr",
    "com.tr",
    "com.cn",
    "com.tw",
    "blogspot.com",
    "wordpress.com",
    "tumblr.com",
    "substack.com",
    "medium.com",
    "github.io",
    "gitlab.io",
    "netlify.app",
    "vercel.app",
})


def registrable_domain(host: str) -> str:
    host = (host or "").lower().rstrip(".")
    if not host:
        return host
    # An IP literal (v4 or v6) is its own registrable unit -- never fold it
    # by label, or unrelated addresses like 10.0.1.1 and 20.0.1.1 would
    # collapse to a shared "1.1" throttle bucket.
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        return host
    labels = host.split(".")
    if len(labels) <= 2:
        return host
    if ".".join(labels[-2:]) in _MULTI_SUFFIXES:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


class _DomainState:
    """Per-registrable-domain throttle state: a concurrency semaphore, an
    interval lock, the next-allowed and backoff timestamps, and a count of
    in-flight callers (holders + waiters) used to keep a busy domain from
    being evicted from the LRU map."""

    __slots__ = (
        "backoff_until",
        "in_flight",
        "interval_lock",
        "next_allowed",
        "sem",
    )

    def __init__(self, max_in_flight: int) -> None:
        self.sem = asyncio.Semaphore(max_in_flight)
        self.interval_lock = asyncio.Lock()
        self.next_allowed = 0.0
        self.backoff_until = 0.0
        self.in_flight = 0


class InMemoryRateLimiter:
    """Per-registrable-domain throttle. Domain state lives in an LRU map
    capped at ``max_domains`` so a long-lived limiter that sees a very large
    number of distinct hosts doesn't grow without bound; the least-recently-
    used idle domains are dropped first, and a domain with in-flight requests
    or an active backoff is never evicted (that would drop a held semaphore
    and let a fresh request exceed ``max_in_flight``)."""

    def __init__(
        self,
        max_in_flight: int = 2,
        min_interval: float = 1.0,
        max_domains: int = 1_000_000,
    ) -> None:
        self.max_in_flight = max_in_flight
        self.min_interval = min_interval
        self.max_domains = max_domains
        self._domains: OrderedDict[str, _DomainState] = OrderedDict()

    def _domain(self, url: str) -> str:
        return registrable_domain(urlsplit(url).hostname or "")

    def _touch(self, domain: str) -> _DomainState:
        """Get-or-create the domain's state and mark it most-recently-used.
        Does not evict -- callers evict after protecting this domain."""
        state = self._domains.get(domain)
        if state is None:
            state = _DomainState(self.max_in_flight)
            self._domains[domain] = state
        else:
            self._domains.move_to_end(domain)
        return state

    def _evict_if_needed(self) -> None:
        overflow = len(self._domains) - self.max_domains
        if overflow <= 0:
            return
        now = time.monotonic()
        victims: list[str] = []
        for domain, state in self._domains.items():  # least-recent first
            if state.in_flight == 0 and state.backoff_until <= now:
                victims.append(domain)
                if len(victims) >= overflow:
                    break
        for domain in victims:
            del self._domains[domain]

    def note_retry_after(self, url: str, seconds: float) -> None:
        state = self._touch(self._domain(url))
        state.backoff_until = time.monotonic() + seconds
        self._evict_if_needed()

    @asynccontextmanager
    async def slot(self, url: str) -> AsyncIterator[None]:
        state = self._touch(self._domain(url))
        # Mark in-flight BEFORE evicting so this domain can't be its own
        # (or a concurrent add's) eviction victim while we hold its slot.
        state.in_flight += 1
        self._evict_if_needed()
        try:
            async with state.sem:
                await self._wait_turn(state)
                yield
        finally:
            state.in_flight -= 1

    async def _wait_turn(self, state: _DomainState) -> None:
        async with state.interval_lock:
            now = time.monotonic()
            base = max(now, state.next_allowed, state.backoff_until)
            # Reserve the next slot for whoever comes after us.
            state.next_allowed = base + self.min_interval
        delay = base - time.monotonic()
        if delay > 0:
            await asyncio.sleep(delay)
