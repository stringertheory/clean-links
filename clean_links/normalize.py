from typing import Union

from w3lib.url import canonicalize_url

from clean_links.clean import clean_url
from clean_links.unshorten import unshorten_url


def fragment_seems_important(url: str) -> bool:
    return True


def normalize_url(
    url: str,
    clean_before_unshortening: bool = False,
    unshorten_kwargs: Union[dict, None] = None,
    clean_kwargs: Union[dict, None] = None,
    canonicalize_kwargs: Union[dict, None] = None,
) -> str:
    # optionally remove e.g. tracking query parameters before first request
    if clean_before_unshortening:
        url = clean_url(url)

    # follow redirect chain and get the final request->response pair
    unshorten_kwargs = unshorten_kwargs or {}
    unshortened = unshorten_url(url, **unshorten_kwargs)

    # remove cruft after following any redirects
    clean_kwargs = clean_kwargs or {}
    cleaned = clean_url(unshortened["resolved"], **clean_kwargs)

    # sorty query params, normalize encodings, etc (see w3lib docs for detail)
    if canonicalize_kwargs is None:
        canonicalize_kwargs = {
            "keep_fragments": fragment_seems_important(cleaned)
        }
    final = canonicalize_url(cleaned, **canonicalize_kwargs)

    return final
