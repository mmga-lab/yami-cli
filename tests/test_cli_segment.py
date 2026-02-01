"""Tests for new segment commands."""

from __future__ import annotations

from yami.cli.main import app


class TestSegmentOptimize:
    """Test segment optimize command."""

    def test_optimize_default_size(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["segment", "optimize", "test_col"])

        assert result.exit_code == 0
        mock_client.optimize.assert_called_once_with(
            collection_name="test_col",
            target_segment_size=512 * 1024 * 1024,  # 512MB default
        )

    def test_optimize_custom_size(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(
            app, ["segment", "optimize", "test_col", "--target-size", "1073741824"]
        )

        assert result.exit_code == 0
        mock_client.optimize.assert_called_once_with(
            collection_name="test_col",
            target_segment_size=1073741824,  # 1GB
        )

    def test_optimize_short_flag(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["segment", "optimize", "test_col", "-s", "268435456"])

        assert result.exit_code == 0
        mock_client.optimize.assert_called_once_with(
            collection_name="test_col",
            target_segment_size=268435456,  # 256MB
        )

    def test_optimize_error(self, cli_runner, mock_context, mock_client):
        mock_client.optimize.side_effect = Exception("Collection not found")

        result = cli_runner.invoke(app, ["segment", "optimize", "missing_col"])

        assert result.exit_code == 1
        assert "Collection not found" in result.output
