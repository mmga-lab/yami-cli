#!/usr/bin/env python3
"""Demo: Using yami with Claude Agent SDK.

This example shows how to use yami CLI with Claude Agent SDK.
The agent will use Bash tool to execute yami commands.

Requirements:
    pip install claude-agent-sdk yami-cli

Usage:
    # Set your API key
    export ANTHROPIC_API_KEY=your-api-key

    # Run the demo
    python examples/agent_sdk_demo.py
"""

import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# Import yami's skill prompt
from yami import get_skill_prompt


async def demo_list_collections():
    """Demo: List all Milvus collections."""
    print("=" * 60)
    print("Demo 1: List Collections")
    print("=" * 60)

    async for message in query(
        prompt="List all Milvus collections",
        options=ClaudeAgentOptions(
            system_prompt=get_skill_prompt(),
            allowed_tools=["Bash"],
            max_turns=3,
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


async def demo_create_and_describe():
    """Demo: Create a collection and describe it."""
    print("\n" + "=" * 60)
    print("Demo 2: Create and Describe Collection")
    print("=" * 60)

    async for message in query(
        prompt="""
        1. Create a collection named 'demo_products' with 768 dimensions and COSINE metric
        2. Describe the collection to verify it was created
        """,
        options=ClaudeAgentOptions(
            system_prompt=get_skill_prompt(),
            allowed_tools=["Bash"],
            max_turns=5,
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


async def demo_search():
    """Demo: Search with random vectors."""
    print("\n" + "=" * 60)
    print("Demo 3: Vector Search")
    print("=" * 60)

    async for message in query(
        prompt="Search the 'demo_products' collection with random vectors, limit 5 results",
        options=ClaudeAgentOptions(
            system_prompt=get_skill_prompt(),
            allowed_tools=["Bash"],
            max_turns=3,
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


async def demo_cleanup():
    """Demo: Drop the test collection."""
    print("\n" + "=" * 60)
    print("Demo 4: Cleanup")
    print("=" * 60)

    async for message in query(
        prompt="Drop the 'demo_products' collection (use --force to skip confirmation)",
        options=ClaudeAgentOptions(
            system_prompt=get_skill_prompt(),
            allowed_tools=["Bash"],
            max_turns=3,
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


async def demo_interactive():
    """Demo: Interactive conversation about Milvus."""
    print("\n" + "=" * 60)
    print("Demo 5: Interactive Query")
    print("=" * 60)

    async for message in query(
        prompt="""
        I want to:
        1. Check what collections exist
        2. If there are any collections, show me the stats of the first one
        3. Summarize what you found
        """,
        options=ClaudeAgentOptions(
            system_prompt=get_skill_prompt(),
            allowed_tools=["Bash"],
            max_turns=10,
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


async def main():
    """Run all demos."""
    print("Yami + Claude Agent SDK Demo")
    print("Make sure Milvus is running at localhost:19530")
    print()

    # Run demos
    await demo_list_collections()
    await demo_create_and_describe()
    await demo_search()
    await demo_cleanup()
    await demo_interactive()

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    anyio.run(main)
