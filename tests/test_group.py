import asyncio

from clean_links import Engine, FakeFetcher
from clean_links.ratelimit import InMemoryRateLimiter

run = asyncio.run


def engine(fetcher):
    return Engine(fetcher=fetcher, limiter=InMemoryRateLimiter(min_interval=0))


def test_group_counts_by_resource():
    fetcher = FakeFetcher({
        "https://bit.ly/x": (301, "https://news.com/a?utm_source=fb"),
        "https://trib.al/y": (301, "https://news.com/a?utm_source=tw"),
        "https://bit.ly/z": (301, "https://news.com/b"),
    })
    groups = run(
        engine(fetcher).group([
            "https://bit.ly/x",
            "https://trib.al/y",
            "https://bit.ly/z",
        ])
    )
    sizes = sorted(len(members) for members in groups.values())
    assert sizes == [1, 2]


def test_query_sensitivity_report():
    urls = [
        "https://shop.com/item?variant=red",
        "https://shop.com/item?variant=blue",
    ]
    result = run(
        engine(FakeFetcher({})).group(urls, show_query_sensitivity=True)
    )
    # Conservative default keeps the unknown param -> currently split...
    assert len(result["groups"]) == 2
    # ...but flagged as query-dependent (would merge if query were dropped).
    assert len(result["query_sensitive"]) == 1
    assert set(result["query_sensitive"][0]) == set(urls)
