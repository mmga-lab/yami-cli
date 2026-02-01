"""Tests for new database commands."""

from __future__ import annotations

from yami.cli.main import app


class TestDatabaseAlterProperties:
    """Test database alter-properties command."""

    def test_alter_properties(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            [
                "database",
                "alter-properties",
                "test_db",
                "-p",
                "database.replica.number=2",
            ],
        )

        assert result.exit_code == 0
        mock_client.alter_database_properties.assert_called_once_with(
            db_name="test_db",
            properties={"database.replica.number": 2},
        )

    def test_alter_properties_multiple(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            [
                "database",
                "alter-properties",
                "test_db",
                "-p",
                "prop1=value1",
                "-p",
                "prop2=true",
            ],
        )

        assert result.exit_code == 0
        call_args = mock_client.alter_database_properties.call_args
        props = call_args[1]["properties"]
        assert props["prop1"] == "value1"
        assert props["prop2"] is True

    def test_alter_properties_no_prop_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["database", "alter-properties", "test_db"])

        assert result.exit_code == 1

    def test_alter_properties_error(self, cli_runner, mock_context, mock_client):
        mock_client.alter_database_properties.side_effect = Exception("DB not found")

        result = cli_runner.invoke(
            app,
            ["database", "alter-properties", "test_db", "-p", "key=value"],
        )

        assert result.exit_code == 1


class TestDatabaseDropProperties:
    """Test database drop-properties command."""

    def test_drop_properties(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            ["database", "drop-properties", "test_db", "-k", "database.replica.number"],
        )

        assert result.exit_code == 0
        mock_client.drop_database_properties.assert_called_once_with(
            db_name="test_db",
            property_keys=["database.replica.number"],
        )

    def test_drop_properties_multiple(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            ["database", "drop-properties", "test_db", "-k", "key1", "-k", "key2"],
        )

        assert result.exit_code == 0
        mock_client.drop_database_properties.assert_called_once_with(
            db_name="test_db",
            property_keys=["key1", "key2"],
        )

    def test_drop_properties_no_key_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["database", "drop-properties", "test_db"])

        assert result.exit_code == 1
