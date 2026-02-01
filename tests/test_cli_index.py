"""Tests for new index commands."""

from __future__ import annotations

from yami.cli.main import app


class TestIndexAlterProperties:
    """Test index alter-properties command."""

    def test_alter_properties(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            [
                "index",
                "alter-properties",
                "test_col",
                "my_index",
                "-p",
                "mmap.enabled=true",
            ],
        )

        assert result.exit_code == 0
        mock_client.alter_index_properties.assert_called_once_with(
            collection_name="test_col",
            index_name="my_index",
            properties={"mmap.enabled": True},
        )

    def test_alter_properties_multiple(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            [
                "index",
                "alter-properties",
                "test_col",
                "my_index",
                "-p",
                "prop1=value1",
                "-p",
                "prop2=123",
            ],
        )

        assert result.exit_code == 0
        call_args = mock_client.alter_index_properties.call_args
        assert call_args[1]["properties"]["prop1"] == "value1"
        assert call_args[1]["properties"]["prop2"] == 123

    def test_alter_properties_no_prop_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["index", "alter-properties", "test_col", "my_index"])

        assert result.exit_code == 1

    def test_alter_properties_error(self, cli_runner, mock_context, mock_client):
        mock_client.alter_index_properties.side_effect = Exception("Index not found")

        result = cli_runner.invoke(
            app,
            [
                "index",
                "alter-properties",
                "test_col",
                "my_index",
                "-p",
                "mmap.enabled=true",
            ],
        )

        assert result.exit_code == 1
        assert "Index not found" in result.output


class TestIndexDropProperties:
    """Test index drop-properties command."""

    def test_drop_properties(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            [
                "index",
                "drop-properties",
                "test_col",
                "my_index",
                "-k",
                "mmap.enabled",
            ],
        )

        assert result.exit_code == 0
        mock_client.drop_index_properties.assert_called_once_with(
            collection_name="test_col",
            index_name="my_index",
            property_keys=["mmap.enabled"],
        )

    def test_drop_properties_multiple(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            [
                "index",
                "drop-properties",
                "test_col",
                "my_index",
                "-k",
                "key1",
                "-k",
                "key2",
            ],
        )

        assert result.exit_code == 0
        mock_client.drop_index_properties.assert_called_once_with(
            collection_name="test_col",
            index_name="my_index",
            property_keys=["key1", "key2"],
        )

    def test_drop_properties_no_key_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["index", "drop-properties", "test_col", "my_index"])

        assert result.exit_code == 1
