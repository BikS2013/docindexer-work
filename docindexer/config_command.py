#!/usr/bin/env python3
"""Implementation of the config command for DocIndexer CLI."""

import json
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Initialize console for rich output
console = Console()

def execute_config_command(config_manager, source, create_local, create_global, show):
    """Execute the config command.
    
    Args:
        config_manager: Configuration manager instance
        source: Which configuration source to display
        create_local: Whether to create a local config file
        create_global: Whether to create a global config file
        show: Whether to show the effective configuration
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Load configuration
    config_manager.load_config()
    
    # Handle configuration creation if requested
    config_created = False
    
    if create_local:
        config_manager.create_local_config()
        config_created = True
        console.print("[bold green]✓[/] Created local configuration file")
        
    if create_global:
        config_manager.create_global_config()
        config_created = True
        console.print("[bold green]✓[/] Created global configuration file")
    
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

def setup_config_command(main_group, config_manager):
    """Set up the config command for the main CLI group.
    
    Args:
        main_group: Click group to attach the command to
        config_manager: Configuration manager instance
    """
    @main_group.command()
    @click.option('--source', type=click.Choice(['all', 'global', 'local', 'effective']), 
                default='effective', help='Which configuration source to display')
    @click.option('--create-local', is_flag=True, 
                help='Create a local config.json file with current settings')
    @click.option('--create-global', is_flag=True, 
                help='Create a global config.json file with current settings')
    @click.option('--show', is_flag=True,
                help='Show effective configuration and exit')
    def config(source, create_local, create_global, show):
        """Display current configuration settings."""
        return execute_config_command(config_manager, source, create_local, create_global, show)