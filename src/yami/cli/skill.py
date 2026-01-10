"""Claude Code skill management commands."""

from __future__ import annotations

import shutil
from pathlib import Path
from enum import Enum

import typer

from yami.output.formatter import print_error, print_info, print_success

app = typer.Typer(no_args_is_help=True)


class SkillScope(str, Enum):
    """Skill installation scope."""
    user = "user"
    project = "project"


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


def _get_skill_target_dir(scope: SkillScope, project_dir: Path | None = None) -> Path:
    """Get the target directory for skill installation.

    Args:
        scope: user or project
        project_dir: Project directory for project scope (defaults to cwd)

    Returns:
        Path to skill directory
    """
    if scope == SkillScope.user:
        return Path.home() / ".claude" / "skills" / "yami"
    else:
        base = project_dir or Path.cwd()
        return base / ".claude" / "skills" / "yami"


def _install_skill_to(source_dir: Path, target_dir: Path, force: bool) -> bool:
    """Install skill files to target directory.

    Returns:
        True if installed, False if skipped
    """
    # Check if already exists
    if target_dir.exists() and not force:
        print_info(f"Skill already exists at: {target_dir}")
        print_info("Use --force to overwrite")
        return False

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy skill files
    files_copied = 0
    for file in source_dir.iterdir():
        if file.is_file() and file.suffix == ".md":
            shutil.copy2(file, target_dir / file.name)
            files_copied += 1
            print_info(f"  Copied: {file.name}")

    if files_copied == 0:
        print_error("No skill files found to copy")
        return False

    return True


@app.command()
def install(
    scope: SkillScope = typer.Option(
        SkillScope.user,
        "--scope",
        "-s",
        help="Installation scope: user (~/.claude/skills/) or project (.claude/skills/)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing skill files",
    ),
    project_dir: Path = typer.Option(
        None,
        "--project",
        "-p",
        help="Project directory for project scope (defaults to current directory)",
    ),
) -> None:
    """Install yami skill for Claude Code / Agent SDK.

    \b
    Scopes:
      user    - Install to ~/.claude/skills/ (personal, all projects)
      project - Install to .claude/skills/ (shared via git)

    \b
    Examples:
      yami skill install                    # Install to user scope
      yami skill install --scope project    # Install to current project
      yami skill install -s project -p /path/to/project
    """
    source_dir = _get_skill_source_dir()
    if source_dir is None:
        print_error("Could not find yami skill files")
        raise typer.Exit(1)

    target_dir = _get_skill_target_dir(scope, project_dir)

    print_info(f"Installing to {scope.value} scope...")
    if _install_skill_to(source_dir, target_dir, force):
        print_success(f"Yami skill installed to: {target_dir}")
        if scope == SkillScope.project:
            print_info("Add .claude/skills/ to git to share with your team")
        else:
            print_info("Restart Claude Code to apply changes")


@app.command()
def uninstall(
    scope: SkillScope = typer.Option(
        SkillScope.user,
        "--scope",
        "-s",
        help="Uninstall scope: user or project",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
    project_dir: Path = typer.Option(
        None,
        "--project",
        "-p",
        help="Project directory for project scope",
    ),
) -> None:
    """Uninstall yami skill."""
    target_dir = _get_skill_target_dir(scope, project_dir)

    if not target_dir.exists():
        print_info(f"Yami skill is not installed in {scope.value} scope")
        return

    if not force:
        confirm = typer.confirm(f"Remove yami skill from {target_dir}?")
        if not confirm:
            raise typer.Abort()

    shutil.rmtree(target_dir)
    print_success(f"Yami skill uninstalled from {scope.value} scope")


@app.command()
def status(
    project_dir: Path = typer.Option(
        None,
        "--project",
        "-p",
        help="Project directory to check",
    ),
) -> None:
    """Check yami skill installation status."""
    # Check user scope
    user_dir = _get_skill_target_dir(SkillScope.user)
    user_installed = user_dir.exists() and (user_dir / "SKILL.md").exists()

    # Check project scope
    proj_dir = _get_skill_target_dir(SkillScope.project, project_dir)
    proj_installed = proj_dir.exists() and (proj_dir / "SKILL.md").exists()

    print_info("Yami Skill Status:")
    print_info("")

    if user_installed:
        print_success(f"  user:     {user_dir}")
    else:
        print_info("  user:     Not installed")

    if proj_installed:
        print_success(f"  project:  {proj_dir}")
    else:
        print_info("  project:  Not installed")

    if not user_installed and not proj_installed:
        print_info("")
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
