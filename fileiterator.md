# FileIterator - Comprehensive File Discovery and Filtering System

## Overview

The `FileIterator` is a powerful, configurable system for discovering, filtering, sorting, and iterating through files in a filesystem. It serves as the foundation for the DocIndexer application's file processing capabilities, providing a flexible and efficient way to locate and process files based on various criteria.

This document explains the architecture, capabilities, and usage patterns of the `FileIterator` and its supporting classes.

## System Architecture

```mermaid
graph TD
    CLI[CLI Interface] --> CONFIG[Configuration]
    CONFIG --> ITERATOR[FileIterator]
    ITERATOR --> DISCOVER[File Discovery]
    ITERATOR --> FILTER[Filtering]
    ITERATOR --> SORT[Sorting]
    
    DISCOVER --> DIR[Directory Scanner]
    DISCOVER --> CAT[Catalogue Loader]
    DISCOVER --> FILE[Single File]
    
    FILTER --> EXT[Extension Filter]
    FILTER --> PAT[Pattern Filter]
    FILTER --> SIZE[Size Filter]
    FILTER --> DATE[Date Filter]
    FILTER --> COMP[Composite Filter]
    
    SORT --> NAME[Name Sort]
    SORT --> DATESORT[Date Sort]
    SORT --> SIZESORT[Size Sort]
    SORT --> RANDOM[Random Order]

    ITERATOR --> FILEINFO[FileInfo]
    
    CAT <--> CATALOGUE[CatalogueBuilder]
    
    classDef main fill:#f96,stroke:#333,stroke-width:2px;
    classDef secondary fill:#bbf,stroke:#333,stroke-width:1px;
    classDef support fill:#bfb,stroke:#333,stroke-width:1px;
    
    class CLI,CONFIG,ITERATOR main;
    class DISCOVER,FILTER,SORT,CATALOGUE secondary;
    class FILEINFO,DIR,CAT,FILE,EXT,PAT,SIZE,DATE,COMP,NAME,DATESORT,SIZESORT,RANDOM support;
```

## Core Components

### 1. FileInfo

A dataclass that encapsulates metadata about a file:

```python
@dataclass
class FileInfo:
    path: Path           # Path object representing the file location
    size: int            # Size in bytes
    modified: float      # Modification time as Unix timestamp
    extension: str       # File extension (with leading dot)
```

**Key features:**
- Provides convenient properties (`name`, `absolute_path`)
- Factory method `from_path()` to create instances from Path objects
- Used as the primary data structure throughout the iterator system

### 2. FileFilter Hierarchy

An extensible filter system based on the Strategy pattern:

```mermaid
classDiagram
    class FileFilter {
        <<abstract>>
        +matches(FileInfo) bool
    }
    
    FileFilter <|-- ExtensionFilter
    FileFilter <|-- PatternFilter
    FileFilter <|-- SizeFilter
    FileFilter <|-- DateFilter
    FileFilter <|-- CompositeFilter
    
    CompositeFilter *-- FileFilter : contains
    
    class ExtensionFilter {
        -extensions: List[str]
        +matches(FileInfo) bool
    }
    
    class PatternFilter {
        -pattern: str
        -glob: bool
        -regex: Pattern
        +matches(FileInfo) bool
    }
    
    class SizeFilter {
        -min_size: int
        -max_size: int
        +matches(FileInfo) bool
    }
    
    class DateFilter {
        -min_date: float
        -max_date: float
        +matches(FileInfo) bool
    }
    
    class CompositeFilter {
        -filters: List[FileFilter]
        +matches(FileInfo) bool
    }
```

Each filter implements a `matches(file_info)` method that returns `True` if a file meets specific criteria.

### 3. FileIterator

The main class that ties everything together:

```mermaid
classDiagram
    class FileIterator {
        -config: Configuration
        -file_filter: FileFilter
        -_files: List[FileInfo]
        -_index: int
        -_loaded: bool
        -_include_hidden: bool
        +__init__(config: Configuration)
        -_create_filter() FileFilter
        -_get_sort_key() Callable
        -_get_sort_order() SortOrder
        -_discover_files() None
        -_load_from_catalogue(catalogue_path) None
        -_scan_directory(directory, recursive, current_depth, max_depth) None
        +load() None
        +reset() None
        +__iter__() FileIterator
        +__next__() FileInfo
        +get_files() List[FileInfo]
        +count() int
        +__len__() int
    }
    
    FileIterator --> "1" Configuration : uses
    FileIterator --> "1" FileFilter : filters with
    FileIterator --> "*" FileInfo : produces
    FileIterator --> "1" SortOrder : sorts by
    
    class Iterator {
        <<interface>>
        +__iter__()
        +__next__()
    }
    
    Iterator <|.. FileIterator : implements
```

The `FileIterator` provides a rich interface for:
- Configurable file discovery
- Filtering and sorting files
- Python iterator protocol support
- Bulk file retrieval

### 4. SortOrder

An enumeration defining different sorting strategies:

```python
class SortOrder(Enum):
    NAME_ASC = auto()
    NAME_DESC = auto()
    DATE_ASC = auto()
    DATE_DESC = auto()
    SIZE_ASC = auto()
    SIZE_DESC = auto()
    RANDOM = auto()
    NONE = auto()
```

### 5. CatalogueBuilder

A utility class for creating and saving file listings:

```python
class CatalogueBuilder:
    def __init__(self, output_path: str):
        # Initialize builder
        
    def add_file(self, file_info: FileInfo) -> None:
        # Add a file to the catalogue
        
    def add_files(self, file_iterator: FileIterator) -> None:
        # Add all files from an iterator
        
    def save(self) -> None:
        # Save the catalogue to a JSON file
```

## Key Features and Capabilities

### 1. Multiple File Discovery Methods

```mermaid
flowchart TD
    START([File Discovery]) --> CHECK{Source Type?}
    CHECK -->|File Name| SINGLE[Load Single File]
    CHECK -->|Source Folder| DIR[Scan Directory]
    CHECK -->|Catalogue| CAT[Load from Catalogue]
    
    DIR --> RECURSIVE{Recursive?}
    RECURSIVE -->|Yes| REC[Scan Subdirectories]
    RECURSIVE -->|No| FLAT[Scan Only Top Level]
    
    REC --> DEPTH{Max Depth?}
    DEPTH -->|Yes| LIMITED[Limit Recursion Depth]
    DEPTH -->|No| FULL[Full Recursion]
    
    SINGLE --> FILTER[Apply Filters]
    FLAT --> FILTER
    LIMITED --> FILTER
    FULL --> FILTER
    CAT --> FILTER
    
    FILTER --> SORT[Apply Sorting]
    SORT --> LIMIT{Apply Limit?}
    LIMIT -->|Yes| LIMITED_RESULTS[Truncate Results]
    LIMIT -->|No| ALL_RESULTS[Return All Files]
    
    LIMITED_RESULTS --> DONE([Done])
    ALL_RESULTS --> DONE
```

The `FileIterator` can discover files from different sources:

- **Direct file specification**:
  ```python
  # Load a single specific file
  config.set('file_name', '/path/to/file.txt')
  ```

- **Directory scanning**:
  ```python
  # Scan a directory (flat or recursive)
  config.set('source_folder', '/path/to/directory')
  config.set('recursive', True)  # Optional, defaults to True
  ```

- **Catalogue-based loading**:
  ```python
  # Load pre-defined list of files from JSON
  config.set('catalogue', '/path/to/catalogue.json')
  ```

### 2. Comprehensive Filtering System

```mermaid
flowchart LR
    FILE[File] --> COMP{Composite Filter}
    
    subgraph Filters
    COMP --> EXT{Extension Filter}
    COMP --> PAT{Pattern Filter}
    COMP --> SIZE{Size Filter}
    COMP --> DATE{Date Filter}
    end
    
    EXT -->|No| REJECT([Reject])
    PAT -->|No| REJECT
    SIZE -->|No| REJECT
    DATE -->|No| REJECT
    
    EXT -->|Yes| PASS1[Pass]
    PAT -->|Yes| PASS2[Pass]
    SIZE -->|Yes| PASS3[Pass]
    DATE -->|Yes| PASS4[Pass]
    
    PASS1 --> COMP2{All Passed?}
    PASS2 --> COMP2
    PASS3 --> COMP2
    PASS4 --> COMP2
    
    COMP2 -->|Yes| ACCEPT([Accept])
    COMP2 -->|No| REJECT
    
    style REJECT fill:#f96,stroke:#333,stroke-width:1px;
    style ACCEPT fill:#6f6,stroke:#333,stroke-width:1px;
```

Files can be filtered based on various criteria:

- **Extension filtering**:
  ```python
  # Built-in support for common document formats
  # .txt, .md, .pdf, .docx, .doc, .html, .htm, .xml, .json
  ```

- **Pattern matching**:
  ```python
  # Glob pattern (default)
  config.set('pattern', '*.md')
  
  # Regular expression
  config.set('pattern', '^README.*\.md$')
  config.set('use_regex', True)
  ```$')
  config.set('use_regex', True)
  ```

- **Size filtering**:
  ```python
  # Limit by file size
  config.set('min_size', 1024)  # Minimum 1KB
  config.set('max_size', 1024*1024)  # Maximum 1MB
  ```

- **Date filtering**:
  ```python
  # Filter by modification date
  config.set('min_date', 1609459200)  # After Jan 1, 2021
  config.set('max_date', 1640995199)  # Before Dec 31, 2021
  ```

All filters can be combined through the `CompositeFilter` which implements logical AND semantics.

### 3. Flexible Sorting Options

```mermaid
flowchart TD
    FILES([Files]) --> SORT{Sort Type?}
    SORT -->|Name| NAME[Sort by Name]
    SORT -->|Date| DATE[Sort by Date]
    SORT -->|Size| SIZE[Sort by Size]
    SORT -->|Random| RANDOM[Random Order]
    
    NAME --> ORDER_N{Direction?}
    DATE --> ORDER_D{Direction?}
    SIZE --> ORDER_S{Direction?}
    
    ORDER_N -->|Ascending| NAME_ASC[A to Z]
    ORDER_N -->|Descending| NAME_DESC[Z to A]
    
    ORDER_D -->|Ascending| DATE_ASC[Oldest First]
    ORDER_D -->|Descending| DATE_DESC[Newest First]
    
    ORDER_S -->|Ascending| SIZE_ASC[Smallest First]
    ORDER_S -->|Descending| SIZE_DESC[Largest First]
    
    NAME_ASC --> SORTED([Sorted Files])
    NAME_DESC --> SORTED
    DATE_ASC --> SORTED
    DATE_DESC --> SORTED
    SIZE_ASC --> SORTED
    SIZE_DESC --> SORTED
    RANDOM --> SORTED
```

Files can be sorted in various ways:

```python
# Sort by name (default)
config.set('sort_by', 'name')

# Sort by modification date (newest first)
config.set('sort_by', 'date')
config.set('sort_desc', True)

# Sort by size (smallest first)
config.set('sort_by', 'size')

# Random order
config.set('random', True)
```

### 4. Recursive Directory Control

Fine-grained control over directory traversal:

```python
# Enable/disable recursion
config.set('recursive', True)  # Default is True

# Limit recursion depth
config.set('max_depth', 3)  # Go no deeper than 3 levels

# Control hidden file inclusion
config.set('include_hidden', True)  # Include .hidden files and directories
```

### 5. Result Limiting

Control the number of files returned:

```python
# Limit to the first N files after filtering and sorting
config.set('limit', 100)
```

### 6. Lazy Loading and Memory Efficiency

The `FileIterator` uses lazy loading to optimize memory usage:

- Files are discovered only when `load()` is called
- Iteration through `__iter__()` and `__next__()` loads files on-demand
- `reset()` allows reuse of the iterator without creating a new instance

### 7. Catalogue Generation

Create JSON catalogues for later reuse:

```python
# Create a catalogue builder
builder = CatalogueBuilder("catalogue.json")

# Add files from an iterator
builder.add_files(file_iterator)

# Save to file
builder.save()
```

Catalogue format:
```json
{
  "files": [
    {
      "path": "/absolute/path/to/file.md",
      "size": 1024,
      "modified": 1635724800,
      "extension": ".md"
    },
    // Additional files...
  ]
}
```

## CLI Integration

```mermaid
graph TD
    USER([User]) --> CLI[DocIndexer CLI]
    CLI --> LIST[list command]
    CLI --> INDEX[index command]
    CLI --> CONFIG[config command]
    CLI --> SCHEMA[schema command]
    
    subgraph "FileIterator Integration"
    LIST --> ITERATOR[FileIterator]
    INDEX --> INDEXER[DocIndexer]
    INDEXER --> ITERATOR
    end
    
    ITERATOR --> DISCOVERY[File Discovery]
    ITERATOR --> FILTERING[File Filtering]
    ITERATOR --> SORTING[File Sorting]
    
    DISCOVERY --> FS[(Filesystem)]
    
    LIST --> DISPLAY[Display Results]
    INDEX --> SAVE[Save Index]
    
    style CLI fill:#f96,stroke:#333,stroke-width:2px;
    style ITERATOR fill:#bbf,stroke:#333,stroke-width:2px;
    style LIST,INDEX fill:#bfb,stroke:#333,stroke-width:1px;
```

The FileIterator functionality is exposed through the DocIndexer CLI:

### 1. List Command

List files matching specific criteria:

```bash
# Basic listing
docindexer list --source-folder /path/to/docs

# Pattern matching with sorting
docindexer list --source-folder /path/to/docs --pattern "*.md" --sort-by date --desc

# Recursive control and limiting
docindexer list --source-folder /path/to/docs --no-recursive
docindexer list --source-folder /path/to/docs --max-depth 2 --limit 50

# Include hidden files/folders
docindexer list --source-folder /path/to/docs --include-hidden

# Random order
docindexer list --source-folder /path/to/docs --random
```

### 2. Index Command

Index documents in a specified path (uses FileIterator internally):

```bash
# Basic indexing
docindexer index /path/to/docs --output index.json

# Control recursion
docindexer index /path/to/docs --recursive --output index.json
```

## Common Usage Patterns

### 1. Basic Iteration

```python
from docindexer.config import Configuration
from docindexer.file_iterator import FileIterator

# Create configuration
config = Configuration()
config.set('source_folder', '/path/to/docs')
config.set('pattern', '*.md')

# Create iterator
iterator = FileIterator(config)

# Process files
for file_info in iterator:
    print(f"Processing {file_info.name} ({file_info.size} bytes)")
    # Process file...
```

### 2. Get All Files at Once

```python
# Create and configure iterator
iterator = FileIterator(config)

# Get all files as a list
all_files = iterator.get_files()

# Get count
file_count = len(iterator)  # or iterator.count()
```

### 3. Create a Catalogue for Later Use

```python
from docindexer.file_iterator import FileIterator, CatalogueBuilder

# Create and configure iterator
iterator = FileIterator(config)

# Create and save catalogue
builder = CatalogueBuilder('docs_catalogue.json')
builder.add_files(iterator)
builder.save()

# Later use the catalogue
config.set('catalogue', 'docs_catalogue.json')
catalogue_iterator = FileIterator(config)
```

## Design Principles and Best Practices

```mermaid
graph LR
    SOLID[SOLID Principles] --> SRP[Single Responsibility]
    SOLID --> OCP[Open-Closed]
    SOLID --> LSP[Liskov Substitution]
    SOLID --> ISP[Interface Segregation]
    SOLID --> DIP[Dependency Inversion]
    
    PATTERNS[Design Patterns] --> STRAT[Strategy Pattern]
    PATTERNS --> COMP[Composite Pattern]
    PATTERNS --> ITER[Iterator Pattern]
    PATTERNS --> FACT[Factory Method]
    
    PRACTICES[Best Practices] --> LAZY[Lazy Evaluation]
    PRACTICES --> CONFIG[Configuration-Driven]
    PRACTICES --> COMP_OVER[Composition Over Inheritance]
    
    SRP --> CLASS[Each class has\nsingle focus]
    OCP --> EXTEND[Adding filters\nwithout changing code]
    
    STRAT --> FILTER[FileFilter hierarchy]
    COMP --> COMPOSITE[CompositeFilter]
    ITER --> PROTOCOL[Python iterator\nprotocol]
    FACT --> FACTORY[FileInfo.from_path]
    
    LAZY --> LOAD[Load files\nonly when needed]
    CONFIG --> CENTRALIZED[Central config object]
    COMP_OVER --> BUILD[Build complex behavior\nfrom simple components]
    
    style SOLID fill:#f96,stroke:#333,stroke-width:2px;
    style PATTERNS fill:#bbf,stroke:#333,stroke-width:2px;
    style PRACTICES fill:#bfb,stroke:#333,stroke-width:2px;
```

The `FileIterator` and supporting classes follow several important design principles:

1. **Single Responsibility Principle**: Each class has a focused purpose
2. **Open-Closed Principle**: New filters can be added without modifying existing code
3. **Composition over Inheritance**: Complex behavior built through composing simpler components
4. **Lazy Evaluation**: Files are discovered only when needed
5. **Configuration-Driven**: Behavior controlled through a central Configuration object
6. **Iterator Pattern**: Standard Python iteration protocol support

## Performance Considerations

- **Lazy Loading**: Files are only discovered when needed
- **Filtering Early**: Filters are applied during discovery to avoid loading unnecessary files
- **Catalogue Support**: Pre-scanned file lists can be saved for faster reuse
- **Memory Efficiency**: Files are processed one at a time during iteration

## Use Cases

```mermaid
mindmap
  root((FileIterator<br>Use Cases))
    Document Processing
      ::icon(fa fa-file-text)
      Find markdown files
      Order by modification
      Generate HTML outputs
    Data Management
      ::icon(fa fa-database)
      Locate data files
      Filter by patterns
      Sort by size
      Transform & analyze
    Media Organization
      ::icon(fa fa-image)
      Find media files
      Filter by size/date
      Organize & backup
    Log Analysis
      ::icon(fa fa-list)
      Find logs in date range
      Process chronologically
      Extract statistics
    Content Indexing
      ::icon(fa fa-search)
      Discover content files
      Filter by document type
      Index for search
```

1. **Document Processing Pipeline**:
   - Find all markdown files in a documentation directory
   - Process them in order of last modification
   - Generate HTML or other output formats

2. **Data File Management**:
   - Locate CSV or JSON data files matching specific patterns
   - Sort by size to process smaller files first
   - Apply transformations or analysis

3. **Media File Organization**:
   - Find image or audio files with specific patterns
   - Filter by size or date to identify recent or large files
   - Process for backup or organization

4. **Log Analysis**:
   - Locate log files within date ranges
   - Process in chronological order
   - Extract relevant information or statistics

5. **Content Indexing**:
   - Discover content files across a directory structure
   - Filter by relevant document types
   - Index contents for search or analysis

## Conclusion

The `FileIterator` provides a flexible, efficient foundation for file discovery and processing in the DocIndexer application. Its modular design, powerful filtering capabilities, and adherence to Python best practices make it a versatile tool for a wide range of file processing tasks.

By leveraging the configuration system, users can customize file discovery behavior through the command line or configuration files, while developers can extend the system with new filtering strategies and processing capabilities.