"""Shell completion management commands."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console

from yami.output.formatter import print_error, print_info, print_success

app = typer.Typer(no_args_is_help=True)
console = Console()

# Shell config files
SHELL_CONFIGS = {
    "bash": [".bashrc", ".bash_profile"],
    "zsh": [".zshrc"],
    "fish": [".config/fish/config.fish"],
}


def _detect_shell() -> str:
    """Detect the current shell."""
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return "zsh"
    elif "fish" in shell:
        return "fish"
    elif "bash" in shell:
        return "bash"
    else:
        # Try to detect from parent process
        try:
            import shutil

            if shutil.which("zsh"):
                return "zsh"
        except Exception:
            pass
        return "bash"


def _get_completion_script(shell: str) -> str:
    """Get the completion script for a shell."""
    # Use typer's built-in completion generation
    env = os.environ.copy()
    env["_YAMI_COMPLETE"] = f"{shell}_source"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "yami"],
            capture_output=True,
            text=True,
            env=env,
        )
        return result.stdout
    except Exception:
        return ""


def _get_completion_dir(shell: str) -> Path | None:
    """Get the completion directory for a shell."""
    home = Path.home()

    if shell == "bash":
        # Check common locations
        for path in [
            Path("/etc/bash_completion.d"),
            home / ".local/share/bash-completion/completions",
            Path("/usr/local/etc/bash_completion.d"),
        ]:
            if path.exists() or path.parent.exists():
                return path
        return home / ".local/share/bash-completion/completions"

    elif shell == "zsh":
        # Check fpath locations
        for path in [
            home / ".zfunc",
            home / ".zsh/completions",
            Path("/usr/local/share/zsh/site-functions"),
        ]:
            if path.exists():
                return path
        return home / ".zfunc"

    elif shell == "fish":
        return home / ".config/fish/completions"

    return None


@app.command()
def install(
    shell: str = typer.Option(
        "",
        "--shell",
        "-s",
        help="Shell type: bash, zsh, fish (auto-detected if not specified)",
    ),
) -> None:
    """Install shell completion for yami.

    This will add completion support to your shell configuration.
    """
    if not shell:
        shell = _detect_shell()
        print_info(f"Detected shell: {shell}")

    shell = shell.lower()
    if shell not in ["bash", "zsh", "fish"]:
        print_error(f"Unsupported shell: {shell}. Supported: bash, zsh, fish")
        raise typer.Exit(1)

    # Get completion directory
    comp_dir = _get_completion_dir(shell)
    if comp_dir is None:
        print_error(f"Could not find completion directory for {shell}")
        raise typer.Exit(1)

    # Create directory if needed
    comp_dir.mkdir(parents=True, exist_ok=True)

    # Determine completion file path
    if shell == "zsh":
        comp_file = comp_dir / "_yami"
    elif shell == "fish":
        comp_file = comp_dir / "yami.fish"
    else:
        comp_file = comp_dir / "yami"

    # Generate and write completion script
    script = _get_completion_script(shell)
    if not script:
        # Fallback: use typer's method
        print_info("Generating completion script...")
        try:
            # For typer, we need to use the internal completion mechanism
            from typer.completion import get_completion_script
            script = get_completion_script(prog_name="yami", complete_var="_YAMI_COMPLETE", shell=shell)
        except ImportError:
            pass

    if not script:
        # Final fallback: instruct user to use typer's built-in
        print_info(f"Run this command to install completion:")
        print_info(f"  yami --install-completion {shell}")
        return

    comp_file.write_text(script)
    print_success(f"Completion script installed to: {comp_file}")

    # Shell-specific post-install instructions
    if shell == "zsh":
        zshrc = Path.home() / ".zshrc"
        add_line = f'fpath=({comp_dir} $fpath)'

        # Check if already added
        if zshrc.exists():
            content = zshrc.read_text()
            if str(comp_dir) not in content:
                print_info(f"Add this line to your ~/.zshrc:")
                console.print(f"  [cyan]{add_line}[/cyan]")
                print_info("Then run: autoload -Uz compinit && compinit")
            else:
                print_info("Run: autoload -Uz compinit && compinit")
        else:
            print_info(f"Add this line to your ~/.zshrc:")
            console.print(f"  [cyan]{add_line}[/cyan]")

    elif shell == "bash":
        print_info("Restart your shell or run:")
        console.print(f"  [cyan]source {comp_file}[/cyan]")

    elif shell == "fish":
        print_info("Restart your shell to enable completion")


@app.command()
def show(
    shell: str = typer.Option(
        "",
        "--shell",
        "-s",
        help="Shell type: bash, zsh, fish (auto-detected if not specified)",
    ),
) -> None:
    """Show the completion script without installing.

    Useful for manual installation or piping to a file.
    """
    if not shell:
        shell = _detect_shell()

    shell = shell.lower()
    if shell not in ["bash", "zsh", "fish"]:
        print_error(f"Unsupported shell: {shell}. Supported: bash, zsh, fish")
        raise typer.Exit(1)

    try:
        from typer.completion import get_completion_script
        script = get_completion_script(prog_name="yami", complete_var="_YAMI_COMPLETE", shell=shell)
        console.print(script)
    except ImportError:
        print_error("Could not generate completion script")
        print_info("Try: yami --show-completion")
        raise typer.Exit(1)


@app.command()
def uninstall(
    shell: str = typer.Option(
        "",
        "--shell",
        "-s",
        help="Shell type: bash, zsh, fish (auto-detected if not specified)",
    ),
) -> None:
    """Uninstall shell completion for yami."""
    if not shell:
        shell = _detect_shell()

    shell = shell.lower()
    comp_dir = _get_completion_dir(shell)

    if comp_dir is None:
        print_error(f"Could not find completion directory for {shell}")
        raise typer.Exit(1)

    # Determine completion file path
    if shell == "zsh":
        comp_file = comp_dir / "_yami"
    elif shell == "fish":
        comp_file = comp_dir / "yami.fish"
    else:
        comp_file = comp_dir / "yami"

    if comp_file.exists():
        comp_file.unlink()
        print_success(f"Removed completion script: {comp_file}")
    else:
        print_info(f"Completion script not found: {comp_file}")
