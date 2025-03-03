#!/usr/bin/env python3
"""
Example implementation of a CLI using Click and Rich based on the cli_schema.json.
This demonstrates how to create a beautiful and user-friendly command-line interface.
"""
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

# Initialize Rich console
console = Console()

# Load CLI schema
try:
    with open('cli_schema.json', 'r') as f:
        schema = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    console.print(f"[bold red]Error loading schema:[/bold red] {e}")
    sys.exit(1)

# Configuration context to share between commands
class Config:
    def __init__(self):
        self.global_config = {}
        self.local_config = {}
        self.debug = False
        self.effective_config = {}
    
    def load_config_files(self):
        """Load configuration from different sources according to priority."""
        # 1. Load global config
        global_config_path = Path.home() / ".vectorizer" / "config.json"
        if global_config_path.exists():
            try:
                with open(global_config_path, 'r') as f:
                    self.global_config = json.load(f)
            except json.JSONDecodeError:
                console.print("[bold yellow]Warning: Invalid JSON in global config file[/bold yellow]")
        
        # 2. Load local config (overrides global)
        local_config_path = Path.cwd() / "config.json"
        if local_config_path.exists():
            try:
                with open(local_config_path, 'r') as f:
                    self.local_config = json.load(f)
            except json.JSONDecodeError:
                console.print("[bold yellow]Warning: Invalid JSON in local config file[/bold yellow]")
        
        # 3. Combine configs according to priority
        self.effective_config = self.global_config.copy()
        self.effective_config.update(self.local_config)

# Pass the Config object to all commands
pass_config = click.make_pass_decorator(Config, ensure=True)

def common_options(func):
    """Decorator to add common options defined in the schema."""
    for option in reversed(schema.get('commonOptions', [])):
        option_name = option['flag']
        
        kwargs = {
            'help': option['description'],
            'required': option.get('required', False),
        }
        
        # Handle different option types
        if option['type'] == 'boolean':
            kwargs['is_flag'] = True
        elif option['type'] == 'integer':
            kwargs['type'] = int
        elif option['type'] == 'float':
            kwargs['type'] = float
        elif option['type'] == 'array':
            kwargs['multiple'] = True
        
        # Add default value if specified
        if 'default' in option:
            kwargs['default'] = option['default']
        
        func = click.option(option_name, **kwargs)(func)
    
    return func

# Main CLI group
@click.group(help=schema['description'])
@click.version_option(schema['version'])
@click.option('--readme', is_flag=True, help='Display README and exit')
@click.pass_context
def cli(ctx, readme):
    """Main CLI entry point."""
    ctx.obj = Config()
    
    if readme:
        readme_path = Path.cwd() / "README.md"
        try:
            with open(readme_path, 'r') as f:
                # Use Rich to render the markdown with a title panel
                md_content = f.read()
                console.print(Panel.fit(
                    Markdown(md_content),
                    title="README",
                    border_style="blue"
                ))
            ctx.exit()
        except FileNotFoundError:
            console.print("[bold red]README.md not found![/bold red]")
            ctx.exit(1)

# Split command
@cli.command('split', help="Split markdown files into chunks")
@click.option('--output-folder', type=str, help="Path to folder where chunks should be saved")
@common_options
@pass_config
def split_command(config, output_folder, **kwargs):
    """Split markdown files into chunks."""
    # Load configuration
    config.load_config_files()
    
    # Update config with command-line args
    cmd_config = {k.replace('_', '-'): v for k, v in kwargs.items() if v is not None}
    config.effective_config.update(cmd_config)
    
    # Set debug mode
    debug = config.effective_config.get('debug', False)
    if debug:
        console.print("[bold blue]Running in debug mode - displaying extended information[/bold blue]")
        console.print(Panel(
            json.dumps(config.effective_config, indent=2),
            title="Effective Configuration",
            border_style="yellow"
        ))
    
    # Check required parameters
    required = ['catalogue', 'folder']
    missing = [param for param in required if param not in config.effective_config or not config.effective_config[param]]
    
    if missing:
        console.print(f"[bold red]Missing required parameters: {', '.join(missing)}[/bold red]")
        sys.exit(1)
    
    # Display operation summary
    console.print()
    console.print("[bold green]Splitting markdown files into chunks[/bold green]")
    console.print()
    
    # Create a table to display the parameters
    table = Table(title="Split Command Parameters")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    
    for param, value in config.effective_config.items():
        if param not in ['debug'] and value is not None:
            table.add_row(param, str(value))
    
    console.print(table)
    console.print()
    
    # Simulate processing with a progress bar
    console.print("[bold]Processing files...[/bold]")
    
    # Count files to process
    file_count = config.effective_config.get('count', 5)  # Default to 5 for demo
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn()
    ) as progress:
        # Main task for overall progress
        overall_task = progress.add_task("[cyan]Overall progress", total=file_count)
        current_file_task = progress.add_task("[green]Current file", total=100, visible=False)
        
        for i in range(file_count):
            # Update task description for current file
            file_name = f"file_{i+1}.md"
            progress.update(current_file_task, description=f"[green]Processing {file_name}", visible=True, completed=0)
            
            # Simulate file processing steps
            for j in range(100):
                time.sleep(0.01)  # Simulate work
                progress.update(current_file_task, completed=j+1)
            
            # Mark current file as complete
            progress.update(current_file_task, visible=False)
            
            # Update overall progress
            progress.update(overall_task, advance=1)
    
    console.print()
    console.print("[bold green]✓[/bold green] Successfully split all files into chunks!")
    console.print(f"  Output folder: [cyan]{output_folder or 'output_chunks'}[/cyan]")

# Vectorize command
@cli.command('vectorize', help="Split and vectorize markdown files")
@click.option('--output-folder', type=str, required=True, help="Path to folder where vectors should be saved")
@click.option('--model', type=str, default='nomic-embed-text', help="Model to use for vectorization")
@click.option('--base-url', type=str, default='http://localhost:11434', help="Base URL for the Ollama API")
@common_options
@pass_config
def vectorize_command(config, output_folder, model, base_url, **kwargs):
    """Split and vectorize markdown files."""
    # Load configuration
    config.load_config_files()
    
    # Update config with command-line args
    cmd_config = {k.replace('_', '-'): v for k, v in kwargs.items() if v is not None}
    cmd_config.update({
        'output-folder': output_folder,
        'model': model,
        'base-url': base_url
    })
    config.effective_config.update(cmd_config)
    
    # Display operation summary
    console.print()
    console.print("[bold green]Vectorizing markdown files[/bold green]")
    console.print()
    
    # Create a table to display the parameters
    table = Table(title="Vectorize Command Parameters")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    
    for param, value in config.effective_config.items():
        if param not in ['debug'] and value is not None:
            table.add_row(param, str(value))
    
    console.print(table)
    console.print()
    
    # Simulate processing with a progress bar
    console.print("[bold]Processing files...[/bold]")
    
    # Count files to process
    file_count = config.effective_config.get('count', 3)  # Default to 3 for demo
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn()
    ) as progress:
        # Create tasks
        overall_task = progress.add_task("[cyan]Overall progress", total=file_count)
        split_task = progress.add_task("[green]Splitting", total=100, visible=False)
        embed_task = progress.add_task("[yellow]Embedding", total=100, visible=False)
        
        for i in range(file_count):
            file_name = f"file_{i+1}.md"
            
            # Splitting phase
            progress.update(split_task, description=f"[green]Splitting {file_name}", visible=True, completed=0)
            for j in range(100):
                time.sleep(0.01)
                progress.update(split_task, completed=j+1)
            progress.update(split_task, visible=False)
            
            # Embedding phase
            progress.update(embed_task, description=f"[yellow]Embedding {file_name}", visible=True, completed=0)
            for j in range(100):
                time.sleep(0.02)  # Embedding is slower
                progress.update(embed_task, completed=j+1)
            progress.update(embed_task, visible=False)
            
            # Update overall progress
            progress.update(overall_task, advance=1)
    
    console.print()
    console.print("[bold green]✓[/bold green] Successfully vectorized all files!")
    console.print(f"  Output folder: [cyan]{output_folder}[/cyan]")
    console.print(f"  Model used: [cyan]{model}[/cyan]")

# Organize command
@cli.command('organize', help="Create a hierarchical JSON representation of markdown structure")
@click.option('--output-folder', type=str, required=True, 
              help="Path to folder where JSON structure files should be saved")
@click.option('--ommit-properties', type=str,
              help="Comma-separated list of properties to omit from the JSON output (e.g., 'items,size')")
@common_options
@pass_config
def organize_command(config, output_folder, ommit_properties, **kwargs):
    """Create a hierarchical JSON representation of markdown structure."""
    # Load configuration
    config.load_config_files()
    
    # Update config with command-line args
    cmd_config = {k.replace('_', '-'): v for k, v in kwargs.items() if v is not None}
    cmd_config.update({
        'output-folder': output_folder,
    })
    if ommit_properties:
        cmd_config['ommit-properties'] = ommit_properties
    
    config.effective_config.update(cmd_config)
    
    # Display operation summary
    console.print()
    console.print("[bold green]Organizing markdown files[/bold green]")
    console.print()
    
    # Show which properties will be omitted if specified
    if ommit_properties:
        omitted = [prop.strip() for prop in ommit_properties.split(',')]
        console.print(f"[yellow]Omitting properties from JSON output: {', '.join(omitted)}[/yellow]")
        console.print()
    
    # Create a table to display the parameters
    table = Table(title="Organize Command Parameters")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")
    
    for param, value in config.effective_config.items():
        if param not in ['debug'] and value is not None:
            table.add_row(param, str(value))
    
    console.print(table)
    console.print()
    
    # Simulate processing with a progress bar
    console.print("[bold]Processing files...[/bold]")
    
    # Count files to process
    file_count = config.effective_config.get('count', 4)  # Default to 4 for demo
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn()
    ) as progress:
        task = progress.add_task("[cyan]Organizing documents", total=file_count)
        
        for i in range(file_count):
            file_name = f"file_{i+1}.md"
            progress.update(task, description=f"[cyan]Organizing {file_name}")
            time.sleep(0.5)  # Simulate work
            progress.update(task, advance=1)
    
    # Show a sample of the JSON output structure
    console.print()
    console.print("[bold green]✓[/bold green] Successfully organized all files!")
    console.print(f"  Output folder: [cyan]{output_folder}[/cyan]")
    
    # Display a sample JSON structure
    sample_json = {
        "type": "document",
        "title": "Sample Document",
        "content_size": 1024,
        "elements": [
            {
                "type": "header",
                "level": 1,
                "content": "Introduction"
            },
            {
                "type": "paragraph",
                "content": "This is a sample paragraph."
            }
        ]
    }
    
    # Remove omitted properties if specified
    if ommit_properties:
        omitted = [prop.strip() for prop in ommit_properties.split(',')]
        for prop in omitted:
            if prop in sample_json:
                del sample_json[prop]
    
    # Show sample output
    console.print()
    console.print("[bold]Sample JSON output structure:[/bold]")
    syntax = Syntax(
        json.dumps(sample_json, indent=2),
        "json",
        theme="monokai",
        line_numbers=True,
        word_wrap=True
    )
    console.print(Panel(syntax, title="JSON Structure", border_style="green"))

# Config command
@cli.command('config', help="Display or manage configuration")
@click.option('--source', type=click.Choice(['all', 'global', 'local', 'effective']), 
              default='effective', help="Which configuration source to display")
@click.option('--create-local', is_flag=True, help="Create a local config file with current settings")
@click.option('--create-global', is_flag=True, help="Create a global config file with current settings")
@pass_config
def config_command(config, source, create_local, create_global):
    """Display or manage configuration settings."""
    # Load configuration
    config.load_config_files()
    
    if create_local:
        local_config_path = Path.cwd() / "config.json"
        with open(local_config_path, 'w') as f:
            json.dump(config.effective_config, f, indent=2)
        console.print(f"[bold green]✓[/bold green] Created local config file at [cyan]{local_config_path}[/cyan]")
    
    if create_global:
        global_config_dir = Path.home() / ".vectorizer"
        global_config_dir.mkdir(parents=True, exist_ok=True)
        global_config_path = global_config_dir / "config.json"
        with open(global_config_path, 'w') as f:
            json.dump(config.effective_config, f, indent=2)
        console.print(f"[bold green]✓[/bold green] Created global config file at [cyan]{global_config_path}[/cyan]")
    
    if not create_local and not create_global:
        # Display configuration
        if source in ['all', 'global'] and config.global_config:
            console.print(Panel.fit(
                Syntax(json.dumps(config.global_config, indent=2), "json", theme="monokai"),
                title="Global Configuration (~/.vectorizer/config.json)",
                border_style="blue"
            ))
        
        if source in ['all', 'local'] and config.local_config:
            console.print(Panel.fit(
                Syntax(json.dumps(config.local_config, indent=2), "json", theme="monokai"),
                title="Local Configuration (./config.json)",
                border_style="green"
            ))
        
        if source in ['all', 'effective']:
            console.print(Panel.fit(
                Syntax(json.dumps(config.effective_config, indent=2), "json", theme="monokai"),
                title="Effective Configuration",
                border_style="yellow"
            ))

# Schema command
@cli.command('schema', help="Visualize CLI schema structure")
def schema_command():
    """Visualize the CLI schema structure."""
    tree = Tree(f"[bold magenta]{schema['name']} CLI[/bold magenta]")
    
    # Add global options
    global_branch = tree.add("[bold blue]Global Options[/bold blue]")
    for option in schema.get('globalOptions', []):
        global_branch.add(f"[cyan]{option['flag']}[/cyan]: {option['description']}")
    
    # Add commands
    commands_branch = tree.add("[bold green]Commands[/bold green]")
    for command in schema.get('commands', []):
        cmd_branch = commands_branch.add(f"[yellow]{command['name']}[/yellow]: {command['description']}")
        
        # Add command options
        for option in command.get('options', []):
            required = "[bold red]*[/bold red] " if option.get('required', False) else ""
            cmd_branch.add(f"{required}[cyan]{option['flag']}[/cyan]: {option['description']}")
    
    # Add common options
    common_branch = tree.add("[bold blue]Common Options[/bold blue]")
    for option in schema.get('commonOptions', []):
        required = "[bold red]*[/bold red] " if option.get('required', False) else ""
        common_branch.add(f"{required}[cyan]{option['flag']}[/cyan]: {option['description']}")
    
    # Add configuration sources
    config_branch = tree.add("[bold yellow]Configuration Sources[/bold yellow]")
    for source in schema.get('configurationSources', []):
        priority = source.get('priority', 0)
        config_branch.add(f"[cyan]{priority}.[/cyan] {source['name']}: {source['description']}")
    
    console.print(tree)

if __name__ == "__main__":
    try:
        cli()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if "--debug" in sys.argv:
            console.print_exception()
        sys.exit(1)