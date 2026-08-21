"""clean-links: decide whether two links point at the same Resource, and
group/count them. See docs/glossary.md for vocabulary.
"""

from clean_links.canonical import canonical_key as key_of
from clean_links.clean import clean_url
from clean_links.engine import (
    Engine,
    are_equivalent,
    are_equivalent_sync,
    canonical_key,
    canonical_key_sync,
    group,
    group_sync,
    resolve,
    resolve_sync,
)
from clean_links.fetcher import FakeFetcher, HttpxFetcher
from clean_links.models import Hop, Options, Resolution
from clean_links.store import InMemoryStore, SqliteStore

__all__ = [
    "Engine",
    "FakeFetcher",
    "Hop",
    "HttpxFetcher",
    "InMemoryStore",
    "Options",
    "Resolution",
    "SqliteStore",
    "are_equivalent",
    "are_equivalent_sync",
    "canonical_key",
    "canonical_key_sync",
    "clean_url",
    "group",
    "group_sync",
    "key_of",
    "resolve",
    "resolve_sync",
]

__version__ = "0.2.2"
