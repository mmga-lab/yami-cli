"""Tests for replica commands."""

from __future__ import annotations

from yami.cli.main import app


class TestReplicaDescribe:
    """Test replica describe command."""

    def test_describe_replica(self, cli_runner, mock_context, mock_client):
        mock_client.describe_replica.return_value = {
            "collection": "test_col",
            "replicas": [{"replica_id": 1, "node_ids": [1, 2]}],
        }

        result = cli_runner.invoke(app, ["replica", "describe", "test_col"])

        assert result.exit_code == 0
        mock_client.describe_replica.assert_called_once_with("test_col")

    def test_describe_replica_error(self, cli_runner, mock_context, mock_client):
        mock_client.describe_replica.side_effect = Exception("Collection not found")

        result = cli_runner.invoke(app, ["replica", "describe", "missing_col"])

        assert result.exit_code == 1
        assert "Collection not found" in result.output


class TestReplicaTransfer:
    """Test replica transfer command."""

    def test_transfer_replica(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            ["replica", "transfer", "rg1", "rg2", "-c", "test_col", "-n", "1"],
        )

        assert result.exit_code == 0
        mock_client.transfer_replica.assert_called_once_with(
            source_group="rg1",
            target_group="rg2",
            collection_name="test_col",
            num_replicas=1,
        )

    def test_transfer_replica_default_num(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app,
            ["replica", "transfer", "rg1", "rg2", "-c", "test_col"],
        )

        assert result.exit_code == 0
        mock_client.transfer_replica.assert_called_once_with(
            source_group="rg1",
            target_group="rg2",
            collection_name="test_col",
            num_replicas=1,
        )

    def test_transfer_replica_missing_collection(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["replica", "transfer", "rg1", "rg2"])

        assert result.exit_code == 2  # Missing required option

    def test_transfer_replica_error(self, cli_runner, mock_context, mock_client):
        mock_client.transfer_replica.side_effect = Exception("Transfer failed")

        result = cli_runner.invoke(
            app,
            ["replica", "transfer", "rg1", "rg2", "-c", "test_col"],
        )

        assert result.exit_code == 1
        assert "Transfer failed" in result.output
