"""Core data types for the link equivalence engine."""

from dataclasses import dataclass, field


@dataclass
class Hop:
    """A single URL within a Redirect chain."""

    url: str
    status: int | None
    location: str | None
    kind: str  # "redirect" | "unwrap" | "endpoint" | "error"


@dataclass
class Resolution:
    """The result of resolving a link to its Endpoint.

    ``endpoint`` is the deepest reachable Hop: a real Endpoint when
    ``reachable`` is True, or the deepest URL we could see before a
    failure/loop/cap when it is False (a best-effort key source).
    """

    url: str
    endpoint: str
    chain: list[str]
    reachable: bool
    error: str | None = None
    hops: list[Hop] = field(default_factory=list)


@dataclass
class Options:
    """Tunable policy for resolution and canonicalization."""

    max_redirects: int = 30
    verify_tls: bool = True
    timeout: float = 9.0
    # Canonical-key policy.
    fold_scheme: bool = True
    fold_www: bool = True
    fold_trailing_slash: bool = True
    # Cache lifetimes, seconds.
    success_ttl: float = 2592000.0  # 30 days
    failure_ttl: float = 21600.0  # 6 hours
