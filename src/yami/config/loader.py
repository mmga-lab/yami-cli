"""Configuration loading utilities."""

from __future__ import annotations

import os
import sys
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from yami.config.settings import YamiConfig, get_config_dir, get_config_file


def _ensure_config_dir() -> None:
    """Ensure config directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> YamiConfig:
    """Load main configuration from file."""
    config_file = get_config_file()

    if not config_file.exists():
        return YamiConfig()

    with open(config_file, "rb") as f:
        data = tomllib.load(f)

    defaults = data.get("defaults", {})

    return YamiConfig(
        default_profile=defaults.get("profile", ""),
        default_output=defaults.get("output", "table"),
        timeout=defaults.get("timeout", 30.0),
    )


def save_config(config: YamiConfig) -> None:
    """Save configuration to file."""
    _ensure_config_dir()
    config_file = get_config_file()

    data: dict[str, Any] = {
        "defaults": {
            "profile": config.default_profile,
            "output": config.default_output,
            "timeout": config.timeout,
        }
    }

    with open(config_file, "wb") as f:
        tomli_w.dump(data, f)


def get_config_value(key: str) -> Any:
    """Get a specific configuration value.

    Args:
        key: Dot-separated key path (e.g., 'defaults.profile').
    """
    config_file = get_config_file()

    if not config_file.exists():
        return None

    with open(config_file, "rb") as f:
        data = tomllib.load(f)

    # Navigate the key path
    parts = key.split(".")
    current = data

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


def set_config_value(key: str, value: Any) -> None:
    """Set a specific configuration value.

    Args:
        key: Dot-separated key path (e.g., 'defaults.profile').
        value: The value to set.
    """
    _ensure_config_dir()
    config_file = get_config_file()

    if config_file.exists():
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
    else:
        data = {}

    # Navigate and set the key path
    parts = key.split(".")
    current = data

    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value

    with open(config_file, "wb") as f:
        tomli_w.dump(data, f)


def get_uri_from_env() -> str | None:
    """Get Milvus URI from environment variable."""
    return os.environ.get("MILVUS_URI") or os.environ.get("YAMI_URI")


def get_token_from_env() -> str | None:
    """Get Milvus token from environment variable."""
    return os.environ.get("MILVUS_TOKEN") or os.environ.get("YAMI_TOKEN")
