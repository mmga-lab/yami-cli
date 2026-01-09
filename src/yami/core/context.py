"""CLI context management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from yami.core.client import YamiClient


@dataclass
class CLIContext:
    """CLI execution context."""

    uri: str | None = None
    token: str | None = None
    db: str | None = None
    profile: str | None = None
    output: str = "table"
    timeout: float = 30.0

    _client: "YamiClient | None" = field(default=None, repr=False)

    def get_client(self) -> "YamiClient":
        """Get or create a Milvus client."""
        if self._client is None:
            from yami.core.client import create_client

            self._client = create_client(self)
        return self._client

    def close(self) -> None:
        """Close the client connection."""
        if self._client is not None:
            self._client.close()
            self._client = None


# Global context storage
_context: CLIContext | None = None


def get_context() -> CLIContext:
    """Get the current CLI context."""
    global _context
    if _context is None:
        _context = CLIContext()
    return _context


def set_context(ctx: CLIContext) -> None:
    """Set the current CLI context."""
    global _context
    _context = ctx


def reset_context() -> None:
    """Reset the context."""
    global _context
    if _context is not None:
        _context.close()
    _context = None
