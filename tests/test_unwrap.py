import re

import clean_links.unwrap as unwrap_mod
from clean_links.unwrap import unwrap


def test_curated_google():
    url = "https://www.google.com/url?q=https%3A%2F%2Fn.com%2Fa&sa=D"
    assert unwrap(url) == "https://n.com/a"


def test_curated_facebook():
    url = "https://l.facebook.com/l.php?u=https%3A%2F%2Fn.com%2Fb&h=x"
    assert unwrap(url) == "https://n.com/b"


def test_structural_known_target_key():
    url = "https://svc.com/go?url=https%3A%2F%2Fn.com%2Fc"
    assert unwrap(url) == "https://n.com/c"


def test_incidental_url_param_not_unwrapped():
    # `ref` is not a known target key -> stay conservative, don't unwrap.
    assert unwrap("https://blog.com/post?ref=https://twitter.com/x") is None


def test_plain_url_is_not_a_gateway():
    assert unwrap("https://n.com/a?id=5") is None


def test_curated_rule_does_not_fire_on_unrelated_host():
    # A provider's `redirections` capture must only apply when that
    # provider's urlPattern matches. The vendored rutracker rule
    # `.*url=([^&]*)` would otherwise unwrap ANY URL whose query merely
    # contains `url=` as a substring (here, `content_url=`), producing a
    # false merge onto the captured host.
    url = "https://news.com/article?content_url=https%3A%2F%2Fother.com%2Fx"
    assert unwrap(url) is None


def test_curated_optional_group_matching_none_is_skipped(monkeypatch):
    # A redirections rule whose first capture group is optional can match a
    # URL while group(1) is None; unquote(None) would raise TypeError (which
    # is unguarded in resolve() and aborts the whole batch). Such a match
    # must be skipped, not crash.
    provider = {
        "urlPattern": re.compile(r"^https://gw\.test/"),
        "exceptions": [],
        "redirections": [re.compile(r"^https://gw\.test/go(?:\?u=([^&]+))?")],
    }
    monkeypatch.setitem(
        unwrap_mod.clear_urls_rules, "providers", {"gw": provider}
    )
    assert unwrap("https://gw.test/go") is None
