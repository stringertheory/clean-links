"""Cleaning: remove parameters that don't change which Resource a URL
points at (tracking / marketing cruft), using the ClearURLs ruleset.

A means to deciding equivalence, not the product itself. Kept intact:
matched keys are stripped, every other parameter is preserved *verbatim*
(original percent-encoding and blank values untouched) so cleaning never
silently rewrites a URL it isn't targeting.
"""

from urllib.parse import unquote_plus, urlsplit, urlunsplit

from clean_links.config import read_config

clear_urls_rules = read_config()


def _filter_query(query: str, compiled_rules: list) -> str:
    """Drop query pairs whose (decoded) key matches a rule; keep the rest
    exactly as written."""
    if not query:
        return ""
    kept = []
    for pair in query.split("&"):
        if not pair:
            continue
        raw_key = pair.split("=", 1)[0]
        key = unquote_plus(raw_key)
        if any(rule.match(key) for rule in compiled_rules):
            continue
        kept.append(pair)
    return "&".join(kept)


def _filter_fragment(fragment: str, compiled_rules: list) -> str:
    """Strip tracking params from a fragment's query part (SPA routes such
    as ``#!/path?utm_x=1``); leave plain fragments untouched."""
    if "?" not in fragment:
        return fragment
    base, _, frag_query = fragment.partition("?")
    filtered = _filter_query(frag_query, compiled_rules)
    if filtered:
        return base + "?" + filtered
    return base


def match_provider(provider_name: str, url: str, rules: dict) -> bool:
    """True if the provider applies to ``url``: its urlPattern matches and
    no exception pattern matches. (Exceptions previously never applied.)"""
    if not rules["urlPattern"].match(url):
        return False
    return all(not exception.match(url) for exception in rules["exceptions"])


def clean_url(
    url: str, keep_query: bool = True, keep_fragment: bool = True
) -> str:
    for provider_name, rules in clear_urls_rules["providers"].items():
        if not match_provider(provider_name, url, rules):
            continue
        for raw_rule in rules["rawRules"]:
            url = raw_rule.sub("", url)
        split = urlsplit(url)
        if keep_query:
            query = _filter_query(split.query, rules["rules"])
        else:
            query = ""
        if keep_fragment and split.fragment:
            fragment = _filter_fragment(split.fragment, rules["rules"])
        else:
            fragment = ""
        url = urlunsplit((
            split.scheme,
            split.netloc,
            split.path,
            query,
            fragment,
        ))
    return url
