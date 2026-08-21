"""Compute a Canonical key for a URL: the stable string that identifies a
Resource. Two links are Equivalent exactly when their keys match.

Deliberately biased away from a False merge: only *known* trackers are
stripped (unknown params are kept), so distinct Resources stay split.
"""

from urllib.parse import urlsplit, urlunsplit

from w3lib.url import canonicalize_url

from clean_links.clean import clean_url
from clean_links.models import Options


def _keep_fragment(fragment: str) -> bool:
    # Preserve SPA/hashbang fragments (the fragment IS the Resource there);
    # drop ordinary anchors.
    return fragment.startswith("!") or fragment.startswith("/")


def canonical_key(
    url: str,
    options: Options | None = None,
    strip_query: bool = False,
) -> str:
    options = options or Options()
    cleaned = clean_url(url)
    split = urlsplit(cleaned)

    orig_scheme = split.scheme.lower()
    scheme = orig_scheme
    if options.fold_scheme and scheme in ("http", "https"):
        scheme = "https"

    host = (split.hostname or "").lower()
    if options.fold_www and host.startswith("www."):
        host = host[4:]

    # split.hostname strips the brackets from an IPv6 literal; restore them
    # so the rebuilt netloc stays a well-formed URL and the host:port
    # boundary is unambiguous.
    host_in_netloc = f"[{host}]" if ":" in host else host

    netloc = host_in_netloc
    try:
        port = split.port
    except ValueError:
        # Malformed port (non-numeric or out of 0-65535, e.g. from a bad
        # Location header): drop it rather than raise -- a raise here would
        # abort the whole gathered batch in Engine.group().
        port = None
    # Default-port test uses the ORIGINAL scheme (:80 is default for http).
    is_default = (orig_scheme == "https" and port == 443) or (
        orig_scheme == "http" and port == 80
    )
    if port is not None and not is_default:
        netloc = f"{host_in_netloc}:{port}"

    path = split.path
    if options.fold_trailing_slash and len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/") or "/"

    query = "" if strip_query else split.query
    keep_frag = _keep_fragment(split.fragment)
    fragment = split.fragment if keep_frag else ""

    rebuilt = urlunsplit((scheme, netloc, path, query, fragment))
    return str(canonicalize_url(rebuilt, keep_fragments=keep_frag))
