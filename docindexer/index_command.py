#!/usr/bin/env python3
"""Implementation of the index command for DocIndexer CLI."""

import json
from typing import Dict, Any
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .indexer import DocIndexer
from .validator import ValidationError

# Initialize console for rich output
console = Console()

def execute_index_command(config_manager, args: Dict[str, Any], validate_and_apply_config):
    """Execute the index command.
    
    Args:
        config_manager: Configuration manager instance
        args: Command arguments
        validate_and_apply_config: Function to validate and apply configuration
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Validate and apply configuration
        effective_config = validate_and_apply_config('index', args)
        
        # No configuration-related functionality here anymore
        
        # If this is just a dry run or config operation, we're done
        if args.get('dry_run', False) and not args.get('debug', False):
            console.print("[bold yellow]Dry run mode:[/] No files will be modified")
            return 0
            
        # Execute the actual command
        path = args.get('path', '')
        recursive = args.get('recursive', False)
        output = args.get('output', None)
        
        console.print(f"Indexing documents in [bold blue]{path}[/]")
        
        if recursive:
            console.print("Recursive mode: [bold green]enabled[/]")
        if output:
            console.print(f"Output will be saved to: [bold yellow]{output}[/]")
        
        # Create and run the indexer (skipping actual operations in dry-run mode)
        indexer = DocIndexer(output_path=output, config=config_manager)
        
        if not args.get('dry_run', False):
            # Pass all the filter options to the indexer, it will handle them through the FileIterator
            results = indexer.index_directory(
                path, 
                recursive=recursive,
                pattern=args.get('pattern'),
                use_regex=args.get('use_regex', False),
                sort_by=args.get('sort_by', 'name'),
                sort_desc=args.get('sort_desc', False),
                max_depth=args.get('max_depth'),
                limit=args.get('limit'),
                random=args.get('random', False),
                include_hidden=args.get('include_hidden', False)
            )
            
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
        if args.get('debug', False):
            console.print_exception()
        return 1
    
    return 0

def setup_index_command(main_group, validate_and_apply_config, config_manager):
    """Set up the index command for the main CLI group.
    
    Args:
        main_group: Click group to attach the command to
        validate_and_apply_config: Function to validate and apply configuration
        config_manager: Configuration manager instance
    """
    @main_group.command()
    @click.argument('path', type=click.Path(exists=True))
    
    # Common file filtering options (moved from list command to common)
    @click.option('--pattern', '-p', help='Pattern to match file names (glob pattern by default). Patterns must be included in quotes')
    @click.option('--regex', is_flag=True, help='Use regular expressions instead of glob patterns. Regular expressions must be included in quotes')
    @click.option('--sort-by', type=click.Choice(['name', 'date', 'size']), default='name',
                help='Sort files by: name, date, or size')
    @click.option('--desc', is_flag=True, help='Sort in descending order')
    @click.option('--max-depth', type=int, help='Maximum directory depth for recursive search')
    
    # Other options specific to index or shared
    @click.option('--recursive', '-R', is_flag=True, help='Index documents recursively.')
    @click.option('--output', '-o', type=click.Path(), help='Output file path.')
    @click.option('--limit', '-l', type=int, help='Limit the number of files to be processed')
    @click.option('--random', is_flag=True, help='Process files in random order')
    @click.option('--debug', is_flag=True, help='Enable debug mode with additional logging')
    @click.option('--dry-run', is_flag=True, help='Perform a dry run without saving any files')
    @click.option('--include-hidden', is_flag=True, help='Include hidden files and directories (starting with .)')
    @click.pass_context
    def index(ctx, path, pattern, regex, sort_by, desc, max_depth, recursive, output,
              limit, random, debug, dry_run, include_hidden):
        """Index documents in the specified path."""
        # Convert click context to dictionary
        args = {
            'command': 'index',
            'path': path,
            'pattern': pattern,
            'use_regex': regex,
            'sort_by': sort_by,
            'sort_desc': desc, 
            'max_depth': max_depth,
            'recursive': recursive,
            'output': output,
            'limit': limit,
            'random': random,
            'debug': debug,
            'dry_run': dry_run,
            'include_hidden': include_hidden
        }
        
        return execute_index_command(config_manager, args, validate_and_apply_config)