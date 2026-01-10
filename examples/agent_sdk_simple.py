#!/usr/bin/env python3
"""Minimal example: Using yami with Claude Agent SDK.

Requirements:
    pip install claude-agent-sdk yami-cli

Usage:
    export ANTHROPIC_API_KEY=your-api-key
    python examples/agent_sdk_simple.py
"""

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions
from yami import get_skill_prompt


async def main():
    # Use yami skill as system prompt
    # Agent will use Bash to run yami commands
    async for message in query(
        prompt="List all Milvus collections and show server version",
        options=ClaudeAgentOptions(
            system_prompt=get_skill_prompt(),
            allowed_tools=["Bash"],
        ),
    ):
        print(message)


if __name__ == "__main__":
    anyio.run(main)
