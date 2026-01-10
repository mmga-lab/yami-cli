"""Configuration settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConnectionProfile:
    """Connection profile configuration."""

    name: str
    uri: str
    token: str = ""
    db: str = ""
    description: str = ""


@dataclass
class YamiConfig:
    """Main configuration class."""

    default_profile: str = ""
    default_output: str = "table"
    timeout: float = 30.0
    mode: str = "human"  # "human" or "agent"
    profiles: dict[str, ConnectionProfile] = field(default_factory=dict)


def get_config_dir() -> Path:
    """Get configuration directory path."""
    config_dir = Path(os.environ.get("YAMI_CONFIG_DIR", Path.home() / ".yami"))
    return config_dir


def get_config_file() -> Path:
    """Get main config file path."""
    return get_config_dir() / "config.toml"


def get_profiles_file() -> Path:
    """Get profiles file path."""
    return get_config_dir() / "profiles.toml"
