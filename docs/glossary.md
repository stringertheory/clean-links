# Clean Links

`clean-links` determines whether two links point at the same **Resource**, so
that shared or collected links can be de-duplicated and counted, e.g. "how many
people shared this?" or "how often does this appear in my RSS feeds?" Following redirects is central to that job.

## Language

### Links & resources

**Resource**:
The destination a link points at: the page or article a person would consider
"the same thing." Sameness is about _destination identity_, not byte-for-byte
equality of the fetched content.
_Avoid_: page, document, target (when ambiguous)

**Equivalent** (of two links):
Two links are equivalent when they point at the same Resource. Determining this
is the clean-links' primary job.
_Avoid_: identical, duplicate, same URL

**Canonical key**:
The stable string that identifies a Resource; two links are Equivalent exactly
when they share a Canonical key. Computed from a link's Endpoint.
_Avoid_: fingerprint, hash, normalized URL

**Cleaning**:
Removing the parts of a URL that don't change which Resource it points at
(tracking / marketing parameters, ClearURLs-style). A means to deciding
equivalence, not the product itself.
_Avoid_: sanitizing, normalizing, scrubbing

### Redirects

**Redirect chain**:
The ordered sequence of URLs traversed from an input link to its Endpoint by
following redirects.
_Avoid_: redirect path, redirect trail

**Hop**:
A single URL within a Redirect chain.

**Endpoint**:
The final URL a Redirect chain resolves to (the Hop with no further redirect).
_Avoid_: final URL, destination URL, resolved

**Shortener**:
A Hop whose only purpose is to redirect to another URL (e.g. `bit.ly`,
`trib.al`, `t.co`).
_Avoid_: link wrapper, redirect service

**Gateway**:
A Hop that redirects to a target encoded in its own query string (e.g.
`google.com/url?q=…`, `l.facebook.com/l.php?u=…`). Because many different targets
share one Gateway host+path, treating a shared Gateway as evidence of equivalence
causes a False merge.
_Avoid_: interstitial, redirector

**Unwrapping**:
Resolving a Gateway by reading its target out of the URL (no network request
needed), as opposed to _following_ a redirect, which requires a request. Only
done when the target can be extracted reliably (it parses as an absolute URL).
_Avoid_: extracting, decoding

### Equivalence quality

**False merge**:
Treating two _different_ Resources as equivalent — inflates counts. The most
damaging error for the counting use case.
_Avoid_: over-merge, collision

**False split**:
Treating _one_ Resource as two non-equivalent links — undercounts.
_Avoid_: under-merge, miss
