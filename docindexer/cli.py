#!/usr/bin/env python3
"""Command line interface for DocIndexer with schema validation and configuration management."""

import sys
import json
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.tree import Tree
from pathlib import Path
import os
from typing import Any, Dict, List, Optional

from .indexer import DocIndexer
from .validator import SchemaValidator, ValidationError
from .config import Configuration

# Initialize console for rich output
console = Console()

# Create configuration and validator instances
config = Configuration()
validator = SchemaValidator(Path(__file__).parent / "cli_schema.json")

def validate_and_apply_config(command: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Validate arguments against schema and apply configuration.
    
    Args:
        command: The command being executed
        args: The command arguments
        
    Returns:
        Dict containing validated and merged configuration
        
    Raises:
        click.UsageError: If validation fails
    """
    # Normalize argument names
    normalized_args = validator.normalize_args(args)
    
    # Load configuration from files
    config.load_config()
    
    # Apply defaults from schema
    args_with_defaults = validator.apply_defaults(normalized_args, command)
    
    # Validate the command arguments
    is_valid, errors = validator.validate_command(command, args_with_defaults)
    if not is_valid:
        error_msg = "\n".join(errors)
        raise click.UsageError(f"Validation failed:\n{error_msg}")
    
    # Update configuration with command-line arguments
    config.set_cli_args(args_with_defaults)
    
    return config.as_dict()

@click.group()
@click.version_option()
@click.option('--readme', is_flag=True, help='Display README and exit')
def main(readme):
    """DocIndexer - A command line tool for indexing documents."""
    if readme:
        try:
            readme_path = Path.cwd() / "README.md"
            with open(readme_path, 'r') as f:
                console.print(Panel(Markdown(f.read()), title="README", border_style="blue"))
            sys.exit(0)
        except FileNotFoundError:
            console.print("[bold red]README.md not found![/]")
            sys.exit(1)

@main.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--recursive', '-r', '-R', is_flag=True, help='Index documents recursively.')
@click.option('--output', '-o', type=click.Path(), help='Output file path.')
@click.option('--create-local-config', is_flag=True, 
              help='Create a local config.json file with current settings')
@click.option('--create-global-config', is_flag=True, 
              help='Create a global config.json file with current settings')
@click.option('--run-after-config-create', is_flag=True, default=True,
              help='Run the command after creating config file(s)')
@click.option('--show-config', is_flag=True,
              help='Show effective configuration and exit')
@click.option('--debug', is_flag=True, help='Enable debug mode with additional logging')
@click.option('--dry-run', is_flag=True, help='Perform a dry run without saving any files')
@click.pass_context
def index(ctx, path, recursive, output, create_local_config, create_global_config,
          run_after_config_create, show_config, debug, dry_run):
    """Index documents in the specified path."""
    # Convert click context to dictionary
    args = {
        'command': 'index',
        'path': path,
        'recursive': recursive,
        'output': output,
        'create_local_config': create_local_config,
        'create_global_config': create_global_config,
        'run_after_config_create': run_after_config_create,
        'show_config': show_config,
        'debug': debug,
        'dry_run': dry_run
    }
    
    try:
        # Validate and apply configuration
        effective_config = validate_and_apply_config('index', args)
        
        # Handle configuration creation if requested
        config_created = False
        
        if create_local_config:
            config.create_local_config()
            config_created = True
            console.print("[bold green]✓[/] Created local configuration file")
            
        if create_global_config:
            config.create_global_config()
            config_created = True
            console.print("[bold green]✓[/] Created global configuration file")
            
        # Show configuration if requested
        if show_config:
            table = Table(title="Effective Configuration")
            table.add_column("Option", style="cyan")
            table.add_column("Value", style="green")
            
            for k, v in sorted(effective_config.items()):
                if v is not None:
                    table.add_row(k, str(v))
                    
            console.print(table)
            
            if not run_after_config_create or not config_created:
                return 0
        
        # If this is just a dry run or config operation, we're done
        if dry_run and not debug:
            console.print("[bold yellow]Dry run mode:[/] No files will be modified")
            return 0
            
        # Execute the actual command
        console.print(f"Indexing documents in [bold blue]{path}[/]")
        
        if recursive:
            console.print("Recursive mode: [bold green]enabled[/]")
        if output:
            console.print(f"Output will be saved to: [bold yellow]{output}[/]")
        
        # Create and run the indexer (skipping actual operations in dry-run mode)
        indexer = DocIndexer(output_path=output)
        
        if not dry_run:
            results = indexer.index_directory(path, recursive=recursive)
            
            # Display results
            if results:
                table = Table(title="Indexed Documents")
                table.add_column("Path", style="cyan")
                table.add_column("Size", style="green")
                table.add_column("Extension", style="yellow")
                
                for file_path, info in results.items():
                    table.add_row(
                        Path(file_path).name, 
                        f"{info['size'] / 1024:.2f} KB",
                        info['extension']
                    )
                
                console.print(table)
                console.print(f"[bold green]Indexed {len(results)} documents![/]")
            else:
                console.print("[yellow]No documents found to index.[/]")
        else:
            console.print("[bold yellow]Dry run complete[/]")
    
    except ValidationError as e:
        console.print(f"[bold red]Validation Error:[/] {str(e)}")
        return 1
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        if debug:
            console.print_exception()
        return 1
    
    return 0

@main.command()
@click.option('--source', type=click.Choice(['all', 'global', 'local', 'effective']), 
              default='effective', help='Which configuration source to display')
def config(source):
    """Display current configuration settings."""
    # Load configuration
    config.load_config()
    
    if source in ['all', 'global']:
        config.load_global_config()
        if config._global_config:
            console.print(Panel(
                json.dumps(config._global_config, indent=2),
                title="Global Configuration (~/.docindexer/config.json)",
                border_style="blue"
            ))
        else:
            console.print("[yellow]No global configuration found[/]")
    
    if source in ['all', 'local']:
        config.load_local_config()
        if config._local_config:
            console.print(Panel(
                json.dumps(config._local_config, indent=2),
                title="Local Configuration (./config.json)",
                border_style="green"
            ))
        else:
            console.print("[yellow]No local configuration found[/]")
    
    if source in ['all', 'effective']:
        effective_config = config.as_dict()
        if effective_config:
            console.print(Panel(
                json.dumps(effective_config, indent=2),
                title="Effective Configuration",
                border_style="yellow"
            ))
        else:
            console.print("[yellow]No configuration found[/]")
    
    return 0

@main.command()
def schema():
    """Visualize CLI schema structure."""
    schema_data = validator.schema
    
    # Create a tree visualization of the schema
    tree = Tree(f"[bold magenta]{schema_data['name']} CLI[/bold magenta]")
    
    # Add global options
    if schema_data.get('globalOptions'):
        global_branch = tree.add("[bold blue]Global Options[/bold blue]")
        for option in schema_data['globalOptions']:
            global_branch.add(f"[cyan]{option['flag']}[/cyan]: {option['description']}")
    
    # Add commands
    if schema_data.get('commands'):
        commands_branch = tree.add("[bold green]Commands[/bold green]")
        for command in schema_data['commands']:
            cmd_branch = commands_branch.add(f"[yellow]{command['name']}[/yellow]: {command['description']}")
            
            # Add command options
            for option in command.get('options', []):
                required = "[bold red]*[/bold red] " if option.get('required', False) else ""
                cmd_branch.add(f"{required}[cyan]{option['flag']}[/cyan]: {option['description']}")
    
    # Add common options
    if schema_data.get('commonOptions'):
        common_branch = tree.add("[bold blue]Common Options[/bold blue]")
        for option in schema_data['commonOptions']:
            required = "[bold red]*[/bold red] " if option.get('required', False) else ""
            common_branch.add(f"{required}[cyan]{option['flag']}[/cyan]: {option['description']}")
    
    # Add configuration sources
    if schema_data.get('configurationSources'):
        config_branch = tree.add("[bold yellow]Configuration Sources[/bold yellow]")
        for source in schema_data['configurationSources']:
            priority = source.get('priority', 0)
            config_branch.add(f"[cyan]{priority}.[/cyan] {source['name']}: {source['description']}")
    
    console.print(tree)
    return 0

@main.command()
@click.argument('command', required=True)
@click.argument('args', nargs=-1)
def structure(command, args):
    """Create a hierarchical JSON representation of markdown structure."""
    console.print("[bold]The 'structure' command is not yet implemented[/]")
    console.print(f"Called with command: {command}, args: {args}")
    return 1

if __name__ == '__main__':
    main()