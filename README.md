# Clean Links

[![Release](https://img.shields.io/github/v/release/stringertheory/clean-links)](https://img.shields.io/github/v/release/stringertheory/clean-links)
[![Build status](https://img.shields.io/github/actions/workflow/status/stringertheory/clean-links/main.yml?branch=main)](https://github.com/stringertheory/clean-links/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/stringertheory/clean-links/branch/main/graph/badge.svg)](https://codecov.io/gh/stringertheory/clean-links)
[![Commit activity](https://img.shields.io/github/commit-activity/m/stringertheory/clean-links)](https://img.shields.io/github/commit-activity/m/stringertheory/clean-links)
[![License](https://img.shields.io/github/license/stringertheory/clean-links)](https://img.shields.io/github/license/stringertheory/clean-links)

Decide whether two links point at the same **resource** — so you can
de-duplicate and count links shared across feeds (a Nuzzel-style use case).
Shorteners hide the destination and per-share tracking parameters mean the final
URLs rarely match as strings; `clean-links` follows the redirects, strips the
cruft, and compares what's left.

Install with:

```shell
pip install clean_links
```

Are two shortened, tracking-tagged links the same article?

```pycon
>>> from clean_links import are_equivalent_sync
>>> are_equivalent_sync(
...     "https://bit.ly/some-short-link",
...     "https://trib.al/another-one",
... )
True
```

Or count how many links in a batch point at the same thing:

```pycon
>>> from clean_links import group_sync
>>> groups = group_sync([
...     "https://bit.ly/some-short-link",
...     "https://trib.al/another-one",
...     "https://example.com/unrelated",
... ])
>>> {key: len(members) for key, members in groups.items()}
{'https://www.bloomberg.com/news/articles/...': 2, 'https://example.com/unrelated': 1}
```

These calls make live network requests to follow the redirects. The library is
**async-first** — drop the `_sync` suffix for the coroutine API — and an
`Engine` with a `SqliteStore` resolves each link once and reuses it across runs.

See the documentation [here](https://stringertheory.github.io/clean-links).
