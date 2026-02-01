"""Text analyzer commands."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from yami.core.context import get_context
from yami.output.formatter import format_output, print_error

app = typer.Typer(no_args_is_help=True)


@app.command()
def run(
    texts: Annotated[
        list[str] | None,
        typer.Argument(help="Text(s) to analyze"),
    ] = None,
    analyzer: str = typer.Option(
        "standard",
        "--analyzer",
        "-a",
        help="Analyzer type (e.g., standard, english, chinese)",
    ),
    params: str | None = typer.Option(
        None,
        "--params",
        "-p",
        help="Analyzer parameters as JSON",
    ),
) -> None:
    """Run text analyzer on input texts.

    \b
    The analyzer breaks down text into tokens for full-text search.

    \b
    Examples:
      yami analyzer run "hello world"
      yami analyzer run "hello world" "foo bar" --analyzer standard
      yami analyzer run "你好世界" --analyzer chinese
      yami analyzer run "hello" --params '{"case_sensitive": false}'
    """
    if not texts:
        print_error("At least one text argument is required")
        raise typer.Exit(1)

    ctx = get_context()
    client = ctx.get_client()

    try:
        analyzer_params = {"type": analyzer}
        if params:
            extra_params = json.loads(params)
            analyzer_params.update(extra_params)

        results = client.run_analyzer(
            texts=list(texts),
            analyzer_params=analyzer_params,
        )

        # Format output
        output_data = []
        for i, (text, tokens) in enumerate(zip(texts, results)):
            output_data.append({
                "text": text,
                "tokens": tokens,
                "token_count": len(tokens),
            })

        format_output(output_data, ctx.output, title="Analyzer Results")

    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON params: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
