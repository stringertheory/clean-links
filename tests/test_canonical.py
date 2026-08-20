from clean_links.canonical import canonical_key


def test_folds_scheme_www_port_slash():
    a = canonical_key("HTTP://WWW.Example.com:80/a/")
    b = canonical_key("https://example.com/a")
    assert a == b


def test_strips_known_trackers():
    with_utm = canonical_key("https://x.com/a?utm_source=q")
    without = canonical_key("https://x.com/a")
    assert with_utm == without


def test_keeps_meaningful_unknown_params():
    # Conservative: unknown params are kept, so distinct Resources stay split.
    assert canonical_key("https://x.com/a?page=2") != canonical_key(
        "https://x.com/a?page=3"
    )


def test_spa_fragment_is_identity():
    assert canonical_key("https://app.x.com/#!/orgs/AAA") != canonical_key(
        "https://app.x.com/#!/orgs/BBB"
    )


def test_plain_fragment_dropped():
    assert canonical_key("https://x.com/a#section") == canonical_key(
        "https://x.com/a"
    )


def test_strip_query_option_ignores_query():
    a = canonical_key("https://x.com/a?id=1", strip_query=True)
    b = canonical_key("https://x.com/a?id=2", strip_query=True)
    assert a == b


def test_tolerates_out_of_range_port():
    # urlsplit(...).port raises ValueError for a port > 65535 (or non-numeric);
    # canonical_key must degrade gracefully instead of raising.
    assert canonical_key("http://host:99999/x")


def test_tolerates_non_numeric_port():
    assert canonical_key("http://host:abc/x")


def test_ipv6_host_keeps_brackets():
    # split.hostname strips the brackets from an IPv6 literal; the key must
    # restore them so it stays a well-formed, re-parseable URL.
    assert canonical_key("https://[2001:db8::1]/a") == "https://[2001:db8::1]/a"


def test_ipv6_host_with_port_is_unambiguous():
    # Without brackets, "::1:8080" is an ambiguous host:port boundary.
    assert canonical_key("https://[::1]:8080/x") == "https://[::1]:8080/x"


def test_ipv6_default_port_folded():
    assert canonical_key("https://[2001:db8::1]:443/a") == canonical_key(
        "https://[2001:db8::1]/a"
    )
