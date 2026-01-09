"""Connection profile management."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w

from yami.config.settings import ConnectionProfile, get_config_dir, get_profiles_file
from yami.exceptions import ProfileNotFoundError


def _expand_env_vars(value: str) -> str:
    """Expand environment variables in a string.

    Supports ${VAR_NAME} syntax.
    """
    pattern = r"\$\{([^}]+)\}"

    def replace_env(match: re.Match) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return re.sub(pattern, replace_env, value)


def _ensure_config_dir() -> None:
    """Ensure config directory exists."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)


def load_profiles() -> dict[str, ConnectionProfile]:
    """Load all connection profiles from file."""
    profiles_file = get_profiles_file()

    if not profiles_file.exists():
        return {}

    with open(profiles_file, "rb") as f:
        data = tomllib.load(f)

    profiles = {}
    profiles_data = data.get("profiles", {})

    for name, profile_data in profiles_data.items():
        # Expand environment variables
        uri = _expand_env_vars(profile_data.get("uri", ""))
        token = _expand_env_vars(profile_data.get("token", ""))

        profiles[name] = ConnectionProfile(
            name=name,
            uri=uri,
            token=token,
            db=profile_data.get("db", ""),
            description=profile_data.get("description", ""),
        )

    return profiles


def save_profiles(profiles: dict[str, ConnectionProfile]) -> None:
    """Save profiles to file."""
    _ensure_config_dir()
    profiles_file = get_profiles_file()

    # Convert to TOML structure
    data: dict[str, Any] = {"profiles": {}}

    for name, profile in profiles.items():
        data["profiles"][name] = {
            "uri": profile.uri,
        }
        if profile.token:
            data["profiles"][name]["token"] = profile.token
        if profile.db:
            data["profiles"][name]["db"] = profile.db
        if profile.description:
            data["profiles"][name]["description"] = profile.description

    with open(profiles_file, "wb") as f:
        tomli_w.dump(data, f)


def get_profile(name: str) -> ConnectionProfile:
    """Get a specific profile by name."""
    profiles = load_profiles()

    if name not in profiles:
        raise ProfileNotFoundError(f"Profile '{name}' not found")

    return profiles[name]


def add_profile(profile: ConnectionProfile) -> None:
    """Add or update a profile."""
    profiles = load_profiles()
    profiles[profile.name] = profile
    save_profiles(profiles)


def remove_profile(name: str) -> None:
    """Remove a profile."""
    profiles = load_profiles()

    if name not in profiles:
        raise ProfileNotFoundError(f"Profile '{name}' not found")

    del profiles[name]
    save_profiles(profiles)


def list_profile_names() -> list[str]:
    """List all profile names."""
    return list(load_profiles().keys())
