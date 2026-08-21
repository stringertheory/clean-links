"""Gateway detection and Unwrapping.

A Gateway carries its target in its own URL, so it is resolved by *reading*
the target out of the URL (no request), not by following a redirect. Only
done when the target can be extracted reliably (parses as an absolute URL):

  tier 1 (structural) -- a *known target-named* query param whose value is
    itself a URL. Conservative on purpose: unknown param names are ignored
    so an incidental URL-valued param never triggers a wrong unwrap.
  tier 2 (curated) -- the vendored ClearURLs ``redirections`` capture rules.

Learned high-fan-out detection (tier 3) is intentionally NOT here: it can
only *flag* a node for exclusion, never Unwrap, and belongs to the future
Model-A escalation (out of scope).
"""

import base64
import binascii
from urllib.parse import parse_qsl, unquote, urlsplit

from clean_links.clean import clear_urls_rules, match_provider

# Strongly redirect-target-named keys only (kept conservative on purpose:
# e.g. `q` and `r` are omitted because they are commonly search/ref keys).
_TARGET_KEYS = frozenset({
    "url",
    "u",
    "to",
    "target",
    "dest",
    "destination",
    "redirect",
    "redirect_uri",
    "redirecturl",
    "out",
    "goto",
    "returnurl",
})


def _is_abs_url(value: str) -> bool:
    try:
        split = urlsplit(value)
    except ValueError:
        return False
    return split.scheme in ("http", "https") and bool(split.netloc)


def _maybe_url(value: str) -> str | None:
    value = value.strip()
    if _is_abs_url(value):
        return value
    decoded = unquote(value)
    if decoded != value and _is_abs_url(decoded):
        return decoded
    try:
        padded = value + "=" * (-len(value) % 4)
        raw = base64.urlsafe_b64decode(padded).decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError):
        raw = ""
    if _is_abs_url(raw):
        return raw
    return None


def _structural_target(url: str) -> str | None:
    split = urlsplit(url)
    for key, value in parse_qsl(split.query, keep_blank_values=True):
        if key.lower() in _TARGET_KEYS:
            target = _maybe_url(value)
            if target is not None:
                return target
    return None


def _curated_target(url: str) -> str | None:
    for name, rules in clear_urls_rules["providers"].items():
        # A provider's redirect-capture rules are host-scoped: only apply
        # them when that provider's urlPattern matches, or a rule like
        # rutracker's `.*url=([^&]*)` would unwrap any URL containing `url=`.
        if not match_provider(name, url, rules):
            continue
        for pattern in rules.get("redirections", []):
            match = pattern.match(url)
            if not match or not match.groups():
                continue
            # An optional capture group (e.g. `(?:x=(...))?`) can match while
            # group(1) is None -- unquote(None) would raise TypeError, which
            # is unguarded in resolve() and aborts the whole group() batch.
            captured = match.group(1)
            if captured is None:
                continue
            target = unquote(captured)
            if _is_abs_url(target):
                return target
    return None


def unwrap(url: str) -> str | None:
    """Return the Gateway's target if it can be reliably extracted, else
    None (meaning: not a detectable Gateway -- follow it as a redirect)."""
    target = _curated_target(url)
    if target is not None:
        return target
    return _structural_target(url)
