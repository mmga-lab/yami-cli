"""Tests for analyzer commands."""

from __future__ import annotations

from yami.cli.main import app


class TestAnalyzerRun:
    """Test analyzer run command."""

    def test_run_analyzer_single_text(self, cli_runner, mock_context, mock_client):
        mock_client.run_analyzer.return_value = [["hello", "world"]]

        result = cli_runner.invoke(app, ["analyzer", "run", "hello world"])

        assert result.exit_code == 0
        mock_client.run_analyzer.assert_called_once_with(
            texts=["hello world"],
            analyzer_params={"type": "standard"},
        )

    def test_run_analyzer_multiple_texts(self, cli_runner, mock_context, mock_client):
        mock_client.run_analyzer.return_value = [["hello"], ["world"]]

        result = cli_runner.invoke(app, ["analyzer", "run", "hello", "world"])

        assert result.exit_code == 0
        mock_client.run_analyzer.assert_called_once_with(
            texts=["hello", "world"],
            analyzer_params={"type": "standard"},
        )

    def test_run_analyzer_with_analyzer_type(self, cli_runner, mock_context, mock_client):
        mock_client.run_analyzer.return_value = [["hello"]]

        result = cli_runner.invoke(app, ["analyzer", "run", "hello", "--analyzer", "english"])

        assert result.exit_code == 0
        mock_client.run_analyzer.assert_called_once_with(
            texts=["hello"],
            analyzer_params={"type": "english"},
        )

    def test_run_analyzer_with_params(self, cli_runner, mock_context, mock_client):
        mock_client.run_analyzer.return_value = [["hello"]]

        result = cli_runner.invoke(
            app,
            ["analyzer", "run", "hello", "--params", '{"case_sensitive": false}'],
        )

        assert result.exit_code == 0
        mock_client.run_analyzer.assert_called_once_with(
            texts=["hello"],
            analyzer_params={"type": "standard", "case_sensitive": False},
        )

    def test_run_analyzer_no_text_error(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["analyzer", "run"])

        assert result.exit_code == 1
        assert "text" in result.output.lower()

    def test_run_analyzer_invalid_params_json(self, cli_runner, mock_context, mock_client):
        result = cli_runner.invoke(app, ["analyzer", "run", "hello", "--params", "not json"])

        assert result.exit_code == 1
        assert "json" in result.output.lower()

    def test_run_analyzer_error(self, cli_runner, mock_context, mock_client):
        mock_client.run_analyzer.side_effect = Exception("Analyzer failed")

        result = cli_runner.invoke(app, ["analyzer", "run", "hello"])

        assert result.exit_code == 1
        assert "Analyzer failed" in result.output
