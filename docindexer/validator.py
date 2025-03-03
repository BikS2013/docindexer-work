"""CLI Schema Validator for DocIndexer."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised for CLI schema validation errors."""
    pass


class SchemaOption:
    """Represents an option defined in the CLI schema."""
    
    def __init__(self, option_data: Dict[str, Any]):
        """Initialize a SchemaOption.
        
        Args:
            option_data: Dictionary containing option data from schema
        """
        self.name = option_data.get("name", "")
        self.description = option_data.get("description", "")
        self.type = option_data.get("type", "string")
        self.flag = option_data.get("flag", "")
        self.alt_flag = option_data.get("alternative-flag", "")
        self.required = option_data.get("required", False)
        self.default = option_data.get("default-value", None)
        self.requires = option_data.get("requires", [])
        self.mutually_exclusive_with = option_data.get("mutually-exclusive-with", [])
    
    def validate_value(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate a value against this option's type.
        
        Args:
            value: The value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return (True, None)  # None is allowed unless required is checked separately
            
        if self.type == "string":
            if not isinstance(value, str):
                return (False, f"Value for {self.name} must be a string")
        elif self.type == "integer":
            try:
                int(value)
            except (ValueError, TypeError):
                return (False, f"Value for {self.name} must be an integer")
        elif self.type == "boolean":
            if not isinstance(value, bool):
                return (False, f"Value for {self.name} must be a boolean")
        elif self.type == "float":
            try:
                float(value)
            except (ValueError, TypeError):
                return (False, f"Value for {self.name} must be a float")
        elif self.type == "array":
            if not isinstance(value, list):
                return (False, f"Value for {self.name} must be an array")
                
        return (True, None)


class SchemaValidator:
    """Validates command-line arguments against a CLI schema."""
    
    def __init__(self, schema_path: Optional[Union[str, Path]] = None):
        """Initialize a SchemaValidator.
        
        Args:
            schema_path: Path to the CLI schema file
        """
        self.schema: Dict[str, Any] = {}
        self.global_options: Dict[str, SchemaOption] = {}
        self.common_options: Dict[str, SchemaOption] = {}
        self.command_options: Dict[str, Dict[str, SchemaOption]] = {}
        self.commands: List[str] = []
        self.config_sources: List[Dict[str, Any]] = []
        
        if schema_path:
            self.load_schema(schema_path)
    
    def load_schema(self, schema_path: Union[str, Path]) -> None:
        """Load and parse the CLI schema file.
        
        Args:
            schema_path: Path to the CLI schema file
            
        Raises:
            ValidationError: If the schema file is invalid or cannot be read
        """
        try:
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
            
            # Process global options
            for option_data in self.schema.get("globalOptions", []):
                option = SchemaOption(option_data)
                self.global_options[option.name] = option
            
            # Process common options
            for option_data in self.schema.get("commonOptions", []):
                option = SchemaOption(option_data)
                self.common_options[option.name] = option
            
            # Process commands and their options
            for command_data in self.schema.get("commands", []):
                command_name = command_data.get("name", "")
                if not command_name:
                    continue
                    
                self.commands.append(command_name)
                self.command_options[command_name] = {}
                
                # Add command-specific options
                for option_data in command_data.get("options", []):
                    option = SchemaOption(option_data)
                    self.command_options[command_name][option.name] = option
                
                # If command inherits common options, add them
                if command_data.get("inheritsCommonOptions", False):
                    for name, option in self.common_options.items():
                        if name not in self.command_options[command_name]:
                            self.command_options[command_name][name] = option
            
            # Process configuration sources
            self.config_sources = self.schema.get("configurationSources", [])
            
            logger.debug(f"Successfully loaded schema: {len(self.commands)} commands, "
                       f"{len(self.global_options)} global options, "
                       f"{len(self.common_options)} common options")
                       
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValidationError(f"Failed to load schema file: {str(e)}")
    
    def validate_command(self, command: str, args: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate command-line arguments for a specific command.
        
        Args:
            command: Command name
            args: Dictionary of command-line arguments
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if command not in self.commands:
            return (False, [f"Unknown command: {command}"])
        
        errors = []
        
        # Get command options
        command_opts = self.command_options.get(command, {})
        
        # Validate all provided arguments
        for arg_name, arg_value in args.items():
            # Skip None values (not provided)
            if arg_value is None:
                continue
                
            # Skip special arguments
            if arg_name in ['command', 'path']:
                continue
                
            # Check if this is a valid option for this command
            if arg_name in command_opts:
                option = command_opts[arg_name]
                is_valid, error = option.validate_value(arg_value)
                if not is_valid:
                    errors.append(error)
            elif arg_name in self.global_options:
                option = self.global_options[arg_name]
                is_valid, error = option.validate_value(arg_value)
                if not is_valid:
                    errors.append(error)
            else:
                errors.append(f"Unknown option for command '{command}': {arg_name}")
        
        # Check for required options
        for opt_name, option in command_opts.items():
            if option.required and (opt_name not in args or args[opt_name] is None):
                errors.append(f"Required option missing: {option.flag}")
        
        # Check for mutually exclusive options
        for opt_name, option in command_opts.items():
            # Skip if this option isn't provided
            if opt_name not in args or args[opt_name] is None:
                continue
                
            for mutex_opt in option.mutually_exclusive_with:
                if mutex_opt in args and args[mutex_opt] is not None:
                    errors.append(
                        f"Options {option.flag} and {command_opts[mutex_opt].flag} "
                        f"cannot be used together"
                    )
        
        # Check for required dependencies
        for opt_name, option in command_opts.items():
            # Skip if this option isn't provided
            if opt_name not in args or args[opt_name] is None:
                continue
                
            for req_opt in option.requires:
                if req_opt not in args or args[req_opt] is None:
                    errors.append(
                        f"Option {option.flag} requires {command_opts[req_opt].flag}"
                    )
        
        return (len(errors) == 0, errors)
    
    def get_option_by_flag(self, flag: str, command: Optional[str] = None) -> Optional[SchemaOption]:
        """Find a schema option by its flag or alternative flag.
        
        Args:
            flag: The flag to search for
            command: Optional command name to restrict search
            
        Returns:
            SchemaOption if found, None otherwise
        """
        # Check global options
        for opt in self.global_options.values():
            if opt.flag == flag or opt.alt_flag == flag:
                return opt
        
        # Check command options if command is provided
        if command and command in self.command_options:
            for opt in self.command_options[command].values():
                if opt.flag == flag or opt.alt_flag == flag:
                    return opt
        
        # Check common options
        for opt in self.common_options.values():
            if opt.flag == flag or opt.alt_flag == flag:
                return opt
                
        return None
    
    def normalize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize argument names to match schema option names.
        
        Converts flag names like "--source-folder" to "source_folder".
        
        Args:
            args: Dictionary of command-line arguments with flag names
            
        Returns:
            Dictionary with normalized option names
        """
        normalized = {}
        
        for flag, value in args.items():
            # Skip special args
            if flag == 'command':
                normalized[flag] = value
                continue
                
            # Try to find the option by flag
            option = self.get_option_by_flag(flag)
            if option:
                normalized[option.name] = value
            else:
                # If not found, just use the flag name without dashes
                normalized_name = flag.lstrip('-').replace('-', '_')
                normalized[normalized_name] = value
        
        return normalized
    
    def apply_defaults(self, args: Dict[str, Any], command: Optional[str] = None) -> Dict[str, Any]:
        """Apply default values to missing arguments.
        
        Args:
            args: Dictionary of command-line arguments
            command: Optional command name to include command-specific defaults
            
        Returns:
            Dictionary with defaults applied
        """
        result = args.copy()
        
        # Apply global option defaults
        for name, option in self.global_options.items():
            if name not in result and option.default is not None:
                result[name] = option.default
        
        # Apply common option defaults
        for name, option in self.common_options.items():
            if name not in result and option.default is not None:
                result[name] = option.default
        
        # Apply command option defaults if command is provided
        if command and command in self.command_options:
            for name, option in self.command_options[command].items():
                if name not in result and option.default is not None:
                    result[name] = option.default
        
        return result