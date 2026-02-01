"""Tests for new flush commands."""

from __future__ import annotations

from yami.cli.main import app


class TestFlushState:
    """Test flush state command."""

    def test_flush_state_complete(self, cli_runner, mock_context, mock_client):
        mock_client.get_flush_all_state.return_value = True

        result = cli_runner.invoke(app, ["flush", "state"])

        assert result.exit_code == 0
        mock_client.get_flush_all_state.assert_called_once()
        # Should show success message when flushed
        assert "complete" in result.output.lower() or "success" in result.output.lower()

    def test_flush_state_incomplete(self, cli_runner, mock_context, mock_client):
        mock_client.get_flush_all_state.return_value = False

        result = cli_runner.invoke(app, ["flush", "state"])

        assert result.exit_code == 0
        mock_client.get_flush_all_state.assert_called_once()

    def test_flush_state_error(self, cli_runner, mock_context, mock_client):
        mock_client.get_flush_all_state.side_effect = Exception("Failed")

        result = cli_runner.invoke(app, ["flush", "state"])

        assert result.exit_code == 1
        assert "Failed" in result.output
