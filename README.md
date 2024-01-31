# clean-links

[![Release](https://img.shields.io/github/v/release/stringertheory/clean-links)](https://img.shields.io/github/v/release/stringertheory/clean-links)
[![Build status](https://img.shields.io/github/actions/workflow/status/stringertheory/clean-links/main.yml?branch=main)](https://github.com/stringertheory/clean-links/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/stringertheory/clean-links/branch/main/graph/badge.svg)](https://codecov.io/gh/stringertheory/clean-links)
[![Commit activity](https://img.shields.io/github/commit-activity/m/stringertheory/clean-links)](https://img.shields.io/github/commit-activity/m/stringertheory/clean-links)
[![License](https://img.shields.io/github/license/stringertheory/clean-links)](https://img.shields.io/github/license/stringertheory/clean-links)

Tools for cleaning up links.

Remove cruft from URLs using the rules from
https://github.com/ClearURLs/Rules

Unshorten URLs by making requests and following redirects.

Are these two links the same?

```python
link1 = "https://trib.al/5m7fAg3"
link2 = "https://bit.ly/dirtylank"

resolved1 = unshorten_url(link1).get("resolved")
cleaned1 = clear_url(resolved1)

resolved2 = unshorten_url(link2).get("resolved")
cleaned2 = clear_url(resolved2)

cleaned1 == cleaned2  # True!
```
