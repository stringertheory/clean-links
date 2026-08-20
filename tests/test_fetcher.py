import asyncio
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import pytest

from clean_links.fetcher import (
    FakeFetcher,
    FetchError,
    HttpxFetcher,
    _parse_retry_after,
)

run = asyncio.run


# -- Retry-After parsing ------------------------------------------------


def test_retry_after_none():
    assert _parse_retry_after(None) is None


def test_retry_after_integer_seconds():
    assert _parse_retry_after("120") == 120.0


def test_retry_after_http_date_gmt_is_seconds_until():
    # IMF-fixdate form real servers send; this instant is in the past, so the
    # delay clamps to 0 rather than going negative.
    assert _parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT") == 0.0


def test_retry_after_http_date_future():
    when = datetime.now(timezone.utc) + timedelta(seconds=120)
    secs = _parse_retry_after(format_datetime(when))
    assert secs is not None
    assert 60 < secs <= 120


def test_retry_after_garbage_is_none():
    assert _parse_retry_after("not-a-date") is None


# -- HttpxFetcher converts transport errors to FetchError ---------------


def test_invalid_url_becomes_fetch_error():
    # httpx.InvalidURL is NOT an HTTPError subclass; a malformed URL (here a
    # control char in the host) must still surface as FetchError so one bad
    # link can't escape as a raw exception and abort a whole group() batch.
    fetcher = HttpxFetcher()

    async def go():
        try:
            await fetcher.fetch("https://exa\tmple.com/x", "HEAD")
        finally:
            await fetcher.aclose()

    with pytest.raises(FetchError):
        run(go())


# -- FakeFetcher must not mutate the caller's routes --------------------


def test_fakefetcher_does_not_drain_shared_routes():
    # Two fetchers built from the same routes dict must not share the inner
    # list: draining one must not consume the other's (or the caller's).
    routes = {
        "https://x.com/a": [
            (301, "https://one.com/"),
            (301, "https://two.com/"),
        ]
    }
    f1 = FakeFetcher(routes)
    f2 = FakeFetcher(routes)
    run(f1.fetch("https://x.com/a", "HEAD"))  # consumes first item
    run(f1.fetch("https://x.com/a", "HEAD"))  # now on the repeating tail
    r = run(f2.fetch("https://x.com/a", "HEAD"))
    assert r.location == "https://one.com/"
    assert len(routes["https://x.com/a"]) == 2  # caller's list untouched
