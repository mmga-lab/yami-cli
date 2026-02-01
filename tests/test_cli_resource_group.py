"""Tests for resource group commands."""

from __future__ import annotations

from yami.cli.main import app


class TestResourceGroupList:
    """Test resource-group list command."""

    def test_list_resource_groups(self, cli_runner, mock_context, mock_client):
        mock_client.list_resource_groups.return_value = ["__default_resource_group", "rg1"]

        result = cli_runner.invoke(app, ["resource-group", "list"])

        assert result.exit_code == 0
        mock_client.list_resource_groups.assert_called_once()


class TestResourceGroupDescribe:
    """Test resource-group describe command."""

    def test_describe_resource_group(self, cli_runner, mock_context, mock_client):
        mock_client.describe_resource_group.return_value = {
            "name": "rg1",
            "capacity": 1,
            "num_available_node": 1,
        }

        result = cli_runner.invoke(app, ["resource-group", "describe", "rg1"])

        assert result.exit_code == 0
        mock_client.describe_resource_group.assert_called_once_with("rg1")


class TestResourceGroupCreate:
    """Test resource-group create command."""

    def test_create_resource_group(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["resource-group", "create", "test_rg"])

        assert result.exit_code == 0
        mock_client.create_resource_group.assert_called_once_with("test_rg")

    def test_create_resource_group_with_config(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            [
                "resource-group",
                "create",
                "test_rg",
                "-c",
                '{"requests": {"node_num": 1}}',
            ],
        )

        assert result.exit_code == 0
        mock_client.create_resource_group.assert_called_once_with(
            "test_rg", config={"requests": {"node_num": 1}}
        )

    def test_create_resource_group_invalid_json(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["resource-group", "create", "test_rg", "-c", "invalid"])

        assert result.exit_code == 1
        assert "json" in result.output.lower()


class TestResourceGroupDrop:
    """Test resource-group drop command."""

    def test_drop_resource_group_with_force(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["resource-group", "drop", "test_rg", "--force"])

        assert result.exit_code == 0
        mock_client.drop_resource_group.assert_called_once_with("test_rg")

    def test_drop_resource_group_confirm(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["resource-group", "drop", "test_rg"], input="y\n")

        assert result.exit_code == 0


class TestResourceGroupUpdate:
    """Test resource-group update command."""

    def test_update_resource_groups(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            ["resource-group", "update", '{"rg1": {"requests": {"node_num": 2}}}'],
        )

        assert result.exit_code == 0
        mock_client.update_resource_groups.assert_called_once_with(
            {"rg1": {"requests": {"node_num": 2}}}
        )

    def test_update_resource_groups_invalid_json(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["resource-group", "update", "not json"])

        assert result.exit_code == 1
