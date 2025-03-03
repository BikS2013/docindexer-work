#!/usr/bin/env python3
"""Implementation of the config command for DocIndexer CLI."""

import json
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Initialize console for rich output
console = Console()

def execute_config_command(config_manager, args, validate_and_apply_config):
    """Execute the config command.
    
    Args:
        config_manager: Configuration manager instance
        args: Command arguments
        validate_and_apply_config: Function to validate and apply configuration
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Extract specific config options
    source = args.get('source', 'effective')
    create_local = args.get('create_local', False)
    create_global = args.get('create_global', False)
    show = args.get('show', False)
    debug = args.get('debug', False)
    
    try:
        # Validate and apply all provided options to configuration
        # This ensures all file filtering options are captured
        effective_config = validate_and_apply_config('config', args)
        
        # Show debug information if requested
        if debug:
            console.print("\n[bold blue]Configuration to be saved:[/]")
            console.print(json.dumps(effective_config, indent=2))
        
        # Handle configuration creation if requested
        config_created = False
        
        if create_local:
            config_manager.create_local_config()
            config_created = True
            console.print("[bold green]✓[/] Created local configuration file with all provided options")
            
        if create_global:
            config_manager.create_global_config()
            config_created = True
            console.print("[bold green]✓[/] Created global configuration file with all provided options")
    
        # Handle display options
        if source in ['all', 'global']:
            config_manager.load_global_config()
            if config_manager._global_config:
                console.print(Panel(
                    json.dumps(config_manager._global_config, indent=2),
                    title="Global Configuration (~/.docindexer/config.json)",
                    border_style="blue"
                ))
            else:
                console.print("[yellow]No global configuration found[/]")
        
        if source in ['all', 'local']:
            config_manager.load_local_config()
            if config_manager._local_config:
                console.print(Panel(
                    json.dumps(config_manager._local_config, indent=2),
                    title="Local Configuration (./config.json)",
                    border_style="green"
                ))
            else:
                console.print("[yellow]No local configuration found[/]")
        
        if source in ['all', 'effective'] or show:
            effective_config = config_manager.as_dict()
            if effective_config:
                console.print(Panel(
                    json.dumps(effective_config, indent=2),
                    title="Effective Configuration",
                    border_style="yellow"
                ))
            else:
                console.print("[yellow]No configuration found[/]")
        
        return 0
    
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        if debug:
            console.print_exception()
        return 1

def setup_config_command(main_group, config_manager, validate_and_apply_config=None):
    """Set up the config command for the main CLI group.
    
    Args:
        main_group: Click group to attach the command to
        config_manager: Configuration manager instance
        validate_and_apply_config: Function to validate and apply configuration
    """
    @main_group.command()
    # Config-specific options
    @click.option('--source', type=click.Choice(['all', 'global', 'local', 'effective']), 
                default='effective', help='Which configuration source to display')
    @click.option('--create-local', is_flag=True, 
                help='Create a local config.json file with current settings')
    @click.option('--create-global', is_flag=True, 
                help='Create a global config.json file with current settings')
    @click.option('--show', is_flag=True,
                help='Show effective configuration and exit')
    
    # Common options for file discovery
    @click.option('--source-folder', '-s', help='Path to the folder containing files to be processed')
    @click.option('--catalogue', '-c', help='Path to a catalogue JSON file')
    @click.option('--file-name', '-n', help='the name of the file to be processed')
    
    # Common file filtering options
    @click.option('--pattern', '-p', help='Pattern to match file names (glob pattern by default)')
    @click.option('--regex', is_flag=True, help='Use regular expressions instead of glob patterns')
    @click.option('--sort-by', type=click.Choice(['name', 'date', 'size']), default=None,
                help='Sort files by: name, date, or size')
    @click.option('--desc', is_flag=True, help='Sort in descending order')
    @click.option('--max-depth', type=int, help='Maximum directory depth for recursive search')
    
    # Other common options
    @click.option('--recursive/--no-recursive', default=None, help='Process files in subfolders recursively')
    @click.option('--limit', '-l', type=int, help='Limit the number of files to be processed')
    @click.option('--random', is_flag=True, help='Process files in random order')
    @click.option('--output-folder', '-o', help='Path to the folder where structure files should be saved')
    @click.option('--debug', is_flag=True, help='Enable debug mode with additional logging')
    @click.option('--include-hidden', is_flag=True, help='Include hidden files and directories (starting with .)')
    @click.option('--omit-properties', help='Properties to omit from processing (for commands that support it)')
    @click.pass_context
    def config(ctx, source, create_local, create_global, show, source_folder, catalogue, file_name,
              pattern, regex, sort_by, desc, max_depth, recursive, limit, random, output_folder, 
              debug, include_hidden, omit_properties):
        """Display and manage configuration settings."""
        # Create dictionary of all parameters
        command_args = {
            'command': 'config',
            'source': source,
            'create_local': create_local,
            'create_global': create_global,
            'show': show,
            'debug': debug
        }
        
        # Add file filtering options only if they were specified
        if source_folder is not None:
            command_args['source_folder'] = source_folder
        if catalogue is not None:
            command_args['catalogue'] = catalogue
        if file_name is not None:
            command_args['file_name'] = file_name
        if pattern is not None:
            command_args['pattern'] = pattern
        if regex:
            command_args['use_regex'] = regex
        if sort_by is not None:
            command_args['sort_by'] = sort_by
        if desc:
            command_args['sort_desc'] = desc
        if max_depth is not None:
            command_args['max_depth'] = max_depth
        if recursive is not None:
            command_args['recursive'] = recursive
        if limit is not None:
            command_args['limit'] = limit
        if random:
            command_args['random'] = random
        if output_folder is not None:
            command_args['output_folder'] = output_folder
        if include_hidden:
            command_args['include_hidden'] = include_hidden
        if omit_properties is not None:
            command_args['omit_properties'] = omit_properties
            
        # Check if we have the validate_and_apply_config function
        # If not, use a simple pass-through function that just returns the args
        if validate_and_apply_config is None:
            def simple_validate(cmd, args):
                config_manager.set_cli_args(args)
                return config_manager.as_dict()
            validate_func = simple_validate
        else:
            validate_func = validate_and_apply_config
            
        return execute_config_command(config_manager, command_args, validate_func)