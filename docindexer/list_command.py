#!/usr/bin/env python3
"""Implementation of the list command for DocIndexer CLI."""

import json
from typing import Dict, Any
from datetime import datetime
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from .file_iterator import FileIterator, FileInfo
from .validator import ValidationError

# Initialize console for rich output
console = Console()

def format_size(size: int) -> str:
    """Format file size in human-readable format.
    
    Args:
        size: Size in bytes
        
    Returns:
        Human-readable size string
    """
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f} KB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"

def execute_list_command(config_manager, args: Dict[str, Any], validate_and_apply_config):
    """Execute the list command.
    
    Args:
        config_manager: Configuration manager instance
        args: Command arguments
        validate_and_apply_config: Function to validate and apply configuration
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Validate and apply configuration
        effective_config = validate_and_apply_config('list', args)
        
        # Show debug information if requested
        if args.get('debug', False):
            console.print("\n[bold blue]Configuration:[/]")
            console.print(Panel(json.dumps(effective_config, indent=2), title="Effective Configuration"))
        
        # Create file iterator
        file_iterator = FileIterator(config_manager)
        
        # Display file count and processing message
        console.print(f"\n[bold]Finding files based on configuration...[/]")
        
        # Load files with progress indicator
        with Progress() as progress:
            task = progress.add_task("[cyan]Scanning directories...", total=None)
            file_iterator.load()
            progress.update(task, completed=100)
        
        file_count = file_iterator.count()
        
        if file_count == 0:
            console.print("[yellow]No files found matching the criteria.[/]")
            return 0
        
        # Create a table to display files
        table = Table(title=f"Found {file_count} files")
        table.add_column("File Name", style="cyan")
        table.add_column("Path", style="green")
        table.add_column("Size", style="yellow", justify="right")
        table.add_column("Modified", style="magenta")
        
        # Add files to the table
        for file_info in file_iterator:
            # Format the modified time
            modified_time = datetime.fromtimestamp(file_info.modified).strftime('%Y-%m-%d %H:%M:%S')
            
            # Format the size
            size_str = format_size(file_info.size)
            
            table.add_row(
                file_info.name,
                str(file_info.path.parent),
                size_str,
                modified_time
            )
        
        console.print(table)
        
        return 0
    
    except ValidationError as e:
        console.print(f"[bold red]Validation Error:[/] {str(e)}")
        return 1
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        if args.get('debug', False):
            console.print_exception()
        return 1

def setup_list_command(main_group, validate_and_apply_config, config_manager):
    """Set up the list command for the main CLI group.
    
    Args:
        main_group: Click group to attach the command to
        validate_and_apply_config: Function to validate and apply configuration
        config_manager: Configuration manager instance
    """
    @main_group.command()
    # Common options for file discovery
    @click.option('--source-folder', '-s', help='Path to the folder containing files to be processed')
    @click.option('--catalogue', '-c', help='Path to a catalogue JSON file')
    @click.option('--file-name', '-n', help='the name of the file to be processed')
    
    # Common file filtering options (moved from command-specific to common)
    @click.option('--pattern', '-p', help='Pattern to match file names (glob pattern by default). Patterns must be included in quotes')
    @click.option('--regex', is_flag=True, help='Use regular expressions instead of glob patterns. Regular expressions must be included in quotes')
    @click.option('--sort-by', type=click.Choice(['name', 'date', 'size']), default='name',
                help='Sort files by: name, date, or size')
    @click.option('--desc', is_flag=True, help='Sort in descending order')
    @click.option('--max-depth', type=int, help='Maximum directory depth for recursive search')
    
    # Other common options
    @click.option('--recursive/--no-recursive', '-R', default=True, help='Process files in subfolders recursively')
    @click.option('--limit', '-l', type=int, help='Limit the number of files to be processed')
    @click.option('--random', '-r', is_flag=True, help='Process files in random order')
    @click.option('--debug', is_flag=True, help='Enable debug mode with additional logging')
    @click.option('--include-hidden', is_flag=True, help='Include hidden files and directories (starting with .)')
    @click.pass_context
    def list(ctx, pattern, regex, sort_by, desc, max_depth, source_folder, catalogue,
             file_name, recursive, limit, random, debug, include_hidden):
        """List files that would be processed based on configuration."""
        args = {
            'command': 'list',
            'pattern': pattern,
            'use_regex': regex,
            'sort_by': sort_by,
            'sort_desc': desc,
            'max_depth': max_depth,
            'source_folder': source_folder,
            'catalogue': catalogue,
            'file_name': file_name,
            'recursive': recursive,
            'limit': limit,
            'random': random,
            'debug': debug,
            'include_hidden': include_hidden
        }
        
        return execute_list_command(config_manager, args, validate_and_apply_config)