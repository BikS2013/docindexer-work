# Python CLI Schema Validator and Configuration Management

## Background
I need to develop a command-line interface (CLI) application that validates and processes arguments against a schema definition, with configuration management capabilities.

## Requirements

### Core Functionality
1. Create a Python script that:
   - Validates command-line arguments against the definitions in `cli_schema.json`
   - Decodes validated arguments into a dedicated Configuration class
   - Implements configuration file management (read/write) using the same Configuration class
   - Properly merges configuration file settings with command-line arguments (CLI args take precedence)

### Configuration Management
1. The system should support both local and global configuration files
2. Command-line arguments should override configuration file values
3. Configuration files should be in a standard format (JSON, YAML, or TOML)
4. The Configuration class should have clear methods for:
   - Loading from config files
   - Saving to config files
   - Merging with command-line arguments
   - Accessing configuration values

### Testing
1. Create a comprehensive test suite with at least 20 test scenarios covering:
   - Valid argument combinations
   - Invalid argument combinations
   - Different configuration file states
   - Precedence rules (CLI overriding config files)
   - Edge cases (missing files, malformed inputs, etc.)
2. Store test scenarios in a JSON file with:
   - Test inputs (arguments, config file contents)
   - Expected outputs (success/failure, resulting configuration)
   - Description of what each test validates
3. Create an automated test runner to execute all test cases and report results

### Documentation
1. Update the `cli_interface_explained.md` file to match the current `cli_schema.json` structure
2. Include docstrings and comments in the code following Python best practices

### Code Quality
1. Follow SOLID principles:
   - Single Responsibility: Each class/module has one job
   - Open/Closed: Extensible without modification
   - Liskov Substitution: Proper inheritance hierarchy
   - Interface Segregation: Focused interfaces
   - Dependency Inversion: Depend on abstractions
2. Implement proper error handling and user feedback
3. Use type hints throughout the codebase
4. Structure code in a modular, maintainable way

## Deliverables
1. Updated `cli_interface_explained.md` file
2. Python implementation of the CLI validator and Configuration class
3. Test scenarios JSON file with at least 20 test cases
4. Automated test runner script
5. Brief documentation on how to use and extend the system

## Out of Scope
- Any business logic beyond configuration management
- UI elements other than help text and error messages
- External integrations

---------------------------------------------------------------

I want you to study the cli_schema.json file and create a python script to:
1. validate the command line arguments against the cli_schema.json description
2. decode the command line arguments to a "configuration" class
3. the configuration class must be used also to read and write the local or global configuration files
4. when the configurtion class is populated by the config files, any command line argument must by added or the same class.
I want you to create also a number (more than 20) of test scenarios that will be used to validate the command line parsing.
The test scenarios must be placed in a json file together with their expected result (success of failure), and you must create a PYTHON script to automated run them and evaluate the results. 

I don't want you to implement any other functionality yet apart of collecting the command line arguments, validating them against the schema definition, populating the configuration class, creating and/or reading the configuration files, and displaying the appropriate help.

You must take into account that cli_interface_explained.md is outdated, so you must fix it according to the new cli_schema.json file. 

The code you will write must be structured, following the SOLID principles and be according the known coding best practices. 