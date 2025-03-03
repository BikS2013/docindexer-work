# FileIterator Class Diagram

```mermaid
classDiagram
    class Configuration {
        -_local_config_path : Path
        -_global_config_path : Path
        -_global_config : Dict
        -_local_config : Dict
        -_cli_args : Dict
        -_config : Dict
        +load_global_config() : None
        +load_local_config() : None
        +set_cli_args(args) : None
        -_update_merged_config() : None
        +create_local_config() : bool
        +create_global_config() : bool
        +get(key, default) : Any
        +__getitem__(key) : Any
        +__contains__(key) : bool
        +keys() : Set
        +as_dict() : Dict
        +load_config() : None
    }
    
    class SortOrder {
        <<enumeration>>
        NAME_ASC
        NAME_DESC
        DATE_ASC
        DATE_DESC
        SIZE_ASC
        SIZE_DESC
        RANDOM
        NONE
    }
    
    class FileInfo {
        +path : Path
        +size : int
        +modified : float
        +extension : str
        +name() : str
        +absolute_path() : str
        +from_path(path) : FileInfo
    }
    
    class FileFilter {
        <<abstract>>
        +matches(file_info) : bool
    }
    
    class ExtensionFilter {
        -extensions : List[str]
        +matches(file_info) : bool
    }
    
    class PatternFilter {
        -pattern : str
        -glob : bool
        -regex : Pattern
        +matches(file_info) : bool
    }
    
    class SizeFilter {
        -min_size : Optional[int]
        -max_size : Optional[int]
        +matches(file_info) : bool
    }
    
    class DateFilter {
        -min_date : Optional[float]
        -max_date : Optional[float]
        +matches(file_info) : bool
    }
    
    class CompositeFilter {
        -filters : List[FileFilter]
        +matches(file_info) : bool
    }
    
    class FileIterator {
        -config : Configuration
        -file_filter : FileFilter
        -_files : List[FileInfo]
        -_index : int
        -_loaded : bool
        -_create_filter() : FileFilter
        -_get_sort_key() : Callable
        -_get_sort_order() : SortOrder
        -_discover_files() : None
        -_load_from_catalogue(catalogue_path) : None
        -_scan_directory(directory, recursive, current_depth, max_depth) : None
        +load() : None
        +reset() : None
        +__iter__() : FileIterator
        +__next__() : FileInfo
        +get_files() : List[FileInfo]
        +count() : int
        +__len__() : int
    }
    
    class CatalogueBuilder {
        -output_path : str
        -files : List[Dict]
        +add_file(file_info) : None
        +add_files(file_iterator) : None
        +save() : None
    }
    
    Configuration <-- FileIterator : uses
    FileFilter <|-- ExtensionFilter : inherits
    FileFilter <|-- PatternFilter : inherits
    FileFilter <|-- SizeFilter : inherits
    FileFilter <|-- DateFilter : inherits
    FileFilter <|-- CompositeFilter : inherits
    FileFilter <-- FileIterator : uses
    FileInfo <-- FileIterator : contains
    FileInfo <-- CatalogueBuilder : uses
    FileIterator <-- CatalogueBuilder : uses
    SortOrder <-- FileIterator : uses
```

# CLI Controller Integration

```mermaid
classDiagram
    class main {
        <<Click Command Group>>
        +index()
        +list()
        +config()
        +schema()
        +structure()
    }
    
    class FileIterator {
        -config : Configuration
        -file_filter : FileFilter
        -_files : List[FileInfo]
        -_index : int
        -_loaded : bool
        +load() : None
        +reset() : None
        +__iter__() : FileIterator
        +__next__() : FileInfo
        +get_files() : List[FileInfo]
        +count() : int
        +__len__() : int
    }
    
    class SchemaValidator {
        -schema : Dict
        -global_options : Dict[str, SchemaOption]
        -common_options : Dict[str, SchemaOption]
        -command_options : Dict[str, Dict[str, SchemaOption]]
        -commands : List[str]
        -config_sources : List[Dict]
        +load_schema(schema_path) : None
        +validate_command(command, args) : Tuple[bool, List[str]]
        +get_option_by_flag(flag, command) : Optional[SchemaOption]
        +normalize_args(args) : Dict
        +apply_defaults(args, command) : Dict
    }
    
    class Configuration {
        -_local_config_path : Path
        -_global_config_path : Path
        -_global_config : Dict
        -_local_config : Dict
        -_cli_args : Dict
        -_config : Dict
        +load_config() : None
        +set_cli_args(args) : None
        +as_dict() : Dict
    }
    
    main --> SchemaValidator : uses
    main --> Configuration : uses
    main --> FileIterator : uses
    SchemaValidator --> Configuration : configures
    Configuration --> FileIterator : configures
```

# Usage Examples

## Basic Usage

```python
from docindexer.config import Configuration
from docindexer.file_iterator import FileIterator

# Create a configuration object
config = Configuration()

# Set configuration values
config.set_cli_args({
    "source_folder": "/path/to/documents",
    "recursive": True,
    "pattern": "*.md",
    "sort_by": "date",
    "sort_desc": True,
    "limit": 100
})

# Create a file iterator
file_iterator = FileIterator(config)

# Iterate through files
for file_info in file_iterator:
    print(f"Processing {file_info.name} ({file_info.size} bytes)")
    
    # Do something with the file
    # ...

# Get count of files
count = len(file_iterator)
print(f"Found {count} files")

# Get all files as a list
files = file_iterator.get_files()
```

## CLI Controller Integration

```python
import click
from rich.console import Console
from rich.table import Table
from docindexer.config import Configuration
from docindexer.file_iterator import FileIterator

console = Console()
config = Configuration()

@click.command()
@click.option('--source-folder', '-s', help='Path to the folder containing files')
@click.option('--recursive/--no-recursive', '-r', default=True, help='Process files recursively')
@click.option('--pattern', '-p', help='Pattern to match file names')
def list_files(source_folder, recursive, pattern):
    """List files based on configuration."""
    # Set configuration from command-line arguments
    config.set_cli_args({
        "source_folder": source_folder,
        "recursive": recursive,
        "pattern": pattern
    })
    
    # Create file iterator
    file_iterator = FileIterator(config)
    
    # Display files in a table
    table = Table(title=f"Files in {source_folder}")
    table.add_column("Name", style="cyan")
    table.add_column("Size", style="green", justify="right")
    table.add_column("Modified", style="yellow")
    
    for file_info in file_iterator:
        size_str = f"{file_info.size / 1024:.2f} KB"
        from datetime import datetime
        date_str = datetime.fromtimestamp(file_info.modified).strftime('%Y-%m-%d %H:%M:%S')
        table.add_row(file_info.name, size_str, date_str)
    
    console.print(table)
    
if __name__ == '__main__':
    list_files()
```

## Creating a Catalogue

```python
from docindexer.config import Configuration
from docindexer.file_iterator import FileIterator, CatalogueBuilder

# Create configuration
config = Configuration()
config.set_cli_args({
    "source_folder": "/path/to/documents",
    "recursive": True
})

# Create file iterator
file_iterator = FileIterator(config)

# Create catalogue builder
catalogue_builder = CatalogueBuilder("/path/to/catalogue.json")

# Add files to catalogue
catalogue_builder.add_files(file_iterator)

# Save catalogue
catalogue_builder.save()
```