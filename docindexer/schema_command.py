#!/usr/bin/env python3
"""Implementation of the schema command for DocIndexer CLI."""

import click
from rich.console import Console
from rich.tree import Tree

# Initialize console for rich output
console = Console()

def execute_schema_command(validator):
    """Execute the schema command.
    
    Args:
        validator: SchemaValidator instance
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
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
            
            # Add note about inherited options if applicable
            if command.get('inheritsCommonOptions', False):
                cmd_branch.add("[italic]Also includes common options[/italic]")
    
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

def setup_schema_command(main_group, validator):
    """Set up the schema command for the main CLI group.
    
    Args:
        main_group: Click group to attach the command to
        validator: SchemaValidator instance
    """
    @main_group.command()
    def schema():
        """Visualize CLI schema structure."""
        return execute_schema_command(validator)