#!/usr/bin/env python3
"""Implementation of the structure command for DocIndexer CLI."""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

import click
from rich.console import Console
from rich.progress import Progress

from .file_iterator import FileIterator, FileInfo
from .validator import ValidationError
from .structure.organizer import Organizer

# Initialize console for rich output
console = Console()



def execute_structure_command(config_manager, args: Dict[str, Any], validate_and_apply_config):
    """Execute the structure command.
    
    Args:
        config_manager: Configuration manager instance
        args: Command arguments
        validate_and_apply_config: Function to validate and apply configuration
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Validate and apply configuration
        effective_config = validate_and_apply_config('structure', args)
        
        # Show debug information if requested
        if args.get('debug', False):
            console.print("\n[bold blue]Configuration:[/]")
            console.print(json.dumps(effective_config, indent=2))
        
        # Create file iterator to get the list of files
        console.print(f"\n[bold]Finding files based on configuration...[/]")
        file_iterator = FileIterator(config_manager)
        
        # Load files with progress indicator
        with Progress() as progress:
            task = progress.add_task("[cyan]Scanning directories...", total=None)
            file_iterator.load()
            progress.update(task, completed=100)
        
        # Get the list of files
        files = file_iterator.get_files()
        file_count = len(files)
        
        if file_count == 0:
            console.print("[yellow]No files found matching the criteria.[/]")
            return 0
        
        console.print(f"[green]Found {file_count} files for processing[/]")
        
        # Get output folder from configuration
        output_folder = effective_config.get('output_folder', './output')
        os.makedirs(output_folder, exist_ok=True)
        
        # Get omit properties (if any)
        omit_properties = []
        if args.get('ommit_properties'):
            omit_properties = args.get('ommit_properties').split(',')
            console.print(f"[blue]Will omit the following properties: {', '.join(omit_properties)}[/]")
        
        # Process files with progress indicator
        with Progress() as progress:
            task = progress.add_task("[cyan]Processing files...", total=file_count)
            
            # Process each file
            for file_info in files:
                file_path = file_info.path

                structure = Organizer.load_structure_from_markdown_file(file_path)
                print (file_path)

                
                # =============================================
                # TODO: Insert actual structure code here
                # =============================================
                # This is where the actual structure-building code will be inserted.
                # The code will:
                # 1. Read the file content
                # 2. Parse it to extract hierarchical structure
                # 3. Generate a JSON representation
                # 4. Save the result to the output folder
                #
                # Example placeholder:
                # structure = build_structure(file_path, omit_properties)
                # output_path = Path(output_folder) / f"{file_path.stem}.structure.json"
                # with open(output_path, 'w') as f:
                #     json.dump(structure, f, indent=2)
                
                # For now, just output a placeholder message
                if args.get('debug', False):
                    # Just print the file path without any formatting to avoid duplicate output
                    print(f"  - Would process: {file_path}")
                
                # Update progress
                progress.update(task, advance=1)
        
        console.print(f"\n[bold green]Structure processing complete![/]")
        console.print(f"[blue]Output folder: {output_folder}[/]")
        
        return 0
    
    except ValidationError as e:
        console.print(f"[bold red]Validation Error:[/] {str(e)}")
        return 1
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        if args.get('debug', False):
            console.print_exception()
        return 1

def setup_structure_command(main_group, validate_and_apply_config, config_manager):
    """Set up the structure command for the main CLI group.
    
    Args:
        main_group: Click group to attach the command to
        validate_and_apply_config: Function to validate and apply configuration
        config_manager: Configuration manager instance
    """
    @main_group.command()
    @click.option('--ommit-properties', help='Comma-separated list of properties to omit from the JSON output (e.g., "items,size")')
    # Common options for file discovery
    @click.option('--source-folder', '-s', help='Path to the folder containing files to be processed')
    @click.option('--catalogue', '-c', help='Path to a catalogue JSON file')
    @click.option('--file-name', '-n', help='the name of the file to be processed')
    
    # Common file filtering options
    @click.option('--pattern', '-p', help='Pattern to match file names (glob pattern by default)')
    @click.option('--regex', is_flag=True, help='Use regular expressions instead of glob patterns')
    @click.option('--sort-by', type=click.Choice(['name', 'date', 'size']), default='name',
                help='Sort files by: name, date, or size')
    @click.option('--desc', is_flag=True, help='Sort in descending order')
    @click.option('--max-depth', type=int, help='Maximum directory depth for recursive search')
    
    # Other common options
    @click.option('--recursive/--no-recursive', '-R', default=True, help='Process files in subfolders recursively')
    @click.option('--limit', '-l', type=int, help='Limit the number of files to be processed')
    @click.option('--random', is_flag=True, help='Process files in random order')
    @click.option('--output-folder', '-o', help='Path to the folder where structure files should be saved')
    @click.option('--debug', is_flag=True, help='Enable debug mode with additional logging')
    @click.option('--include-hidden', is_flag=True, help='Include hidden files and directories (starting with .)')
    @click.pass_context
    def structure(ctx, ommit_properties, source_folder, catalogue, file_name, 
                  pattern, regex, sort_by, desc, max_depth, recursive, limit, random, 
                  output_folder, debug, include_hidden):
        """Create a hierarchical JSON representation of markdown structure."""
        command_args = {
            'command': 'structure',
            'ommit_properties': ommit_properties,
            'source_folder': source_folder,
            'catalogue': catalogue,
            'file_name': file_name,
            'pattern': pattern,
            'use_regex': regex,
            'sort_by': sort_by,
            'sort_desc': desc,
            'max_depth': max_depth,
            'recursive': recursive,
            'limit': limit,
            'random': random,
            'output_folder': output_folder,
            'debug': debug,
            'include_hidden': include_hidden
        }
        
        return execute_structure_command(config_manager, command_args, validate_and_apply_config)