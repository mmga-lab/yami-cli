"""Tests for new query commands."""

from __future__ import annotations

from unittest.mock import MagicMock

from yami.cli.main import app


class TestQuerySearchIterator:
    """Test query search-iterator command."""

    def test_search_iterator_with_random_vector(self, cli_runner, mock_context, mock_client):
        # Mock collection schema for dimension detection
        mock_client.describe_collection.return_value = {
            "fields": [
                {"name": "id", "type": "INT64"},
                {"name": "embedding", "type": "FLOAT_VECTOR", "params": {"dim": 128}},
            ]
        }

        # Create mock iterator
        mock_iterator = MagicMock()
        mock_iterator.next.side_effect = [
            [{"id": 1, "distance": 0.1, "entity": {"name": "a"}}],
            [{"id": 2, "distance": 0.2, "entity": {"name": "b"}}],
            [],  # Empty to stop iteration
        ]
        mock_client.search_iterator.return_value = mock_iterator

        result = cli_runner.invoke(
            app, ["query", "search-iterator", "test_col", "--random", "--limit", "10"]
        )

        assert result.exit_code == 0
        mock_client.search_iterator.assert_called_once()
        mock_iterator.close.assert_called_once()

    def test_search_iterator_with_vector(self, cli_runner, mock_context, mock_client):
        mock_iterator = MagicMock()
        mock_iterator.next.side_effect = [
            [{"id": 1, "distance": 0.1, "entity": {}}],
            [],
        ]
        mock_client.search_iterator.return_value = mock_iterator

        vector = "[" + ",".join(["0.1"] * 128) + "]"
        result = cli_runner.invoke(
            app, ["query", "search-iterator", "test_col", "--vector", vector]
        )

        assert result.exit_code == 0
        mock_iterator.close.assert_called_once()

    def test_search_iterator_with_filter(self, cli_runner, mock_context, mock_client):
        mock_client.describe_collection.return_value = {
            "fields": [
                {"name": "embedding", "type": "FLOAT_VECTOR", "params": {"dim": 4}},
            ]
        }
        mock_iterator = MagicMock()
        mock_iterator.next.side_effect = [[]]
        mock_client.search_iterator.return_value = mock_iterator

        result = cli_runner.invoke(
            app,
            [
                "query",
                "search-iterator",
                "test_col",
                "--random",
                "--filter",
                "age > 20",
            ],
        )

        assert result.exit_code == 0
        call_kwargs = mock_client.search_iterator.call_args[1]
        assert call_kwargs["filter"] == "age > 20"

    def test_search_iterator_with_batch_size(self, cli_runner, mock_context, mock_client):
        mock_client.describe_collection.return_value = {
            "fields": [
                {"name": "embedding", "type": "FLOAT_VECTOR", "params": {"dim": 4}},
            ]
        }
        mock_iterator = MagicMock()
        mock_iterator.next.side_effect = [[]]
        mock_client.search_iterator.return_value = mock_iterator

        result = cli_runner.invoke(
            app,
            [
                "query",
                "search-iterator",
                "test_col",
                "--random",
                "--batch-size",
                "500",
            ],
        )

        assert result.exit_code == 0
        call_kwargs = mock_client.search_iterator.call_args[1]
        assert call_kwargs["batch_size"] == 500

    def test_search_iterator_no_vector_source_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["query", "search-iterator", "test_col"])

        assert result.exit_code == 1
        assert "vector" in result.output.lower() or "random" in result.output.lower()

    def test_search_iterator_multiple_sources_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            ["query", "search-iterator", "test_col", "--random", "--vector", "[0.1,0.2]"],
        )

        assert result.exit_code == 1

    def test_search_iterator_error(self, cli_runner, mock_context, mock_client):
        mock_client.describe_collection.return_value = {
            "fields": [
                {"name": "embedding", "type": "FLOAT_VECTOR", "params": {"dim": 4}},
            ]
        }
        mock_client.search_iterator.side_effect = Exception("Search failed")

        result = cli_runner.invoke(app, ["query", "search-iterator", "test_col", "--random"])

        assert result.exit_code == 1
        assert "Search failed" in result.output
