# DocIndexer Commands

## Setup Commands
```bash
# Create virtual environment using UV
uv venv --python=3.12

# Activate virtual environment
. .venv/bin/activate  # Unix/macOS
# .venv\Scripts\activate  # Windows

# Install package in development mode
uv pip install -e .
```

## Usage Examples
```bash
# Get help
docindexer --help

# Index documents in a directory
docindexer index /path/to/directory

# Index recursively with output file
docindexer index /path/to/directory --recursive --output index.json
```