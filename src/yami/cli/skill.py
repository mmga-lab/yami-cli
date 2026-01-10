"""Claude Code skill management commands."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer

from yami.output.formatter import print_error, print_info, print_success

app = typer.Typer(no_args_is_help=True)


def _get_skill_source_dir() -> Path | None:
    """Get the source directory containing skill files."""
    # Try relative to this file (installed package)
    package_dir = Path(__file__).parent.parent
    skill_dir = package_dir / "skills"
    if skill_dir.exists():
        return skill_dir

    # Try development layout (.claude/skills/yami)
    dev_dir = package_dir.parent.parent / ".claude" / "skills" / "yami"
    if dev_dir.exists():
        return dev_dir

    return None


def _get_claude_skill_dir() -> Path:
    """Get the Claude Code skill directory."""
    import os

    config_home = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    return Path(config_home) / "claude" / "skills" / "yami"


@app.command()
def install(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing skill files",
    ),
) -> None:
    """Install yami skill to Claude Code.

    This makes Claude Code aware of yami CLI commands and usage.
    """
    source_dir = _get_skill_source_dir()
    if source_dir is None:
        print_error("Could not find yami skill files")
        print_info("Skill files should be in .claude/skills/yami/")
        raise typer.Exit(1)

    target_dir = _get_claude_skill_dir()

    # Check if already exists
    if target_dir.exists() and not force:
        print_info(f"Skill already installed at: {target_dir}")
        print_info("Use --force to overwrite")
        return

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy skill files
    files_copied = 0
    for file in source_dir.iterdir():
        if file.is_file() and file.suffix == ".md":
            shutil.copy2(file, target_dir / file.name)
            files_copied += 1
            print_info(f"Copied: {file.name}")

    if files_copied == 0:
        print_error("No skill files found to copy")
        raise typer.Exit(1)

    print_success(f"Yami skill installed to: {target_dir}")
    print_info("Restart Claude Code to apply changes")


@app.command()
def uninstall(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
) -> None:
    """Uninstall yami skill from Claude Code."""
    target_dir = _get_claude_skill_dir()

    if not target_dir.exists():
        print_info("Yami skill is not installed")
        return

    if not force:
        confirm = typer.confirm(f"Remove yami skill from {target_dir}?")
        if not confirm:
            raise typer.Abort()

    shutil.rmtree(target_dir)
    print_success("Yami skill uninstalled")


@app.command()
def status() -> None:
    """Check if yami skill is installed in Claude Code."""
    target_dir = _get_claude_skill_dir()

    if target_dir.exists():
        skill_file = target_dir / "SKILL.md"
        if skill_file.exists():
            print_success(f"Yami skill is installed at: {target_dir}")
        else:
            print_info(f"Skill directory exists but SKILL.md is missing: {target_dir}")
    else:
        print_info("Yami skill is not installed")
        print_info("Run 'yami skill install' to install")


@app.command()
def show() -> None:
    """Show the skill content."""
    source_dir = _get_skill_source_dir()
    if source_dir is None:
        print_error("Could not find yami skill files")
        raise typer.Exit(1)

    skill_file = source_dir / "SKILL.md"
    if skill_file.exists():
        print(skill_file.read_text())
    else:
        print_error("SKILL.md not found")
        raise typer.Exit(1)
