import asyncio
import time
from itertools import pairwise

from clean_links.ratelimit import InMemoryRateLimiter, registrable_domain

run = asyncio.run


def test_registrable_domain():
    assert registrable_domain("www.example.com") == "example.com"
    assert registrable_domain("a.b.example.co.uk") == "example.co.uk"
    assert registrable_domain("foo.blogspot.com") == "foo.blogspot.com"


def test_registrable_domain_keeps_ip_literals_distinct():
    # IP literals must not be folded by label, or unrelated addresses would
    # share one throttle bucket (10.0.1.1 and 20.0.1.1 both -> "1.1").
    assert registrable_domain("10.0.1.1") == "10.0.1.1"
    assert registrable_domain("20.0.1.1") == "20.0.1.1"
    assert registrable_domain("10.0.1.1") != registrable_domain("20.0.1.1")
    assert registrable_domain("2001:db8::1") == "2001:db8::1"


def test_min_interval_spaces_same_host():
    limiter = InMemoryRateLimiter(max_in_flight=5, min_interval=0.05)

    async def hit():
        async with limiter.slot("https://h.com/a"):
            return time.monotonic()

    async def main():
        return await asyncio.gather(*[hit() for _ in range(4)])

    times = sorted(run(main()))
    gaps = [b - a for a, b in pairwise(times)]
    assert min(gaps) >= 0.04


def test_max_in_flight_caps_same_host():
    limiter = InMemoryRateLimiter(max_in_flight=2, min_interval=0)
    state = {"current": 0, "peak": 0}

    async def hit():
        async with limiter.slot("https://h.com/a"):
            state["current"] += 1
            state["peak"] = max(state["peak"], state["current"])
            await asyncio.sleep(0.02)
            state["current"] -= 1

    run(_gather(hit, 6))
    assert state["peak"] <= 2


def test_cross_host_is_unbounded():
    limiter = InMemoryRateLimiter(max_in_flight=2, min_interval=0)
    state = {"current": 0, "peak": 0}

    async def hit(index):
        async with limiter.slot(f"https://h{index}.com/a"):
            state["current"] += 1
            state["peak"] = max(state["peak"], state["current"])
            await asyncio.sleep(0.02)
            state["current"] -= 1

    async def main():
        await asyncio.gather(*[hit(i) for i in range(6)])

    run(main())
    assert state["peak"] >= 3


async def _gather(make_coro, count):
    await asyncio.gather(*[make_coro() for _ in range(count)])


# -- LRU cap on per-domain state ----------------------------------------


def _visit(limiter, host):
    async def go():
        async with limiter.slot(f"https://{host}/"):
            pass

    run(go())


def test_default_max_domains_is_one_million():
    assert InMemoryRateLimiter().max_domains == 1_000_000


def test_lru_evicts_least_recently_used_over_cap():
    limiter = InMemoryRateLimiter(min_interval=0, max_domains=2)
    _visit(limiter, "a.com")
    _visit(limiter, "b.com")
    _visit(limiter, "c.com")  # over cap -> evict LRU (a.com)
    assert set(limiter._domains) == {"b.com", "c.com"}


def test_lru_reuse_protects_from_eviction():
    limiter = InMemoryRateLimiter(min_interval=0, max_domains=2)
    _visit(limiter, "a.com")
    _visit(limiter, "b.com")
    _visit(limiter, "a.com")  # a.com is now most-recently-used
    _visit(limiter, "c.com")  # evicts b.com, keeps a.com
    assert set(limiter._domains) == {"a.com", "c.com"}


def test_lru_never_evicts_in_flight_domain():
    # Evicting a domain whose semaphore is currently held would let a fresh
    # request exceed max_in_flight; a busy domain must survive over-cap.
    limiter = InMemoryRateLimiter(
        max_in_flight=1, min_interval=0, max_domains=1
    )

    async def scenario():
        async with limiter.slot("https://a.com/"):  # a.com held
            async with limiter.slot("https://b.com/"):  # cap=1 exceeded
                pass
            assert "a.com" in set(limiter._domains)

    run(scenario())


def test_max_in_flight_holds_under_eviction_pressure():
    # A hot domain hammered while many one-off domains churn through a tiny
    # cap must never exceed max_in_flight: eviction dropping its held
    # semaphore would let a fresh request build a second one.
    limiter = InMemoryRateLimiter(
        max_in_flight=2, min_interval=0, max_domains=1
    )
    state = {"current": 0, "peak": 0}

    async def hot():
        async with limiter.slot("https://h.com/a"):
            state["current"] += 1
            state["peak"] = max(state["peak"], state["current"])
            await asyncio.sleep(0.02)
            state["current"] -= 1

    async def churn(index):
        async with limiter.slot(f"https://other{index}.com/"):
            await asyncio.sleep(0)

    async def main():
        await asyncio.gather(
            *[hot() for _ in range(6)],
            *[churn(i) for i in range(20)],
        )

    run(main())
    assert state["peak"] <= 2
