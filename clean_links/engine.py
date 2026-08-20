"""The equivalence engine: resolve links to Endpoints, canonicalize, and
group by Resource. The Endpoint's Canonical key is the source of truth; the
redirect graph (in the Store) is a cache.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit

from clean_links.canonical import canonical_key as _key_of
from clean_links.fetcher import FetchError, FetchResult, HttpxFetcher
from clean_links.models import Hop, Options, Resolution
from clean_links.protocols import Fetcher, RateLimiter, Store
from clean_links.ratelimit import InMemoryRateLimiter
from clean_links.store import InMemoryStore
from clean_links.unwrap import unwrap


def _is_redirect(status: Optional[int]) -> bool:
    return status is not None and 300 <= status < 400


def _visit_key(url: str) -> str:
    """Light normalization for loop detection (host-lower, no fragment)."""
    split = urlsplit(url)
    host = (split.hostname or "").lower()
    return urlunsplit((split.scheme.lower(), host, split.path, split.query, ""))


class Engine:
    def __init__(
        self,
        fetcher: Optional[Fetcher] = None,
        store: Optional[Store] = None,
        limiter: Optional[RateLimiter] = None,
        options: Optional[Options] = None,
    ) -> None:
        self.options = options or Options()
        self._owns_fetcher = fetcher is None
        self._owns_store = store is None
        self.fetcher: Fetcher = fetcher or HttpxFetcher(
            verify=self.options.verify_tls, timeout=self.options.timeout
        )
        self.store: Store = store or InMemoryStore()
        self.limiter: RateLimiter = limiter or InMemoryRateLimiter()
        # In-flight hop fetches, so concurrent resolutions of a shared
        # redirect tail (within one group()) fetch it once, not once per link.
        self._inflight_hops: Dict[
            str, asyncio.Future[Tuple[Optional[int], Optional[str]]]
        ] = {}

    async def aclose(self) -> None:
        """Release resources the Engine created (its default fetcher's
        connection pool, its store). A fetcher/store you passed in is left
        for you to close."""
        if self._owns_fetcher:
            closer = getattr(self.fetcher, "aclose", None)
            if closer is not None:
                await closer()
        if self._owns_store:
            await self.store.close()

    # -- resolution -----------------------------------------------------

    async def resolve(self, url: str) -> Resolution:
        """Follow ``url``'s Redirect chain to its Endpoint, unwrapping any
        Gateways. On failure/loop/cap, ``endpoint`` is the deepest reachable
        Hop and ``reachable`` is False."""
        current = url
        chain = [current]
        hops: List[Hop] = []
        visited = {_visit_key(current)}

        for _ in range(self.options.max_redirects + 1):
            target = unwrap(current)
            if target is not None:
                await self.store.put_hop(
                    current, None, target, "unwrap", time.time()
                )
                hops.append(Hop(current, None, target, "unwrap"))
                nxt = target
            else:
                try:
                    status, location = await self._resolve_hop(current)
                except FetchError as exc:
                    hops.append(Hop(current, None, None, "error"))
                    return Resolution(
                        url, current, chain, False, str(exc), hops
                    )
                if _is_redirect(status) and location is not None:
                    hops.append(Hop(current, status, location, "redirect"))
                    nxt = location
                else:
                    hops.append(Hop(current, status, None, "endpoint"))
                    return Resolution(url, current, chain, True, None, hops)

            vkey = _visit_key(nxt)
            if vkey in visited:
                return Resolution(
                    url, nxt, [*chain, nxt], False, "redirect loop", hops
                )
            visited.add(vkey)
            chain.append(nxt)
            current = nxt

        return Resolution(
            url, current, chain, False, "too many redirects", hops
        )

    async def _resolve_hop(
        self, url: str
    ) -> Tuple[Optional[int], Optional[str]]:
        """Return (status, location) for one Hop, via the cache when fresh.
        Raises FetchError on transport failure (also negatively cached).
        Concurrent callers for the same URL share one in-flight fetch."""
        now = time.time()
        cached = await self.store.get_hop(url)
        if cached is not None:
            status, location, kind, fetched_at = cached
            if kind == "error":
                if now - fetched_at < self.options.failure_ttl:
                    raise FetchError("cached failure: " + url)
            elif now - fetched_at < self.options.success_ttl:
                return status, location
        inflight = self._inflight_hops.get(url)
        if inflight is None:
            inflight = asyncio.ensure_future(self._fetch_and_store(url, now))
            self._inflight_hops[url] = inflight
            inflight.add_done_callback(
                lambda _fut: self._inflight_hops.pop(url, None)
            )
        return await inflight

    async def _fetch_and_store(
        self, url: str, now: float
    ) -> Tuple[Optional[int], Optional[str]]:
        """Fetch one Hop, record it, and return (status, location). The
        coalescing/caching bookkeeping lives in _resolve_hop."""
        try:
            status, location = await self._fetch_following(url)
        except FetchError:
            await self.store.put_hop(url, None, None, "error", now)
            raise
        if _is_redirect(status) and location:
            await self.store.put_hop(url, status, location, "redirect", now)
            return status, location
        if status is not None and status >= 400:
            # A persistent HTTP error (surviving the HEAD->GET and
            # Retry-After retries in _fetch_once/_fetch_following) is not a
            # usable Endpoint. Cache it as a failure so it is retried under
            # failure_ttl instead of pinned as reachable for success_ttl.
            await self.store.put_hop(url, None, None, "error", now)
            msg = f"HTTP {status}: {url}"
            raise FetchError(msg)
        await self.store.put_hop(url, status, location, "endpoint", now)
        return status, location

    async def _fetch_following(
        self, url: str
    ) -> Tuple[Optional[int], Optional[str]]:
        result = await self._fetch_once(url, "HEAD")
        if result.status_code in (403, 405, 501):
            result = await self._fetch_once(url, "GET")
        return result.status_code, result.location

    async def _fetch_once(self, url: str, method: str) -> FetchResult:
        async with self.limiter.slot(url):
            result = await self.fetcher.fetch(url, method)
        if result.status_code in (429, 503) and result.retry_after is not None:
            self.limiter.note_retry_after(url, result.retry_after)
            async with self.limiter.slot(url):
                result = await self.fetcher.fetch(url, method)
        return result

    # -- equivalence & aggregation --------------------------------------

    async def _resolve_endpoint(self, url: str) -> Tuple[str, str]:
        """Return ``(endpoint, canonical key)`` for ``url``. A fresh
        resolved-cache entry is served as-is -- not re-resolved and not
        re-stamped, so success_ttl does not slide on every access. A new
        resolution is memoized only when reachable: an unreachable best-effort
        key would otherwise be pinned for success_ttl and never retried after
        the site recovers (the underlying hops still expire under failure_ttl,
        so re-resolving picks up the recovery)."""
        cached = await self.store.get_resolved(url)
        if cached is not None:
            endpoint, key, fetched_at = cached
            if time.time() - fetched_at < self.options.success_ttl:
                return str(endpoint), str(key)
        resolution = await self.resolve(url)
        endpoint = resolution.endpoint
        key = _key_of(endpoint, self.options)
        if resolution.reachable:
            await self.store.put_resolved(url, endpoint, key, time.time())
        return endpoint, key

    async def canonical_key(self, url: str, strip_query: bool = False) -> str:
        """The Canonical key of ``url``'s Resource: resolve to the Endpoint,
        then canonicalize. Two links are Equivalent iff their keys match.
        ``strip_query`` drops the query (used by the sensitivity report)."""
        endpoint, key = await self._resolve_endpoint(url)
        if strip_query:
            return _key_of(endpoint, self.options, strip_query=True)
        return key

    async def _safe_key(self, url: str, strip_query: bool = False) -> str:
        """``canonical_key`` for use inside a gathered batch: an unexpected
        error on one URL must not fail the whole ``group()``. ``resolve()``
        already turns transport failures into a best-effort key; this also
        contains anything else (a Store error, a malformed URL, a redirection
        rule quirk) by falling back to a stable per-URL key -- so a broken
        link forms its own singleton bucket instead of merging into another
        Resource (the model is biased away from a false merge)."""
        try:
            return await self.canonical_key(url, strip_query=strip_query)
        except Exception:
            try:
                return _key_of(url, self.options, strip_query=strip_query)
            except Exception:
                return url

    async def are_equivalent(self, a: str, b: str) -> bool:
        """True if ``a`` and ``b`` point at the same Resource."""
        key_a, key_b = await asyncio.gather(
            self.canonical_key(a), self.canonical_key(b)
        )
        return key_a == key_b

    async def group(
        self, urls: List[str], show_query_sensitivity: bool = False
    ) -> Dict:
        """Bucket ``urls`` by Canonical key (``{key: [urls]}``). With
        ``show_query_sensitivity=True`` return
        ``{"groups": ..., "query_sensitive": [...]}`` where the latter lists
        the clusters that would merge if the query string were dropped."""
        keys = await asyncio.gather(*[self._safe_key(u) for u in urls])
        groups: Dict[str, List[str]] = {}
        for url, key in zip(urls, keys):
            groups.setdefault(key, []).append(url)
        if not show_query_sensitivity:
            return groups

        stripped = await asyncio.gather(
            *[self._safe_key(u, strip_query=True) for u in urls]
        )
        key_of_url = dict(zip(urls, keys))
        by_stripped: Dict[str, List[str]] = {}
        for url, skey in zip(urls, stripped):
            by_stripped.setdefault(skey, []).append(url)
        # Clusters that would MERGE if query were dropped but are split now.
        sensitive = [
            members
            for members in by_stripped.values()
            if len({key_of_url[u] for u in members}) > 1
        ]
        return {"groups": groups, "query_sensitive": sensitive}


# -- module-level conveniences (fresh in-memory Engine per call) --------


async def resolve(url: str, **engine_kwargs: Any) -> Resolution:
    engine = Engine(**engine_kwargs)
    try:
        return await engine.resolve(url)
    finally:
        await engine.aclose()


async def canonical_key(url: str, **engine_kwargs: Any) -> str:
    engine = Engine(**engine_kwargs)
    try:
        return await engine.canonical_key(url)
    finally:
        await engine.aclose()


async def are_equivalent(a: str, b: str, **engine_kwargs: Any) -> bool:
    engine = Engine(**engine_kwargs)
    try:
        return await engine.are_equivalent(a, b)
    finally:
        await engine.aclose()


async def group(
    urls: List[str],
    show_query_sensitivity: bool = False,
    **engine_kwargs: Any,
) -> Dict:
    engine = Engine(**engine_kwargs)
    try:
        return await engine.group(
            urls, show_query_sensitivity=show_query_sensitivity
        )
    finally:
        await engine.aclose()


def resolve_sync(url: str, **engine_kwargs: Any) -> Resolution:
    return asyncio.run(resolve(url, **engine_kwargs))


def canonical_key_sync(url: str, **engine_kwargs: Any) -> str:
    return asyncio.run(canonical_key(url, **engine_kwargs))


def are_equivalent_sync(a: str, b: str, **engine_kwargs: Any) -> bool:
    return asyncio.run(are_equivalent(a, b, **engine_kwargs))


def group_sync(
    urls: List[str],
    show_query_sensitivity: bool = False,
    **engine_kwargs: Any,
) -> Dict:
    return asyncio.run(
        group(
            urls, show_query_sensitivity=show_query_sensitivity, **engine_kwargs
        )
    )
