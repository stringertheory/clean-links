# API reference

See the [home page](index.md) for a tour and [the
glossary](glossary.md) for the vocabulary (Resource, Endpoint,
Canonical key, Gateway, …).

Everything is **async-first**. Each top-level function has a `*_sync`
counterpart (`resolve_sync`, `canonical_key_sync`, `are_equivalent_sync`,
`group_sync`) that simply wraps it in `asyncio.run`.

For repeated use -- persistence across runs, a shared per-host rate
limiter, an injected fetcher -- construct an
[`Engine`](#clean_links.engine.Engine) and call its methods directly.

## Engine

::: clean_links.engine.Engine
options:
show_source: false
heading_level: 3
members: - resolve - canonical_key - are_equivalent - group

## Cleaning

::: clean_links.clean.clean_url
options:
show_source: false
heading_level: 3

## Data types

::: clean_links.models.Resolution
options:
show_source: false
heading_level: 3

::: clean_links.models.Options
options:
show_source: false
heading_level: 3
