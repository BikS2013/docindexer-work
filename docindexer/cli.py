#!/usr/bin/env python3
"""Command line interface for DocIndexer."""

import click
from rich.console import Console
from rich.table import Table
from pathlib import Path
from .indexer import DocIndexer

console = Console()

@click.group()
@click.version_option()
def main():
    """DocIndexer - A command line tool for indexing documents."""
    pass

@main.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--recursive', '-r', is_flag=True, help='Index documents recursively.')
@click.option('--output', '-o', type=click.Path(), help='Output file path.')
def index(path, recursive, output):
    """Index documents in the specified path."""
    console.print(f"Indexing documents in [bold blue]{path}[/]")
    if recursive:
        console.print("Recursive mode: [bold green]enabled[/]")
    if output:
        console.print(f"Output will be saved to: [bold yellow]{output}[/]")
    
    # Create and run the indexer
    indexer = DocIndexer(output_path=output)
    try:
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
    
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    main()