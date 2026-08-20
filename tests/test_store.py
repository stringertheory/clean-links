import asyncio

from clean_links import Engine, FakeFetcher, InMemoryStore, SqliteStore
from clean_links.ratelimit import InMemoryRateLimiter

run = asyncio.run


def _round_trip(store):
    run(store.put_hop("u", 301, "v", "redirect", 123.0))
    assert run(store.get_hop("u")) == (301, "v", "redirect", 123.0)
    run(store.put_resolved("u", "e", "k", 123.0))
    assert run(store.get_resolved("u")) == ("e", "k", 123.0)


def test_inmemory_contract():
    _round_trip(InMemoryStore())


def test_sqlite_contract(tmp_path):
    store = SqliteStore(str(tmp_path / "cache.db"))
    _round_trip(store)
    run(store.close())


def test_sqlite_survives_reopen(tmp_path):
    path = str(tmp_path / "cache.db")
    first = SqliteStore(path)
    run(first.put_resolved("u", "https://n.com/a", "https://n.com/a", 9.0))
    run(first.close())
    second = SqliteStore(path)
    assert run(second.get_resolved("u")) == (
        "https://n.com/a",
        "https://n.com/a",
        9.0,
    )
    run(second.close())


def test_cross_run_reuse_needs_no_refetch(tmp_path):
    path = str(tmp_path / "cache.db")
    routes = {"https://bit.ly/x": (301, "https://news.com/a")}

    first = Engine(
        fetcher=FakeFetcher(dict(routes)),
        store=SqliteStore(path),
        limiter=InMemoryRateLimiter(min_interval=0),
    )
    run(first.canonical_key("https://bit.ly/x"))
    assert len(first.fetcher.calls) > 0
    run(first.store.close())

    # A fresh process/run: new engine, new fetcher, same SQLite file.
    second_fetcher = FakeFetcher(dict(routes))
    second = Engine(
        fetcher=second_fetcher,
        store=SqliteStore(path),
        limiter=InMemoryRateLimiter(min_interval=0),
    )
    run(second.canonical_key("https://bit.ly/x"))
    assert second_fetcher.calls == []  # served entirely from the cache
    run(second.store.close())
