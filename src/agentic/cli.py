"""Main CLI entry point for Agentic CLI."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from agentic import __version__
from agentic.config import ConfigManager
from .generator import GeneratorAgent
from .llm import create_llm_provider
from .sandbox import Sandbox
from .tasks import TaskRegistry

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
@click.option(
    "--enhance",
    is_flag=True,
    help="Enhance generated code with LLM"
)
def generate(task: str, context: Optional[str], enhance: bool) -> None:
    """Generate code or documentation from task description."""
    asyncio.run(_generate_async(task, context, enhance))


async def _generate_async(task: str, context: Optional[str], enhance: bool) -> None:
    """Async implementation of generate command."""
    try:
        console.print(f"[yellow]Generating: {task}[/yellow]")
        if context:
            console.print(f"[dim]Using context: {context}[/dim]")
        if enhance:
            console.print("[dim]LLM enhancement enabled[/dim]")
        
        # Get project directory and config
        project_dir = Path.cwd()
        config_manager = ConfigManager(project_dir)
        config = config_manager.load_config()
        
        # Initialize components
        task_registry = TaskRegistry()
        llm_provider = create_llm_provider(
            provider_type=config.llm_provider or "mock",
            api_key=getattr(config, "openai_api_key", None) if config.llm_provider == "openai" else None
        )
        generator = GeneratorAgent(llm_provider, project_dir)
        sandbox = Sandbox(project_dir)
        
        # Parse task name and inputs from command
        task_name, inputs = _parse_task_command(task)
        
        # Load task template
        try:
            task_template = task_registry.get_task(task_name)
        except FileNotFoundError:
            console.print(f"[red]Task '{task_name}' not found[/red]")
            console.print("Available tasks:")
            for available_task in task_registry.list_tasks():
                console.print(f"  - {available_task}")
            return
        
        # Generate code
        console.print("[cyan]Generating code...[/cyan]")
        result = await generator.generate_from_template(
            task_template, inputs, enhance_with_llm=enhance
        )
        
        # Write to sandbox
        for file_path, content in result.files.items():
            sandbox.write_file(file_path, content)
        
        # Show results
        console.print("[green]✓ Generation complete![/green]")
        console.print(f"Generated {len(result.files)} file(s):")
        for file_path in result.files.keys():
            console.print(f"  - {file_path}")
        
        # Show sandbox status
        stats = sandbox.get_preview_stats()
        console.print(f"\n[dim]Preview: {stats['pending_files']} files, {stats['conflicts']} conflicts[/dim]")
        console.print("[dim]Use 'agentic review' to review changes, 'agentic apply' to apply[/dim]")
        
    except Exception as e:
        console.print(f"[red]Generation failed: {str(e)}[/red]")
        sys.exit(1)


def _parse_task_command(task: str) -> tuple[str, dict]:
    """Parse task command into name and inputs.
    
    Examples:
        'python_function name=hello return_value=world' -> ('python_function', {'name': 'hello', 'return_value': 'world'})
        'readme' -> ('readme', {})
    """
    parts = task.split()
    task_name = parts[0]
    
    inputs = {}
    for part in parts[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            inputs[key] = value
    
    return task_name, inputs


@main.command()
@click.option(
    "--file",
    help="Specific file to review"
)
def review(file: Optional[str]) -> None:
    """Review generated content for quality and security."""
    try:
        project_dir = Path.cwd()
        sandbox = Sandbox(project_dir)
        
        if file:
            console.print(f"[yellow]Reviewing file: {file}[/yellow]")
            content = sandbox.get_file_content(file)
            if content:
                console.print(f"\n[cyan]Content of {file}:[/cyan]")
                console.print(content)
            else:
                console.print(f"[red]File '{file}' not found in preview[/red]")
        else:
            console.print("[yellow]Reviewing all pending changes[/yellow]")
            
            pending_files = sandbox.list_pending_files()
            if not pending_files:
                console.print("[dim]No pending changes to review[/dim]")
                return
            
            # Show summary table
            table = Table(title="Pending Changes")
            table.add_column("File", style="cyan")
            table.add_column("Size", justify="right")
            table.add_column("Status", style="yellow")
            
            conflicts = sandbox.detect_conflicts()
            conflict_paths = {c.path for c in conflicts}
            
            for pending_file in pending_files:
                size = len(pending_file.content)
                status = "CONFLICT" if pending_file.relative_path in conflict_paths else "NEW"
                table.add_row(pending_file.relative_path, f"{size:,} bytes", status)
            
            console.print(table)
            
            # Show conflicts if any
            if conflicts:
                console.print("\n[red]Conflicts detected:[/red]")
                for conflict in conflicts:
                    console.print(f"\n[yellow]File: {conflict.path}[/yellow]")
                    console.print(conflict.generate_diff())
    
    except Exception as e:
        console.print(f"[red]Review failed: {str(e)}[/red]")
        sys.exit(1)


@main.command()
@click.option(
    "--force",
    is_flag=True,
    help="Force apply even with conflicts"
)
def apply(force: bool) -> None:
    """Apply approved changes to the project."""
    try:
        project_dir = Path.cwd()
        sandbox = Sandbox(project_dir)
        
        pending_files = sandbox.list_pending_files()
        if not pending_files:
            console.print("[dim]No pending changes to apply[/dim]")
            return
        
        console.print(f"[yellow]Applying {len(pending_files)} pending changes...[/yellow]")
        
        # Check for conflicts unless force is specified
        if not force:
            conflicts = sandbox.detect_conflicts()
            if conflicts:
                console.print(f"[red]Found {len(conflicts)} conflicts:[/red]")
                for conflict in conflicts:
                    console.print(f"  - {conflict.path}")
                console.print("[red]Use --force to override conflicts[/red]")
                sys.exit(1)
        
        # Apply changes
        applied_files = sandbox.apply_changes(force=force)
        
        console.print("[green]✓ Changes applied successfully![/green]")
        console.print("Applied files:")
        for file_path in applied_files:
            console.print(f"  - {file_path}")
    
    except Exception as e:
        console.print(f"[red]Apply failed: {str(e)}[/red]")
        sys.exit(1)


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