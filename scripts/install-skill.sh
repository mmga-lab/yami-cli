#!/bin/bash
# Install yami skill to Claude Code

set -e

SKILL_DIR="$HOME/.claude/skills/yami"
SOURCE_DIR="$(dirname "$0")/../.claude/skills/yami"

# Check if source exists
if [ ! -d "$SOURCE_DIR" ]; then
    # Try to find it relative to the installed package
    PACKAGE_DIR=$(python3 -c "import yami; import os; print(os.path.dirname(yami.__file__))" 2>/dev/null)
    if [ -n "$PACKAGE_DIR" ]; then
        SOURCE_DIR="$PACKAGE_DIR/../.claude/skills/yami"
    fi
fi

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Could not find yami skill files"
    exit 1
fi

# Create target directory
mkdir -p "$SKILL_DIR"

# Copy skill files
cp "$SOURCE_DIR/SKILL.md" "$SKILL_DIR/"
cp "$SOURCE_DIR/REFERENCE.md" "$SKILL_DIR/"

echo "Yami skill installed to: $SKILL_DIR"
echo ""
echo "Claude Code will now recognize yami commands."
echo "Restart Claude Code to apply changes."
