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
        
        # Handle configuration creation if requested
        config_created = False
        
        if args.get('create_local_config', False):
            config_manager.create_local_config()
            config_created = True
            console.print("[bold green]✓[/] Created local configuration file")
            
        if args.get('create_global_config', False):
            config_manager.create_global_config()
            config_created = True
            console.print("[bold green]✓[/] Created global configuration file")
            
        # Show configuration if requested
        if args.get('show_config', False):
            table = Table(title="Effective Configuration")
            table.add_column("Option", style="cyan")
            table.add_column("Value", style="green")
            
            for k, v in sorted(effective_config.items()):
                if v is not None:
                    table.add_row(k, str(v))
                    
            console.print(table)
            
            if not args.get('run_after_config_create', True) or not config_created:
                return 0
        
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
        indexer = DocIndexer(output_path=output)
        
        if not args.get('dry_run', False):
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
    @click.option('--recursive', '-r', '-R', is_flag=True, help='Index documents recursively.')
    @click.option('--output', '-o', type=click.Path(), help='Output file path.')
    @click.option('--create-local-config', is_flag=True, 
                help='Create a local config.json file with current settings')
    @click.option('--create-global-config', is_flag=True, 
                help='Create a global config.json file with current settings')
    @click.option('--run-after-config-create/--no-run-after-config-create', is_flag=True, default=True,
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
        
        return execute_index_command(config_manager, args, validate_and_apply_config)