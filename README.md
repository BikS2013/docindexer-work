# DocIndexer

A command line tool for processing and indexing documents to prepare them for vectorization and searching.

## Installation

```bash
# Install from PyPI
pip install docindexer

# For development
git clone https://github.com/yourusername/docindexer.git
cd docindexer
```

## Development Setup

This project uses UV for package management with Python 3.12.

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
uv pip install -e .
```

## Usage

### Basic Commands

```bash
# Show help
docindexer --help

# Index documents in a directory
docindexer index /path/to/documents

# Index recursively
docindexer index /path/to/documents --recursive

# Output to a specific file
docindexer index /path/to/documents --output index.json

# Display configuration
docindexer config

# Show CLI schema structure
docindexer schema
```

### Creating Configuration Files

```bash
# Create a local configuration file
docindexer index /path/to/documents --create-local-config

# Create a global configuration file
docindexer index /path/to/documents --create-global-config

# Create config without running the command
docindexer index /path/to/documents --create-local-config --run-after-config-create=false
```

## CLI Schema Validation and Configuration Management

DocIndexer includes a robust CLI schema validation and configuration management system that:

1. Validates command-line arguments against the definitions in `cli_schema.json`
2. Manages configurations from multiple sources with proper precedence
3. Provides a flexible way to extend the CLI with new commands and options

### Architecture

The system consists of three main components:

1. **SchemaValidator**: Validates arguments against a JSON schema
2. **Configuration**: Manages configuration from multiple sources
3. **CLI Interface**: Implements the command-line interface using Click

### Extending the System

#### Adding a New Command

1. Edit `cli_schema.json` to add your new command:

```json
{
  "commands": [
    {
      "name": "your_command",
      "description": "Description of your command",
      "options": [
        {
          "name": "your_option",
          "description": "Description of your option",
          "type": "string",
          "flag": "--your-option",
          "required": false
        }
      ],
      "inheritsCommonOptions": true,
      "requiredOptions": []
    }
  ]
}
```

2. Add the implementation in `cli.py`:

```python
@main.command()
@click.option('--your-option', help='Description of your option')
@click.pass_context
def your_command(ctx, your_option):
    """Description of your command."""
    args = {
        'command': 'your_command',
        'your_option': your_option
    }
    
    try:
        # Validate and apply configuration
        effective_config = validate_and_apply_config('your_command', args)
        
        # Command implementation
        # ...
    
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        return 1
    
    return 0
```

#### Adding a New Option

1. To add a new option to an existing command, add it to the command's `options` array in `cli_schema.json`
2. To add a common option, add it to the `commonOptions` array
3. Update the command implementation in `cli.py` to use the new option

### Testing

The system includes a comprehensive test suite:

- Unit tests for the SchemaValidator and Configuration classes
- Integration tests using a test scenario JSON file
- An automated test runner that verifies all scenarios

Run the tests:

```bash
# Run unit tests
python -m unittest discover -s tests

# Run test scenarios
python tests/test_runner.py
```

## Configuration Precedence

DocIndexer follows this precedence for configuration settings:

1. Command-line arguments (highest priority)
2. Local configuration file (`./config.json`)
3. Global configuration file (`~/.docindexer/config.json`)