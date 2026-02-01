"""Tests for privilege group commands."""

from __future__ import annotations

from yami.cli.main import app


class TestPrivilegeGroupList:
    """Test privilege-group list command."""

    def test_list_privilege_groups(self, cli_runner, mock_context, mock_client):
        mock_client.list_privilege_groups.return_value = ["group1", "group2"]

        result = cli_runner.invoke(app, ["privilege-group", "list"])

        assert result.exit_code == 0
        mock_client.list_privilege_groups.assert_called_once()

    def test_list_privilege_groups_empty(self, cli_runner, mock_context, mock_client):
        mock_client.list_privilege_groups.return_value = []

        result = cli_runner.invoke(app, ["privilege-group", "list"])

        assert result.exit_code == 0


class TestPrivilegeGroupCreate:
    """Test privilege-group create command."""

    def test_create_privilege_group(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["privilege-group", "create", "test_group"])

        assert result.exit_code == 0
        mock_client.create_privilege_group.assert_called_once_with("test_group")

    def test_create_privilege_group_error(self, cli_runner, mock_context, mock_client):
        mock_client.create_privilege_group.side_effect = Exception("Group exists")

        result = cli_runner.invoke(app, ["privilege-group", "create", "test_group"])

        assert result.exit_code == 1
        assert "Group exists" in result.output


class TestPrivilegeGroupDrop:
    """Test privilege-group drop command."""

    def test_drop_privilege_group_with_force(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["privilege-group", "drop", "test_group", "--force"])

        assert result.exit_code == 0
        mock_client.drop_privilege_group.assert_called_once_with("test_group")

    def test_drop_privilege_group_confirm(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["privilege-group", "drop", "test_group"], input="y\n")

        assert result.exit_code == 0
        mock_client.drop_privilege_group.assert_called_once()

    def test_drop_privilege_group_abort(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["privilege-group", "drop", "test_group"], input="n\n")

        assert result.exit_code == 1  # Aborted
        mock_client.drop_privilege_group.assert_not_called()


class TestPrivilegeGroupAdd:
    """Test privilege-group add command."""

    def test_add_privileges(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            ["privilege-group", "add", "test_group", "-p", "Insert", "-p", "Query"],
        )

        assert result.exit_code == 0
        mock_client.add_privileges_to_group.assert_called_once_with(
            group_name="test_group", privileges=["Insert", "Query"]
        )

    def test_add_privileges_no_privilege_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["privilege-group", "add", "test_group"])

        assert result.exit_code == 1
        assert "privilege" in result.output.lower()


class TestPrivilegeGroupRemove:
    """Test privilege-group remove command."""

    def test_remove_privileges(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            ["privilege-group", "remove", "test_group", "-p", "Insert"],
        )

        assert result.exit_code == 0
        mock_client.remove_privileges_from_group.assert_called_once_with(
            group_name="test_group", privileges=["Insert"]
        )

    def test_remove_privileges_no_privilege_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["privilege-group", "remove", "test_group"])

        assert result.exit_code == 1
