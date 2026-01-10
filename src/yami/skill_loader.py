"""Skill loader for Claude Agent SDK integration."""

from __future__ import annotations

from pathlib import Path


def get_skill_prompt(include_reference: bool = True) -> str:
    """Get yami skill content for use as system prompt in Claude Agent SDK.

    Args:
        include_reference: Whether to include the full reference documentation.
                          Set to False for a shorter prompt.

    Returns:
        Skill content as a string, ready to use as system_prompt.

    Example:
        from claude_agent_sdk import query, ClaudeAgentOptions
        from yami import get_skill_prompt

        async for msg in query(
            prompt="List all Milvus collections",
            options=ClaudeAgentOptions(
                system_prompt=get_skill_prompt(),
                allowed_tools=["Bash"],
            )
        ):
            print(msg)
    """
    skill_dir = Path(__file__).parent / "skills"

    # Load main skill file
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return _get_minimal_prompt()

    content = skill_file.read_text()

    # Optionally include reference
    if include_reference:
        ref_file = skill_dir / "REFERENCE.md"
        if ref_file.exists():
            content += "\n\n" + ref_file.read_text()

    return content


def _get_minimal_prompt() -> str:
    """Fallback minimal prompt if skill files not found."""
    return """# Yami - Milvus CLI

Use `yami` CLI for Milvus vector database operations.
Always use `--mode agent` for JSON output.

## Quick Reference

```bash
# List collections
yami --mode agent collection list

# Create collection
yami --mode agent collection create <name> --dim <dim> [--metric COSINE|L2|IP]

# Describe collection
yami --mode agent collection describe <name>

# Insert data
yami --mode agent data insert <collection> --sql "SELECT * FROM 'file.parquet'"

# Search
yami --mode agent query search <collection> --random --limit 10

# Query
yami --mode agent query query <collection> --filter "id > 100"

# Drop collection
yami --mode agent collection drop <name> --force
```

## Output Format

All commands output JSON in agent mode:
- Success: `{"status": "success", "message": "..."}`
- Error: `{"error": {"code": "...", "message": "..."}}`
- Data: `[{"id": 1, ...}, ...]`
"""
