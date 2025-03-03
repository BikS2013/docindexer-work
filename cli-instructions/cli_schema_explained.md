# Command-Line Interface Schema Explanation

This document explains the structure and usage of the `cli_schema.json` file for the DocIndexer CLI tool.

## Overview

The `cli_schema.json` file defines the structure, commands, options, and configuration sources for the DocIndexer command-line interface. It follows a JSON-based hierarchical structure that facilitates documentation, validation, and implementation.

## Schema Structure

The schema has the following top-level elements:

```json
{
  "name": "docindexer",
  "description": "Process files to prepare them for vectorization and indexing",
  "version": "1.0.0",
  "globalOptions": [...],
  "commonOptions": [...],
  "commands": [...],
  "configurationSources": [...]
}
```

### Core Elements

- **name**: The command-line tool's name
- **description**: A brief description of the tool's purpose
- **version**: The current version of the tool

### Options

The schema defines options that can be passed to commands. Each option is represented as an object with the following properties:

```json
{
  "name": "option_name",
  "description": "Description of what the option does",
  "type": "string|integer|boolean|float|array",
  "flag": "--flag-name",
  "alternative-flag": "-f",
  "required": true|false,
  "default-value": "default value",
  "mutually-exclusive-with": ["other_option"],
  "requires": ["dependent_option"]
}
```

Key option properties:

- **name**: Unique identifier for the option
- **description**: Human-readable description
- **type**: Data type (string, integer, boolean, float, array)
- **flag**: Main flag for the option (e.g., "--output-folder")
- **alternative-flag**: Short form flag (e.g., "-o")
- **required**: Whether the option is mandatory
- **default-value**: Value used when the option is not specified
- **mutually-exclusive-with**: List of options that cannot be used together with this option
- **requires**: List of options that must be present when this option is used

Options are categorized into:

- **globalOptions**: Apply to the entire application regardless of command
- **commonOptions**: Shared across multiple commands

### Commands

Commands represent the main actions of the tool:

```json
{
  "name": "command_name",
  "description": "Description of what the command does",
  "options": [...],
  "inheritsCommonOptions": true|false,
  "requiredOptions": [...]
}
```

Key command properties:

- **name**: Command identifier used in the CLI
- **description**: Human-readable description
- **options**: Command-specific options
- **inheritsCommonOptions**: Whether this command uses the common options
- **requiredOptions**: Options that must be provided for this command

The `requiredOptions` array can contain either simple strings (for individual required options) or arrays of strings (for "one of these" requirements).

### Configuration Sources

Configuration sources define where the tool reads configuration from, in priority order:

```json
{
  "name": "Source name",
  "priority": 1,
  "path": "path/to/config",
  "description": "Description of this configuration source"
}
```

Key configuration source properties:

- **name**: Identifier for the configuration source
- **priority**: Numeric priority (lower number = higher priority)
- **path**: File path for config file sources
- **description**: Human-readable description

## DocIndexer Schema Elements

### Global Options

The DocIndexer tool defines the following global options:

- **--readme**: Display README and exit

### Common Options

Common options shared across DocIndexer commands include:

- **--source-folder, -s**: Path to the folder containing files to be processed
- **--catalogue, -c**: Path to a catalogue JSON file
- **--file-name, -n**: Name of a specific file to process
- **--recursive, -R**: Process files in subfolders recursively
- **--limit, -l**: Limit the number of files to be processed
- **--random, -r**: Process files in random order
- **--output-folder, -o**: Path to save processed files
- **--create-local-config**: Create a local config.json file
- **--create-global-config**: Create a global config.json file
- **--run-after-config-create**: Run the command after creating config file(s)
- **--show-config**: Show effective configuration and exit
- **--debug**: Enable debug mode with additional logging
- **--dry-run**: Perform a dry run without saving any files

### Commands

The DocIndexer tool defines the following commands:

#### structure

Creates a hierarchical JSON representation of markdown structure.

Options:
- **--ommit-properties**: Comma-separated list of properties to omit from the JSON output

Required options:
- At least one of: `catalogue`, `source_folder`, or `file_name`
- `output_folder`

### Configuration Sources

The DocIndexer tool uses the following configuration sources in order of priority:

1. **Command-line arguments** (highest priority)
2. **Local config file** (`./config.json`)
3. **Global config file** (`~/.vectorizer/config.json`)

## Using the Schema

### Input Validation

The schema provides a clear way to validate user input:

- Ensuring required options are provided
- Validating option types (string, integer, etc.)
- Checking for invalid combinations of options
- Verifying mutual exclusivity constraints
- Enforcing option dependencies

### Configuration Management

The schema describes the configuration system with:

- Multiple configuration sources with priority
- Local and global configuration files
- Command-line arguments overriding saved configurations

### Implementation

The schema serves as the foundation for:

1. **Command-line parsing**: Validating and processing user input
2. **Configuration management**: Loading, merging, and prioritizing settings
3. **Help system**: Generating comprehensive help text
4. **Error messages**: Providing clear feedback on validation failures

## Extending the Schema

The schema is designed to be extended as the DocIndexer tool evolves:

1. **New Commands**: Add new objects to the `commands` array
2. **New Options**: Add options to command-specific options or common options
3. **New Configuration Sources**: Add sources to the `configurationSources` array

## Implementation Architecture

The DocIndexer CLI implementation uses the following components:

### SchemaValidator Class

Validates command-line arguments against the schema:
- Loads and parses the schema definition
- Validates command arguments against schema options
- Checks required options, mutual exclusivity, and dependencies
- Normalizes arguments to a consistent format
- Applies default values from the schema

### Configuration Class

Manages configuration from multiple sources:
- Loads settings from global and local config files
- Merges configuration sources in order of priority
- Provides access to the effective configuration
- Creates and saves configuration files

### CLI Implementation

Connects the schema and configuration system to the UI:
- Defines commands and options using Click
- Validates user input against the schema
- Applies configuration from all sources
- Displays help text and error messages
- Executes commands with validated configuration

## Best Practices

When working with the CLI schema:

1. **Single Responsibility**: Each component should handle one aspect of the system
2. **Clear Validation**: Provide informative error messages for validation failures
3. **Configuration Precedence**: Always respect the priority order of configuration sources
4. **Default Values**: Provide sensible defaults to minimize required user input
5. **Type Safety**: Validate option values against their declared types
6. **Option Dependencies**: Check for required dependencies between options
7. **Mutual Exclusivity**: Enforce constraints between incompatible options