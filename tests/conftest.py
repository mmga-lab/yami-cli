"""Shared test fixtures for CLI tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from yami.core.context import reset_context


@pytest.fixture
def mock_client():
    """Create a mock Milvus client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_context(mock_client):
    """Mock the create_client function to return our mock client."""
    with patch("yami.core.client.create_client", return_value=mock_client):
        yield mock_client
    reset_context()


@pytest.fixture
def cli_runner():
    """Create a Typer CLI test runner."""
    from typer.testing import CliRunner

    return CliRunner()
