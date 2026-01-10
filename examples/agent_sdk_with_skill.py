#!/usr/bin/env python3
"""Using yami with Claude Agent SDK's native Skill support.

The SDK will automatically discover and load skills from:
- Project: .claude/skills/
- User: ~/.claude/skills/

Requirements:
    pip install claude-agent-sdk yami-cli
    yami skill install  # Install skill to ~/.claude/skills/

Usage:
    export ANTHROPIC_API_KEY=your-api-key
    python examples/agent_sdk_with_skill.py
"""

import anyio
from pathlib import Path
from claude_agent_sdk import query, ClaudeAgentOptions


async def main():
    # Get the yami-cli project directory (contains .claude/skills/yami)
    project_dir = Path(__file__).parent.parent

    async for message in query(
        prompt="List all Milvus collections",
        options=ClaudeAgentOptions(
            # Set working directory to project with .claude/skills/
            cwd=str(project_dir),
            # Load skills from filesystem
            setting_sources=["user", "project"],
            # Enable Skill tool along with Bash
            allowed_tools=["Skill", "Bash", "Read"],
        ),
    ):
        print(message)


async def use_user_skill():
    """Use skill installed in ~/.claude/skills/"""

    # First, make sure skill is installed:
    # yami skill install

    async for message in query(
        prompt="Use yami to list all Milvus collections and show server info",
        options=ClaudeAgentOptions(
            # Load user-level skills from ~/.claude/skills/
            setting_sources=["user"],
            allowed_tools=["Skill", "Bash"],
        ),
    ):
        print(message)


if __name__ == "__main__":
    print("Option 1: Using project-level skill (.claude/skills/)")
    print("=" * 50)
    anyio.run(main)

    print("\nOption 2: Using user-level skill (~/.claude/skills/)")
    print("=" * 50)
    anyio.run(use_user_skill)
