"""Main CLI entry point for Agentic CLI."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console

from agentic import __version__
from agentic.config import ConfigManager

console = Console()


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Agentic CLI - A secure, CLI-first AI development assistant."""
    ctx.ensure_object(dict)


@main.command()
@click.option(
    "--template",
    type=str,
    help="Project template to use (python, javascript, etc.)"
)
def init(template: Optional[str]) -> None:
    """Initialize a new agentic project."""
    # Create .agentic directory and config
    config_dir = Path.cwd() / ".agentic"
    config_manager = ConfigManager(config_dir)
    
    # Load default config (will create if doesn't exist)
    config = config_manager.load()
    
    if template:
        console.print(f"[green]Initialized agentic project with {template} template[/green]")
    else:
        console.print("[green]Initialized agentic project[/green]")


@main.command()
@click.argument("task", required=True)
@click.option(
    "--context",
    type=click.Path(exists=True),
    help="Path to context files or directory"
)
def generate(task: str, context: Optional[str]) -> None:
    """Generate code or documentation from task description."""
    # TODO: Implement code generation
    console.print(f"[yellow]Generating: {task}[/yellow]")
    if context:
        console.print(f"[dim]Using context: {context}[/dim]")
    
    # For now, just indicate we received the task
    console.print("[red]Code generation not yet implemented[/red]")


@main.command()
@click.option(
    "--file",
    type=click.Path(exists=True),
    help="Specific file to review"
)
def review(file: Optional[str]) -> None:
    """Review generated content for quality and security."""
    # TODO: Implement review functionality
    if file:
        console.print(f"[yellow]Reviewing file: {file}[/yellow]")
    else:
        console.print("[yellow]Reviewing all pending changes[/yellow]")
    
    console.print("[red]Review functionality not yet implemented[/red]")


@main.command()
def apply() -> None:
    """Apply approved changes to the project."""
    # TODO: Implement apply functionality
    console.print("[yellow]Applying approved changes[/yellow]")
    console.print("[red]Apply functionality not yet implemented[/red]")


@main.group()
def config() -> None:
    """Manage agentic configuration."""
    pass


@config.command("get")
@click.argument("key")
def config_get(key: str) -> None:
    """Get a configuration value."""
    try:
        config_dir = Path.cwd() / ".agentic"
        config_manager = ConfigManager(config_dir)
        
        # Load existing config or create default
        config_manager.load()
        
        value = config_manager.get_value(key)
        console.print(f"{key}: {value}")
    
    except Exception as e:
        console.print(f"[red]Error getting config value: {e}[/red]")
        raise click.ClickException(str(e))


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    try:
        config_dir = Path.cwd() / ".agentic"
        config_manager = ConfigManager(config_dir)
        
        # Load existing config or create default
        config_manager.load()
        
        # Convert string values to appropriate types
        if value.lower() in ("true", "false"):
            typed_value = value.lower() == "true"
        else:
            typed_value = value
        
        config_manager.set_value(key, typed_value)
        console.print(f"[green]Set {key} to {typed_value}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error setting config value: {e}[/red]")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    main()