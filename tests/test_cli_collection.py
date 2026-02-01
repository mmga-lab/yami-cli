"""Tests for new collection commands."""

from __future__ import annotations

from yami.cli.main import app


class TestCollectionTruncate:
    """Test collection truncate command."""

    def test_truncate_with_force(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["collection", "truncate", "test_col", "--force"])

        assert result.exit_code == 0
        mock_client.truncate_collection.assert_called_once_with("test_col")

    def test_truncate_confirm(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["collection", "truncate", "test_col"], input="y\n")

        assert result.exit_code == 0
        mock_client.truncate_collection.assert_called_once()

    def test_truncate_abort(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["collection", "truncate", "test_col"], input="n\n")

        assert result.exit_code == 1
        mock_client.truncate_collection.assert_not_called()

    def test_truncate_error(self, cli_runner, mock_context, mock_client):
        mock_client.truncate_collection.side_effect = Exception("Not found")

        result = cli_runner.invoke(app, ["collection", "truncate", "test_col", "--force"])

        assert result.exit_code == 1


class TestCollectionAlterProperties:
    """Test collection alter-properties command."""

    def test_alter_properties_single(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            ["collection", "alter-properties", "test_col", "-p", "collection.ttl.seconds=86400"],
        )

        assert result.exit_code == 0
        mock_client.alter_collection_properties.assert_called_once_with(
            collection_name="test_col",
            properties={"collection.ttl.seconds": 86400},  # Parsed as int by JSON
        )

    def test_alter_properties_multiple(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            [
                "collection",
                "alter-properties",
                "test_col",
                "-p",
                "mmap.enabled=true",
                "-p",
                "lazyload.enabled=false",
            ],
        )

        assert result.exit_code == 0
        mock_client.alter_collection_properties.assert_called_once()

    def test_alter_properties_json_value(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            ["collection", "alter-properties", "test_col", "-p", "mmap.enabled=true"],
        )

        assert result.exit_code == 0
        # JSON parsed true -> Python True
        call_args = mock_client.alter_collection_properties.call_args
        assert call_args[1]["properties"]["mmap.enabled"] is True

    def test_alter_properties_no_prop_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["collection", "alter-properties", "test_col"])

        assert result.exit_code == 1
        assert "prop" in result.output.lower()


class TestCollectionDropProperties:
    """Test collection drop-properties command."""

    def test_drop_properties_single(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            ["collection", "drop-properties", "test_col", "-k", "collection.ttl.seconds"],
        )

        assert result.exit_code == 0
        mock_client.drop_collection_properties.assert_called_once_with(
            collection_name="test_col",
            property_keys=["collection.ttl.seconds"],
        )

    def test_drop_properties_multiple(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            [
                "collection",
                "drop-properties",
                "test_col",
                "-k",
                "key1",
                "-k",
                "key2",
            ],
        )

        assert result.exit_code == 0
        mock_client.drop_collection_properties.assert_called_once_with(
            collection_name="test_col",
            property_keys=["key1", "key2"],
        )

    def test_drop_properties_no_key_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["collection", "drop-properties", "test_col"])

        assert result.exit_code == 1


class TestCollectionAlterField:
    """Test collection alter-field command."""

    def test_alter_field(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            [
                "collection",
                "alter-field",
                "test_col",
                "my_field",
                "-p",
                "mmap.enabled=true",
            ],
        )

        assert result.exit_code == 0
        mock_client.alter_collection_field.assert_called_once_with(
            collection_name="test_col",
            field_name="my_field",
            field_params={"mmap.enabled": True},
        )

    def test_alter_field_no_prop_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["collection", "alter-field", "test_col", "my_field"])

        assert result.exit_code == 1


class TestCollectionAddFunction:
    """Test collection add-function command."""

    def test_add_function(self, cli_runner, mock_context, mock_client):
        func_json = '{"name": "bm25", "type": "BM25", "input_fields": ["text"]}'

        result = cli_runner.invoke(app, ["collection", "add-function", "test_col", func_json])

        assert result.exit_code == 0
        mock_client.add_collection_function.assert_called_once_with(
            collection_name="test_col",
            function={
                "name": "bm25",
                "type": "BM25",
                "input_fields": ["text"],
            },
        )

    def test_add_function_invalid_json(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["collection", "add-function", "test_col", "not json"])

        assert result.exit_code == 1
        assert "json" in result.output.lower()


class TestCollectionDropFunction:
    """Test collection drop-function command."""

    def test_drop_function_with_force(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app, ["collection", "drop-function", "test_col", "bm25", "--force"]
        )

        assert result.exit_code == 0
        mock_client.drop_collection_function.assert_called_once_with(
            collection_name="test_col",
            function_name="bm25",
        )

    def test_drop_function_confirm(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app, ["collection", "drop-function", "test_col", "bm25"], input="y\n"
        )

        assert result.exit_code == 0

    def test_drop_function_abort(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app, ["collection", "drop-function", "test_col", "bm25"], input="n\n"
        )

        assert result.exit_code == 1
        mock_client.drop_collection_function.assert_not_called()
