# clean-links

Some tools for cleaning up links.

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
