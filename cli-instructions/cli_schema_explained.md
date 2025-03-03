# Command-Line Interface Schema Explanation

This document explains the structure of the `cli_schema.json` file and how it can be used to describe command-line interfaces.

## Overview

The CLI schema is a JSON-based representation that describes the structure, commands, options, and configuration sources of a command-line interface. It follows a hierarchical structure that allows for easy understanding, validation, and code generation.

## Schema Structure

The CLI schema has the following top-level elements:

```
{
  "name": "...",
  "description": "...",
  "version": "...",
  "globalOptions": [...],
  "commonOptions": [...],
  "commands": [...],
  "configurationSources": [...]
}
```

### Core Elements

- **name**: The name of the command-line tool.
- **description**: A brief description of what the tool does.
- **version**: The version of the tool.

### Options

Options are parameters that can be passed to commands. They are represented as objects with properties:

```json
{
  "name": "option_name",
  "description": "Description of the option",
  "type": "string|integer|boolean|float|array",
  "flag": "--flag-name",
  "default": "default value",
  "required": true|false,
  "notes": "Additional notes about the option"
}
```

- **globalOptions**: Options that apply to the entire application, regardless of command.
- **commonOptions**: Options that are shared across multiple commands.

### Commands

Commands are the main actions that can be performed by the tool:

```json
{
  "name": "command_name",
  "description": "Description of the command",
  "options": [...],
  "inheritsCommonOptions": true|false,
  "requiredOptions": [...]
}
```

Each command can have its own options, and can also inherit common options.

### Configuration Sources

Configuration sources define where the tool can read its configuration from, in order of priority:

```json
{
  "name": "Source name",
  "priority": 1,
  "path": "path/to/config",
  "description": "Description of this configuration source"
}
```

## How to Use This Schema

### Documentation Generation

You can use this schema to generate:
- Command-line help text
- Man pages
- Markdown documentation
- Web-based documentation

### Input Validation

The schema can be used to validate user input before processing:
- Ensure required options are provided
- Validate option types (string, integer, etc.)
- Check for invalid combinations of options

### Code Generation

You can generate code for argument parsing based on this schema:
- Generate argument parser configuration
- Create option validation logic
- Build help text generators

### Configuration Management

The schema describes how configuration is loaded from multiple sources:
- Command-line arguments (highest priority)
- Local configuration files
- Global configuration files
- Environment variables

## Extending the Schema

The schema is designed to be easily extensible:

1. **New Commands**: Add new objects to the `commands` array.
2. **New Options**: Add new option objects to command-specific options or common options.
3. **New Configuration Sources**: Add new sources to the `configurationSources` array.
4. **Additional Properties**: The schema can be extended with additional properties as needed.

## Implementation Libraries and Tools

Here are some libraries and tools that can be used to implement CLI schemas:

### Python

1. **argparse**: Standard library module for command-line parsing
   - Supports commands, options, help generation
   - Can be configured programmatically based on the schema

2. **click**: Modern command-line tool for creating beautiful CLI applications
   - Decorator-based interface
   - Rich support for commands, options, arguments
   - Built-in help generation
   - Supports composition of commands and option groups
   - Excellent for implementing nested command structures
   - Integrates well with Rich for terminal formatting

3. **typer**: Built on top of Click, adds type hints support
   - Modern, type-hint based CLI builder
   - Automatic help text and tab completion
   - Simplified API compared to Click

4. **docopt**: Creates command-line interfaces from docstrings
   - Parses POSIX-style usage patterns

5. **ConfigArgParse**: Extension of argparse that adds support for config files and environment variables
   - Ideal for implementing the multi-source configuration described in the schema

6. **Rich**: Library for rich text and beautiful formatting in the terminal
   - Not a CLI parser but enhances CLIs with:
     - Colorful, formatted output with syntax highlighting
     - Tables, progress bars, and other UI elements
     - Markdown rendering in the terminal
     - Tree visualization for hierarchical data
     - Integrates well with Click, Typer, and argparse

### JavaScript/Node.js

1. **commander.js**: Complete solution for Node.js command-line interfaces
   - Fluent API for defining commands and options
   - Automatic help generation

2. **yargs**: Feature-rich command-line parser
   - Configuration-based approach
   - Supports commands, options, and environment variables

3. **oclif**: Open CLI Framework by Heroku
   - Rich framework for building complex CLIs
   - Support for plugins, hooks, and testing

### Rust

1. **clap**: Command Line Argument Parser for Rust
   - Comprehensive option and command support
   - Supports generation from YAML/TOML configuration

2. **structopt**: Parse command line arguments by defining a struct
   - Built on top of clap
   - Uses Rust's type system and derives

### Go

1. **cobra**: A Commander for modern Go CLI applications
   - Command definition
   - Shell completions
   - Man page generation

2. **urfave/cli**: Simple, fast, and fun package for building command-line apps in Go
   - Subcommands, flags, help text generation

### Multi-Language Tools

1. **JSON Schema**: Define a JSON Schema for CLI configurations
   - Validate CLI configurations against a schema
   - Generate documentation from schema

2. **OpenAPI/Swagger**: While primarily for REST APIs, can be adapted for CLI definition
   - Strong tooling ecosystem
   - Code generation capabilities

## Implementation Example with Click and Rich

Here's how you might implement this schema using Python's Click library and Rich for beautiful terminal output:

```python
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint

# Initialize Rich console
console = Console()

# Load CLI schema
with open('cli_schema.json', 'r') as f:
    schema = json.load(f)

# Configuration context to share between commands
class Config:
    def __init__(self):
        self.global_config = {}
        self.local_config = {}
        self.debug = False

# Pass the Config object to all commands
pass_config = click.make_pass_decorator(Config, ensure=True)

def add_common_options(command_func):
    """Decorator to add common options to a command based on schema."""
    for option in reversed(schema.get('commonOptions', [])):
        param_args = (option['flag'],)
        param_kwargs = {
            'help': option['description'],
            'required': option.get('required', False),
        }
        
        # Handle different option types
        if option['type'] == 'boolean':
            param_kwargs['is_flag'] = True
        elif option['type'] == 'integer':
            param_kwargs['type'] = int
        elif option['type'] == 'float':
            param_kwargs['type'] = float
        elif option['type'] == 'array':
            param_kwargs['multiple'] = True
        
        # Add default value if specified
        if 'default' in option:
            param_kwargs['default'] = option['default']
            
        command_func = click.option(*param_args, **param_kwargs)(command_func)
    
    return command_func

# Create main CLI group
@click.group(help=schema['description'])
@click.version_option(schema['version'])
@click.option('--readme', is_flag=True, help='Display README and exit')
@click.pass_context
def cli(ctx, readme):
    """Main CLI entry point."""
    ctx.obj = Config()
    
    if readme:
        readme_path = Path.cwd() / "README.md"
        try:
            with open(readme_path, 'r') as f:
                # Use Rich to render the markdown
                md = Markdown(f.read())
                console.print(md)
                ctx.exit()
        except FileNotFoundError:
            console.print("[bold red]README.md not found![/bold red]")
            ctx.exit(1)

# Build commands from schema
for cmd_schema in schema.get('commands', []):
    cmd_name = cmd_schema['name']
    cmd_help = cmd_schema['description']
    
    # Create command function with appropriate name
    cmd_code = f"""
@cli.command('{cmd_name}', help='{cmd_help}')
@pass_config
"""
    
    # Add command-specific options
    for option in cmd_schema.get('options', []):
        param_args = f"'{option['flag']}'"
        param_kwargs = {}
        
        param_kwargs['help'] = f"'{option['description']}'"
        param_kwargs['required'] = option.get('required', False)
        
        # Handle different option types
        if option['type'] == 'boolean':
            param_kwargs['is_flag'] = True
        elif option['type'] == 'integer':
            param_kwargs['type'] = 'int'
        elif option['type'] == 'float':
            param_kwargs['type'] = 'float'
        elif option['type'] == 'array':
            param_kwargs['multiple'] = True
        
        # Add default if specified
        if 'default' in option:
            param_kwargs['default'] = f"'{option['default']}'" if isinstance(option['default'], str) else option['default']
            
        # Generate the option decorator
        kwargs_str = ', '.join(f"{k}={v}" for k, v in param_kwargs.items())
        cmd_code += f"@click.option({param_args}, {kwargs_str})\n"
    
    # Add common options if specified
    if cmd_schema.get('inheritsCommonOptions', False):
        cmd_code += "@add_common_options\n"
    
    # Add the command arguments
    arg_list = []
    required_options = cmd_schema.get('requiredOptions', [])
    
    for option in cmd_schema.get('options', []):
        snake_case = option['name'].replace('-', '_')
        arg_list.append(snake_case)
    
    if cmd_schema.get('inheritsCommonOptions', False):
        for option in schema.get('commonOptions', []):
            snake_case = option['name']
            arg_list.append(snake_case)
    
    args_str = ', '.join(arg_list)
    
    # Create the function body
    cmd_code += f"""
def {cmd_name}_cmd(config, {args_str}):
    \"\"\"Execute the {cmd_name} command.\"\"\"
    # Load config from files
    load_config(config)
    
    # Set debug mode
    if debug:
        config.debug = True
        console.print(f"[bold blue]Running in debug mode - displaying extended information[/bold blue]")
    
    # Check required parameters
    missing = check_required_params([{', '.join(f"'{param}'" for param in required_options)}], locals())
    if missing:
        console.print(f"[bold red]Missing required parameters: {{', '.join(missing)}}[/bold red]")
        return 1
        
    # Command implementation
    console.print(f"[bold green]Executing {cmd_name} command...[/bold green]")
    
    # Create a Rich table to display the options
    table = Table(title=f"{cmd_name.capitalize()} Command Options")
    table.add_column("Option", style="cyan")
    table.add_column("Value", style="green")
    
    for param, value in locals().items():
        if param not in ['config', 'check_required_params', 'load_config'] and not param.startswith('_'):
            table.add_row(param, str(value))
    
    console.print(table)
    
    # Real implementation would go here...
    return 0
"""
    
    # Add the command function to the global namespace
    exec(cmd_code)

def load_config(config):
    """Load configuration from different sources according to priority."""
    # 1. Load global config
    global_config_path = Path.home() / ".vectorizer" / "config.json"
    if global_config_path.exists():
        try:
            with open(global_config_path, 'r') as f:
                config.global_config = json.load(f)
        except json.JSONDecodeError:
            console.print(f"[bold yellow]Warning: Invalid JSON in global config file[/bold yellow]")
    
    # 2. Load local config (overrides global)
    local_config_path = Path.cwd() / "config.json"
    if local_config_path.exists():
        try:
            with open(local_config_path, 'r') as f:
                config.local_config = json.load(f)
        except json.JSONDecodeError:
            console.print(f"[bold yellow]Warning: Invalid JSON in local config file[/bold yellow]")

def check_required_params(required: List[str], params: Dict[str, Any]) -> List[str]:
    """Check if all required parameters are present and have values."""
    missing = []
    for param in required:
        if param not in params or params[param] is None:
            missing.append(param)
    return missing

@cli.command('config', help='Display current configuration settings')
@click.option('--source', type=click.Choice(['all', 'global', 'local', 'effective']), 
              default='effective', help='Which configuration source to display')
@pass_config
def show_config(config, source):
    """Show the current configuration from different sources."""
    load_config(config)
    
    if source in ['all', 'global'] and config.global_config:
        console.print(Panel.fit(
            json.dumps(config.global_config, indent=2),
            title="Global Configuration (~/.vectorizer/config.json)",
            border_style="blue"
        ))
    
    if source in ['all', 'local'] and config.local_config:
        console.print(Panel.fit(
            json.dumps(config.local_config, indent=2),
            title="Local Configuration (./config.json)",
            border_style="green"
        ))
    
    if source in ['all', 'effective']:
        # Combine configs according to priority
        effective = config.global_config.copy()
        effective.update(config.local_config)
        
        console.print(Panel.fit(
            json.dumps(effective, indent=2),
            title="Effective Configuration",
            border_style="yellow"
        ))

def visualize_schema():
    """Visualize the CLI schema structure."""
    tree = Tree(f"[bold magenta]{schema['name']} CLI[/bold magenta]")
    
    # Add global options
    global_branch = tree.add("[bold blue]Global Options[/bold blue]")
    for option in schema.get('globalOptions', []):
        global_branch.add(f"[cyan]{option['flag']}[/cyan]: {option['description']}")
    
    # Add commands
    commands_branch = tree.add("[bold green]Commands[/bold green]")
    for command in schema.get('commands', []):
        cmd_branch = commands_branch.add(f"[yellow]{command['name']}[/yellow]: {command['description']}")
        
        # Add command options
        for option in command.get('options', []):
            required = "[bold red]*[/bold red] " if option.get('required', False) else ""
            cmd_branch.add(f"{required}[cyan]{option['flag']}[/cyan]: {option['description']}")
    
    # Add common options
    common_branch = tree.add("[bold blue]Common Options[/bold blue]")
    for option in schema.get('commonOptions', []):
        required = "[bold red]*[/bold red] " if option.get('required', False) else ""
        common_branch.add(f"{required}[cyan]{option['flag']}[/cyan]: {option['description']}")
    
    console.print(tree)

@cli.command('schema', help='Visualize CLI schema structure')
def schema_cmd():
    """Visualize the CLI schema structure."""
    visualize_schema()
    return 0

if __name__ == "__main__":
    sys.exit(cli())
```

This implementation demonstrates several advanced features:

1. **Dynamic Command Generation**: Commands are generated dynamically from the schema
2. **Rich Text Formatting**: All output uses Rich for beautiful terminal display
3. **Configuration Management**: Loads config from multiple sources with proper priority
4. **Schema Visualization**: Includes a command to visualize the CLI structure
5. **Validation**: Validates required parameters before command execution

## Creating Visually Appealing CLIs with Rich

The [Rich](https://github.com/Textualize/rich) library for Python provides a powerful set of tools for creating beautiful terminal output. When combined with a CLI framework like Click, it can transform a standard command-line tool into a visually stunning application.

### Key Rich Features for CLI Development

1. **Rich Console**: The core interface for all Rich output
   ```python
   from rich.console import Console
   console = Console()
   console.print("[bold red]Error:[/bold red] File not found")
   ```

2. **Syntax Highlighting**: Display code with proper syntax highlighting
   ```python
   from rich.syntax import Syntax
   syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
   console.print(syntax)
   ```

3. **Markdown Rendering**: Display markdown documents directly in the terminal
   ```python
   from rich.markdown import Markdown
   with open("README.md") as f:
       markdown = Markdown(f.read())
   console.print(markdown)
   ```

4. **Tables**: Display tabular data with styles and formatting
   ```python
   from rich.table import Table
   table = Table(title="Command Options")
   table.add_column("Option", style="cyan")
   table.add_column("Value", style="green")
   table.add_row("--output", "/path/to/output")
   console.print(table)
   ```

5. **Panels**: Create boxed content with borders and titles
   ```python
   from rich.panel import Panel
   console.print(Panel("Success! Your command has completed.", title="Status", border_style="green"))
   ```

6. **Progress Bars**: Display progress for long-running operations
   ```python
   from rich.progress import Progress
   with Progress() as progress:
       task = progress.add_task("[cyan]Processing...", total=100)
       for i in range(100):
           # Do work
           progress.update(task, advance=1)
   ```

7. **Trees**: Visualize hierarchical data structures
   ```python
   from rich.tree import Tree
   tree = Tree("Project Root")
   src = tree.add("src")
   src.add("main.py")
   src.add("utils.py")
   tests = tree.add("tests")
   tests.add("test_main.py")
   console.print(tree)
   ```

8. **Live Display**: Update a display while a process is running
   ```python
   from rich.live import Live
   with Live(table, refresh_per_second=4) as live:
       for i in range(10):
           # Update table
           table.add_row(f"Row {i}", f"Value {i}")
           time.sleep(0.5)
   ```

### Integrating Rich with Click

Rich can be seamlessly integrated with Click to enhance the user experience:

1. **Command Output**: Use Rich to format command output with colors and styles
2. **Help Text**: Enhance the display of help text with Rich formatting
3. **Error Messages**: Make error messages stand out with colors and formatting
4. **Progress Feedback**: Show progress for long-running commands
5. **Data Visualization**: Display structured data like JSON, tables, and trees

### Design Principles for Rich CLIs

1. **Consistency**: Use a consistent color scheme throughout your application
2. **Clarity**: Use formatting to highlight the most important information
3. **Hierarchy**: Use visual hierarchy to organize information
4. **Feedback**: Provide clear feedback during long-running operations
5. **Accessibility**: Ensure your color choices work for color-blind users

### Sample Rich Components for CLI Applications

```python
def generate_help_text():
    """Generate a rich help text display."""
    console = Console()
    
    # Create a panel for the main description
    console.print(Panel(
        "[bold]vectorizer[/bold] - Process markdown files: split into chunks, vectorize, or organize them",
        title="Command Overview",
        border_style="blue"
    ))
    
    # Create a table for commands
    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    
    table.add_row("split", "Split markdown files into chunks")
    table.add_row("vectorize", "Split and vectorize markdown files")
    table.add_row("organize", "Create a hierarchical JSON representation of markdown structure")
    
    console.print(table)
    
    # Show common options
    options_md = """
    ## Common Options

    * `--catalogue` - Path to the catalogue JSON file
    * `--folder` - Path to the folder containing markdown files
    * `--chunk-size` - Target size of each chunk in characters
    * `--count` - Number of files to process
    """
    
    console.print(Markdown(options_md))
    
    # Show configuration sources
    console.print(Panel(
        "Configuration is loaded from the following sources in order of priority:\n"
        "1. Command-line arguments\n"
        "2. Local config.json file\n"
        "3. Global ~/.vectorizer/config.json file",
        title="Configuration",
        border_style="green"
    ))
```

By combining Rich's visual elements with Click's command and option handling, you can create command-line applications that are not only powerful but also visually engaging and user-friendly.

## Conclusion

The CLI schema described here provides a flexible, extensible way to define command-line interfaces. It separates the interface definition from the implementation, allowing for better documentation, validation, and code generation. When implemented with modern libraries like Click for command processing and Rich for visual presentation, it creates a powerful and user-friendly command-line experience.

By using this schema, you can ensure consistency across your application's interface, simplify maintenance, and improve user experience through better help text and error messages.