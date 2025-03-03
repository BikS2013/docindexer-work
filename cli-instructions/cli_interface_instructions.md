# DocIndexer CLI Interface Instructions

This document provides detailed instructions on using the DocIndexer command-line interface (CLI).

## Overview

DocIndexer is a tool designed to process and index documents for efficient retrieval and vectorization. The CLI provides a robust interface for interacting with the tool, with a variety of commands and options to customize the behavior.

## Command Structure

The general structure of a DocIndexer command is:

```bash
docindexer [global options] COMMAND [command options] [arguments]
```

## Global Options

Global options are available to all commands:

| Option | Description |
| ------ | ----------- |
| `--readme` | Display README and exit |
| `--help` | Show help and exit |
| `--version` | Show version and exit |

## Common Options

These options are available to most commands:

| Option | Description | Default |
| ------ | ----------- | ------- |
| `--source-folder`, `-s` | Path to the folder containing files to be processed | `.` (current directory) |
| `--catalogue`, `-c` | Path to a catalogue JSON file | None |
| `--file-name`, `-n` | The name of the file to be processed | None |
| `--recursive`, `-R` | Process files in subfolders recursively | `true` |
| `--limit`, `-l` | Limit the number of files to be processed | None |
| `--random`, `-r` | Process files in random order | `false` |
| `--output-folder`, `-o` | Path to the folder where processed files should be saved | `./output` |
| `--create-local-config` | Create a local config.json file with current settings | `false` |
| `--create-global-config` | Create a global config.json file with current settings | `false` |
| `--run-after-config-create` | Run the command after creating config file(s) | `true` |
| `--show-config` | Show effective configuration and exit | `false` |
| `--debug` | Enable debug mode with additional logging | `false` |
| `--dry-run` | Perform a dry run without saving any files | `false` |

### Input Source Options

You must specify one (and only one) of the following input source options:

- `--source-folder`: Process all files in a directory
- `--catalogue`: Process files listed in a JSON catalogue file
- `--file-name`: Process a single file

## Commands

### index

The `index` command processes documents from the specified source and creates an index.

```bash
docindexer index PATH [options]
```

**Arguments:**
- `PATH`: Directory path containing documents to index

**Options:**
- `--recursive`, `-r`, `-R`: Index documents recursively (default: true)
- `--output`, `-o`: Output file path for the index

**Examples:**

```bash
# Index documents in the current directory
docindexer index .

# Index documents recursively in a specific directory
docindexer index /path/to/docs --recursive

# Index documents and save the index to a file
docindexer index /path/to/docs --output index.json
```

### structure

The `structure` command creates a hierarchical JSON representation of document structure.

```bash
docindexer structure [options]
```

**Options:**
- `--ommit-properties`: Comma-separated list of properties to omit from the JSON output

**Examples:**

```bash
# Create structure representation of documents in a folder
docindexer structure --source-folder /path/to/docs

# Create structure with specific properties omitted
docindexer structure --source-folder /path/to/docs --ommit-properties "items,size"
```

### config

The `config` command displays or manages configuration settings.

```bash
docindexer config [options]
```

**Options:**
- `--source`: Which configuration source to display (`all`, `global`, `local`, or `effective`)

**Examples:**

```bash
# Show effective configuration
docindexer config

# Show all configuration sources
docindexer config --source all

# Show only global configuration
docindexer config --source global
```

### schema

The `schema` command visualizes the CLI schema structure.

```bash
docindexer schema
```

## Configuration Files

DocIndexer supports multiple configuration sources with the following precedence:

1. **Command-line arguments** (highest priority)
2. **Local config file** (`./config.json`)
3. **Global config file** (`~/.docindexer/config.json`)

Configuration files use JSON format and can contain any of the options available as command-line arguments.

### Creating Configuration Files

You can create configuration files with your current settings using these options:

```bash
# Create a local configuration file
docindexer index /path/to/docs --create-local-config

# Create a global configuration file
docindexer index /path/to/docs --create-global-config

# Create both and exit without running the command
docindexer index /path/to/docs --create-local-config --create-global-config --run-after-config-create=false
```

### Sample Configuration File

```json
{
  "recursive": true,
  "limit": 100,
  "output_folder": "./processed",
  "debug": false,
  "dry_run": false
}
```

## Advanced Usage

### Dry Run Mode

```bash
docindexer index /path/to/docs --dry-run
```

### Debug Mode

```bash
docindexer index /path/to/docs --debug
```

### Using Configuration to Simplify Commands

Once you've created a configuration file with your common settings, you can run simplified commands:

```bash
# Before (with many arguments)
docindexer index /path/to/docs --recursive --output-folder ./processed --limit 100

# After creating a config file with those settings
docindexer index /path/to/docs
```