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
    quiet: bool = False  # Suppress non-data output for agent-friendly mode

    _client: "YamiClient | None" = field(default=None, repr=False)

    def get_uri(self) -> str:
        """Get the effective Milvus URI.

        Returns the URI from profile or direct uri setting.
        Falls back to default localhost if not configured.
        """
        if self.uri:
            return self.uri
        if self.profile:
            from yami.config.profiles import get_profile

            profile_data = get_profile(self.profile)
            if profile_data and "uri" in profile_data:
                return profile_data["uri"]
        return "http://localhost:19530"

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
