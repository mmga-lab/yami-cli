"""Milvus client wrapper."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pymilvus import MilvusClient

from yami.config.loader import get_token_from_env, get_uri_from_env, load_config
from yami.config.profiles import get_profile, load_profiles
from yami.exceptions import ConnectionError

if TYPE_CHECKING:
    from yami.core.context import CLIContext


class YamiClient:
    """Wrapper around MilvusClient with CLI-specific functionality."""

    def __init__(
        self,
        uri: str,
        token: str = "",
        db_name: str = "",
        timeout: float | None = None,
    ):
        """Initialize the client.

        Args:
            uri: Milvus server URI.
            token: Authentication token.
            db_name: Database name.
            timeout: Connection timeout in seconds.
        """
        self._uri = uri
        self._token = token
        self._db_name = db_name
        self._timeout = timeout

        try:
            self._client = MilvusClient(
                uri=uri,
                token=token,
                db_name=db_name if db_name else None,
                timeout=timeout,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Milvus at {uri}: {e}") from e

    @property
    def uri(self) -> str:
        """Get the server URI."""
        return self._uri

    def __getattr__(self, name: str) -> Any:
        """Proxy all methods to underlying MilvusClient."""
        return getattr(self._client, name)

    def close(self) -> None:
        """Close the connection."""
        self._client.close()


def create_client(ctx: "CLIContext") -> YamiClient:
    """Create a Milvus client from CLI context.

    Priority order:
    1. CLI arguments (--uri, --token, --db)
    2. Environment variables (MILVUS_URI, MILVUS_TOKEN)
    3. Profile settings (if --profile specified)
    4. Default profile from config
    """
    uri = ctx.uri
    token = ctx.token
    db = ctx.db

    # Check environment variables
    if not uri:
        uri = get_uri_from_env()
    if not token:
        token = get_token_from_env()

    # Check profile
    profile_name = ctx.profile
    if not profile_name:
        config = load_config()
        profile_name = config.default_profile

    if profile_name:
        try:
            profile = get_profile(profile_name)
            if not uri:
                uri = profile.uri
            if not token:
                token = profile.token
            if not db:
                db = profile.db
        except Exception:
            # Profile not found, continue without it
            pass

    # Validate
    if not uri:
        raise ConnectionError(
            "No Milvus URI specified. Use --uri, set MILVUS_URI environment variable, "
            "or configure a profile with 'yami config profile add'"
        )

    return YamiClient(
        uri=uri,
        token=token or "",
        db_name=db or "",
        timeout=ctx.timeout,
    )
