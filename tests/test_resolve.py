import asyncio
import time

from clean_links import Engine, FakeFetcher, InMemoryStore
from clean_links.ratelimit import InMemoryRateLimiter

run = asyncio.run


class YieldingFetcher(FakeFetcher):
    """A FakeFetcher that yields to the event loop on every fetch, so that
    concurrent resolutions genuinely interleave (the plain FakeFetcher never
    suspends, so gathered tasks run start-to-finish one at a time)."""

    async def fetch(self, url, method):
        await asyncio.sleep(0)
        return await super().fetch(url, method)


def engine(fetcher, store=None):
    return Engine(
        fetcher=fetcher,
        store=store or InMemoryStore(),
        limiter=InMemoryRateLimiter(min_interval=0),
    )


def test_shorteners_to_same_article_merge():
    fetcher = FakeFetcher({
        "https://bit.ly/x": (301, "https://news.com/a?utm_source=fb"),
        "https://trib.al/y": (301, "https://news.com/a?utm_source=tw"),
    })
    eng = engine(fetcher)
    assert run(eng.are_equivalent("https://bit.ly/x", "https://trib.al/y"))


def test_different_articles_split():
    fetcher = FakeFetcher({
        "https://bit.ly/x": (301, "https://news.com/a"),
        "https://bit.ly/z": (301, "https://news.com/b"),
    })
    eng = engine(fetcher)
    assert not run(eng.are_equivalent("https://bit.ly/x", "https://bit.ly/z"))


def test_gateways_split_and_never_fetched():
    eng = engine(FakeFetcher({}))
    a = "https://l.facebook.com/l.php?u=https%3A%2F%2Fnews.com%2Fa&h=1"
    b = "https://l.facebook.com/l.php?u=https%3A%2F%2Fother.com%2Fb&h=2"
    assert not run(eng.are_equivalent(a, b))
    fetched = [url for url, _ in eng.fetcher.calls]
    assert not any(u.startswith("https://l.facebook.com") for u in fetched)


def test_redirect_loop_terminates():
    fetcher = FakeFetcher({
        "https://a.com/1": (301, "https://a.com/2"),
        "https://a.com/2": (301, "https://a.com/1"),
    })
    result = run(engine(fetcher).resolve("https://a.com/1"))
    assert result.reachable is False
    assert result.error == "redirect loop"


def test_unreachable_endpoint_falls_back_and_still_groups():
    fetcher = FakeFetcher(
        {
            "https://bit.ly/z": (301, "https://dead.example/final"),
            "https://s2.co/w": (301, "https://dead.example/final"),
        },
        fail={"https://dead.example/final"},
    )
    eng = engine(fetcher)
    result = run(eng.resolve("https://bit.ly/z"))
    assert result.reachable is False
    assert result.endpoint == "https://dead.example/final"
    assert run(eng.are_equivalent("https://bit.ly/z", "https://s2.co/w"))


def test_hop_cache_avoids_refetch_of_shared_tail():
    fetcher = FakeFetcher({
        "https://bit.ly/x": (301, "https://mid.com/1"),
        "https://mid.com/1": (301, "https://news.com/final"),
        "https://s2.co/y": (301, "https://mid.com/1"),
    })
    eng = engine(fetcher)
    run(eng.resolve("https://bit.ly/x"))
    seen = len(fetcher.calls)
    run(eng.resolve("https://s2.co/y"))
    fresh = [url for url, _ in fetcher.calls[seen:]]
    assert fresh == ["https://s2.co/y"]


def test_resolved_cache_avoids_reresolve():
    fetcher = FakeFetcher({"https://bit.ly/x": (301, "https://news.com/a")})
    eng = engine(fetcher)
    run(eng.canonical_key("https://bit.ly/x"))
    seen = len(fetcher.calls)
    run(eng.canonical_key("https://bit.ly/x"))
    assert len(fetcher.calls) == seen


def test_unreachable_resolution_not_pinned_in_resolved_cache():
    # A best-effort key from an UNREACHABLE resolution must not be memoized
    # in the resolved cache, or it would be served for success_ttl (30 days)
    # and never retried after the site recovers.
    store = InMemoryStore()
    fetcher = FakeFetcher(
        {"https://bit.ly/z": (301, "https://dead.example/final")},
        fail={"https://dead.example/final"},
    )
    eng = engine(fetcher, store=store)
    run(eng.canonical_key("https://bit.ly/z"))
    assert run(store.get_resolved("https://bit.ly/z")) is None


def test_resolved_cache_hit_does_not_reslide_ttl():
    # A cache hit must NOT re-stamp fetched_at; otherwise the success_ttl
    # slides forward on every access and a hot URL is never re-resolved.
    store = InMemoryStore()
    fetcher = FakeFetcher({"https://bit.ly/x": (301, "https://news.com/a")})
    eng = engine(fetcher, store=store)
    stamped = time.time()
    run(
        store.put_resolved(
            "https://bit.ly/x", "https://news.com/a", "cached-key", stamped
        )
    )
    run(eng.canonical_key("https://bit.ly/x"))
    _, _, fetched_at = run(store.get_resolved("https://bit.ly/x"))
    assert fetched_at == stamped


def test_persistent_http_error_is_not_a_reachable_endpoint():
    # A 503/429/4xx that survives the HEAD->GET and Retry-After retries is
    # not a usable Endpoint: it must resolve as reachable=False, not be
    # treated as a settled 200-style endpoint.
    fetcher = FakeFetcher({"https://x.com/a": (503, None)})
    eng = engine(fetcher)
    result = run(eng.resolve("https://x.com/a"))
    assert result.reachable is False


def test_http_error_endpoint_not_pinned_in_resolved_cache():
    store = InMemoryStore()
    fetcher = FakeFetcher({"https://x.com/a": (503, None)})
    eng = engine(fetcher, store=store)
    run(eng.canonical_key("https://x.com/a"))
    assert run(store.get_resolved("https://x.com/a")) is None


def test_group_coalesces_concurrent_shared_tail():
    # Two links sharing a redirect tail resolve concurrently in group();
    # the shared hops must be fetched once, not once per link (the hop cache
    # alone can't help -- nothing is cached yet while both are in flight).
    fetcher = YieldingFetcher({
        "https://bit.ly/x": (301, "https://mid.com/1"),
        "https://s2.co/y": (301, "https://mid.com/1"),
        "https://mid.com/1": (301, "https://news.com/final"),
    })
    eng = engine(fetcher)
    run(eng.group(["https://bit.ly/x", "https://s2.co/y"]))
    fetched = [url for url, _ in fetcher.calls]
    assert fetched.count("https://mid.com/1") == 1
    assert fetched.count("https://news.com/final") == 1


def test_retry_after_zero_still_retries():
    # Retry-After: 0 (and past HTTP-dates, which _parse_retry_after clamps to
    # 0.0) is a real "retry now" instruction, not a missing header -- the
    # retry must fire, so the 200 on the second attempt wins over the 503.
    fetcher = FakeFetcher({
        "https://x.com/a": [(503, None, 0.0), (200, None)],
    })
    eng = engine(fetcher)
    result = run(eng.resolve("https://x.com/a"))
    assert result.reachable is True
    assert [method for _, method in fetcher.calls] == ["HEAD", "HEAD"]


def test_group_isolates_non_fetcherror_failure():
    # One URL raising something OTHER than FetchError (a Store bug, a broken
    # fetcher, a redirection-rule quirk) must not abort the whole batch: it
    # forms its own bucket while the rest still group.
    class ExplodingFetcher(FakeFetcher):
        async def fetch(self, url, method):
            if url == "https://boom.co/x":
                raise ValueError("kaboom")
            return await super().fetch(url, method)

    fetcher = ExplodingFetcher({
        "https://bit.ly/ok1": (301, "https://news.com/a"),
        "https://bit.ly/ok2": (301, "https://news.com/a"),
    })
    groups = run(
        engine(fetcher).group([
            "https://boom.co/x",
            "https://bit.ly/ok1",
            "https://bit.ly/ok2",
        ])
    )
    merged = [members for members in groups.values() if len(members) > 1]
    assert merged == [["https://bit.ly/ok1", "https://bit.ly/ok2"]]
    assert ["https://boom.co/x"] in groups.values()


def test_query_sensitivity_does_not_refetch_unreachable():
    # An unreachable URL is deliberately NOT memoized in the resolved cache
    # (so it is retried after failure_ttl). The second, strip_query pass in
    # group(show_query_sensitivity=True) therefore re-runs resolve() for it --
    # but must not touch the network again: the hop cache (redirect entries
    # plus the negative "error" entry) absorbs the re-walk. Guards against a
    # regression that would turn the re-walk into a real double-fetch.
    fetcher = FakeFetcher(
        {"https://short/x": (301, "https://dead/end")},
        fail={"https://dead/end"},
    )
    run(engine(fetcher).group(["https://short/x"], show_query_sensitivity=True))
    # Each hop fetched exactly once, despite two resolution passes.
    assert fetcher.calls == [
        ("https://short/x", "HEAD"),
        ("https://dead/end", "HEAD"),
    ]


def test_group_survives_one_malformed_port_endpoint():
    # A malformed port in an endpoint URL (e.g. from a bad Location header)
    # must not abort the whole gathered batch -- the other URLs still group.
    fetcher = FakeFetcher({
        "https://bit.ly/bad": (301, "http://host:99999/x"),
        "https://bit.ly/ok1": (301, "https://news.com/a"),
        "https://bit.ly/ok2": (301, "https://news.com/a"),
    })
    eng = engine(fetcher)
    groups = run(
        eng.group([
            "https://bit.ly/bad",
            "https://bit.ly/ok1",
            "https://bit.ly/ok2",
        ])
    )
    merged = [members for members in groups.values() if len(members) > 1]
    assert merged == [["https://bit.ly/ok1", "https://bit.ly/ok2"]]
