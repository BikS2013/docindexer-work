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
from rich.progress import Progress
from pathlib import Path
import os
from typing import Any, Dict, List, Optional

from .indexer import DocIndexer
from .validator import SchemaValidator, ValidationError
from .config import Configuration
from .file_iterator import FileIterator, FileInfo
from .list_command import setup_list_command
from .index_command import setup_index_command
from .schema_command import setup_schema_command
from .config_command import setup_config_command

# Initialize console for rich output
console = Console()

# Create configuration and validator instances
config_manager = Configuration()
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
    config_manager.load_config()
    
    # Apply defaults from schema
    args_with_defaults = validator.apply_defaults(normalized_args, command)
    
    # Validate the command arguments
    is_valid, errors = validator.validate_command(command, args_with_defaults)
    if not is_valid:
        error_msg = "\n".join(errors)
        raise click.UsageError(f"Validation failed:\n{error_msg}")
    
    # Update configuration with command-line arguments
    config_manager.set_cli_args(args_with_defaults)
    
    return config_manager.as_dict()

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

# Command will be set up after main group is defined

# Command will be set up after main group is defined

# Command will be set up after main group is defined

# Command will be set up after main group is defined


@main.command()
@click.argument('command', required=True)
@click.argument('args', nargs=-1)
def structure(command, args):
    """Create a hierarchical JSON representation of markdown structure."""
    console.print("[bold]The 'structure' command is not yet implemented[/]")
    console.print(f"Called with command: {command}, args: {args}")
    return 1

# Set up commands that were defined in separate modules
setup_index_command(main, validate_and_apply_config, config_manager)
setup_list_command(main, validate_and_apply_config, config_manager)
setup_schema_command(main, validator)
setup_config_command(main, config_manager)

if __name__ == '__main__':
    main()