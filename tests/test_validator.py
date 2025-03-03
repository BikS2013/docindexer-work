"""Tests for the CLI schema validator."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import from docindexer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from docindexer.validator import SchemaValidator, SchemaOption, ValidationError
from docindexer.config import Configuration


class TestSchemaOption(unittest.TestCase):
    """Tests for the SchemaOption class."""
    
    def test_init(self):
        """Test SchemaOption initialization."""
        option_data = {
            "name": "test_option",
            "description": "A test option",
            "type": "string",
            "flag": "--test-option",
            "alternative-flag": "-t",
            "required": True,
            "default-value": "default",
            "requires": ["other_option"],
            "mutually-exclusive-with": ["another_option"]
        }
        
        option = SchemaOption(option_data)
        
        self.assertEqual(option.name, "test_option")
        self.assertEqual(option.description, "A test option")
        self.assertEqual(option.type, "string")
        self.assertEqual(option.flag, "--test-option")
        self.assertEqual(option.alt_flag, "-t")
        self.assertTrue(option.required)
        self.assertEqual(option.default, "default")
        self.assertEqual(option.requires, ["other_option"])
        self.assertEqual(option.mutually_exclusive_with, ["another_option"])
    
    def test_validate_value_string(self):
        """Test validation of string values."""
        option = SchemaOption({"name": "test", "type": "string"})
        
        self.assertTrue(option.validate_value("test")[0])
        self.assertTrue(option.validate_value(None)[0])  # None is allowed
        self.assertFalse(option.validate_value(123)[0])
        
    def test_validate_value_integer(self):
        """Test validation of integer values."""
        option = SchemaOption({"name": "test", "type": "integer"})
        
        self.assertTrue(option.validate_value(123)[0])
        self.assertTrue(option.validate_value("123")[0])  # String that can be converted
        self.assertTrue(option.validate_value(None)[0])   # None is allowed
        self.assertFalse(option.validate_value("abc")[0])
        
    def test_validate_value_boolean(self):
        """Test validation of boolean values."""
        option = SchemaOption({"name": "test", "type": "boolean"})
        
        self.assertTrue(option.validate_value(True)[0])
        self.assertTrue(option.validate_value(False)[0])
        self.assertTrue(option.validate_value(None)[0])  # None is allowed
        self.assertFalse(option.validate_value("true")[0])
        self.assertFalse(option.validate_value(1)[0])
        
    def test_validate_value_float(self):
        """Test validation of float values."""
        option = SchemaOption({"name": "test", "type": "float"})
        
        self.assertTrue(option.validate_value(123.5)[0])
        self.assertTrue(option.validate_value("123.5")[0])  # String that can be converted
        self.assertTrue(option.validate_value(None)[0])     # None is allowed
        self.assertFalse(option.validate_value("abc")[0])
        
    def test_validate_value_array(self):
        """Test validation of array values."""
        option = SchemaOption({"name": "test", "type": "array"})
        
        self.assertTrue(option.validate_value([])[0])
        self.assertTrue(option.validate_value([1, 2, 3])[0])
        self.assertTrue(option.validate_value(None)[0])  # None is allowed
        self.assertFalse(option.validate_value("test")[0])
        self.assertFalse(option.validate_value(123)[0])


class TestSchemaValidator(unittest.TestCase):
    """Tests for the SchemaValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary schema file for testing
        self.schema_file = tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.json')
        self.schema_file.write('''
        {
            "name": "test-cli",
            "description": "Test CLI",
            "version": "1.0.0",
            "globalOptions": [
                {
                    "name": "verbose",
                    "description": "Enable verbose output",
                    "type": "boolean",
                    "flag": "--verbose",
                    "required": false
                }
            ],
            "commonOptions": [
                {
                    "name": "output",
                    "description": "Output file",
                    "type": "string",
                    "flag": "--output",
                    "alternative-flag": "-o",
                    "required": false
                },
                {
                    "name": "recursive",
                    "description": "Process recursively",
                    "type": "boolean",
                    "flag": "--recursive",
                    "alternative-flag": "-r",
                    "required": false,
                    "default-value": false
                },
                {
                    "name": "source_folder",
                    "description": "Source folder",
                    "type": "string",
                    "flag": "--source-folder",
                    "alternative-flag": "-s",
                    "required": false,
                    "mutually-exclusive-with": ["file_name"]
                },
                {
                    "name": "file_name",
                    "description": "File name",
                    "type": "string",
                    "flag": "--file-name",
                    "alternative-flag": "-f",
                    "required": false,
                    "mutually-exclusive-with": ["source_folder"]
                },
                {
                    "name": "debug",
                    "description": "Enable debug mode",
                    "type": "boolean",
                    "flag": "--debug",
                    "required": false,
                    "default-value": false
                }
            ],
            "commands": [
                {
                    "name": "process",
                    "description": "Process files",
                    "options": [
                        {
                            "name": "format",
                            "description": "Output format",
                            "type": "string",
                            "flag": "--format",
                            "required": true
                        }
                    ],
                    "inheritsCommonOptions": true,
                    "requiredOptions": [
                        ["source_folder", "file_name"],
                        "format"
                    ]
                },
                {
                    "name": "version",
                    "description": "Show version",
                    "options": [],
                    "inheritsCommonOptions": false
                }
            ],
            "configurationSources": [
                {
                    "name": "Command-line arguments",
                    "priority": 1,
                    "description": "Options specified directly on the command line"
                },
                {
                    "name": "Local config file",
                    "priority": 2,
                    "path": "./config.json",
                    "description": "JSON configuration file in the current directory"
                },
                {
                    "name": "Global config file",
                    "priority": 3,
                    "path": "~/.docindexer/config.json",
                    "description": "JSON configuration file in the user's home directory"
                }
            ]
        }
        ''')
        self.schema_file.close()
        
        # Create the validator
        self.validator = SchemaValidator(self.schema_file.name)
    
    def tearDown(self):
        """Tear down test fixtures."""
        os.unlink(self.schema_file.name)
    
    def test_load_schema(self):
        """Test loading schema from file."""
        self.assertEqual(self.validator.schema["name"], "test-cli")
        self.assertEqual(len(self.validator.global_options), 1)
        self.assertEqual(len(self.validator.common_options), 5)
        self.assertEqual(len(self.validator.commands), 2)
        self.assertEqual(len(self.validator.config_sources), 3)
    
    def test_validate_command_success(self):
        """Test successful command validation."""
        args = {
            "format": "json",
            "source_folder": "/tmp",
            "recursive": True
        }
        
        is_valid, errors = self.validator.validate_command("process", args)
        
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_command_unknown_command(self):
        """Test validation with unknown command."""
        args = {"format": "json"}
        
        is_valid, errors = self.validator.validate_command("unknown", args)
        
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("Unknown command", errors[0])
    
    def test_validate_command_missing_required(self):
        """Test validation with missing required option."""
        args = {
            "source_folder": "/tmp"
        }
        
        is_valid, errors = self.validator.validate_command("process", args)
        
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("Required option missing", errors[0])
    
    def test_validate_command_invalid_value(self):
        """Test validation with invalid value type."""
        args = {
            "format": 123,  # Should be string
            "source_folder": "/tmp"
        }
        
        is_valid, errors = self.validator.validate_command("process", args)
        
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("must be a string", errors[0])
    
    def test_validate_command_mutually_exclusive(self):
        """Test validation with mutually exclusive options."""
        args = {
            "format": "json",
            "source_folder": "/tmp",
            "file_name": "test.txt"
        }
        
        is_valid, errors = self.validator.validate_command("process", args)
        
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("cannot be used together" in e for e in errors))
    
    def test_normalize_args(self):
        """Test argument normalization."""
        args = {
            "--format": "json",
            "--source-folder": "/tmp",
            "-r": True,
            "command": "process"
        }
        
        normalized = self.validator.normalize_args(args)
        
        self.assertEqual(normalized["format"], "json")
        self.assertEqual(normalized["source_folder"], "/tmp")
        self.assertEqual(normalized["recursive"], True)
        self.assertEqual(normalized["command"], "process")
    
    def test_apply_defaults(self):
        """Test applying default values."""
        args = {
            "format": "json",
            "source_folder": "/tmp"
        }
        
        with_defaults = self.validator.apply_defaults(args, "process")
        
        self.assertEqual(with_defaults["format"], "json")
        self.assertEqual(with_defaults["source_folder"], "/tmp")
        self.assertEqual(with_defaults["recursive"], False)
        self.assertEqual(with_defaults["debug"], False)
    
    def test_get_option_by_flag(self):
        """Test finding option by flag."""
        option = self.validator.get_option_by_flag("--output")
        
        self.assertIsNotNone(option)
        self.assertEqual(option.name, "output")
        
        option = self.validator.get_option_by_flag("-o")
        
        self.assertIsNotNone(option)
        self.assertEqual(option.name, "output")
        
        option = self.validator.get_option_by_flag("--nonexistent")
        
        self.assertIsNone(option)


class TestConfiguration(unittest.TestCase):
    """Tests for the Configuration class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Configuration()
        
        # Create a temporary directory for config files
        self.temp_dir = tempfile.mkdtemp()
        self.local_config_path = Path(self.temp_dir) / "config.json"
        self.global_config_dir = Path(self.temp_dir) / ".docindexer"
        self.global_config_dir.mkdir(exist_ok=True)
        self.global_config_path = self.global_config_dir / "config.json"
        
        # Set the config paths to our test paths
        self.config._local_config_path = self.local_config_path
        self.config._global_config_path = self.global_config_path
        
        # Create test config files
        with open(self.global_config_path, 'w') as f:
            json.dump({
                "global_option": "global_value",
                "shared_option": "global_value"
            }, f)
            
        with open(self.local_config_path, 'w') as f:
            json.dump({
                "local_option": "local_value",
                "shared_option": "local_value"
            }, f)
    
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove test files if they exist
        if self.local_config_path.exists():
            os.unlink(self.local_config_path)
        if self.global_config_path.exists():
            os.unlink(self.global_config_path)
        if self.global_config_dir.exists():
            os.rmdir(self.global_config_dir)
        os.rmdir(self.temp_dir)
    
    def test_load_config(self):
        """Test loading configuration from files."""
        self.config.load_config()
        
        self.assertEqual(self.config._global_config["global_option"], "global_value")
        self.assertEqual(self.config._local_config["local_option"], "local_value")
        
        # Check merged config (local overrides global)
        self.assertEqual(self.config.get("global_option"), "global_value")
        self.assertEqual(self.config.get("local_option"), "local_value")
        self.assertEqual(self.config.get("shared_option"), "local_value")
    
    def test_set_cli_args(self):
        """Test setting command-line arguments."""
        self.config.load_config()
        
        self.config.set_cli_args({
            "cli_option": "cli_value",
            "shared_option": "cli_value"
        })
        
        # CLI args should override both local and global
        self.assertEqual(self.config.get("global_option"), "global_value")
        self.assertEqual(self.config.get("local_option"), "local_value")
        self.assertEqual(self.config.get("cli_option"), "cli_value")
        self.assertEqual(self.config.get("shared_option"), "cli_value")
    
    def test_create_config_files(self):
        """Test creating configuration files."""
        # First load existing configs
        self.config.load_config()
        
        # Add a CLI option that overrides shared_option
        self.config.set_cli_args({
            "cli_option": "cli_value", 
            "shared_option": "cli_value"
        })
        
        # Create a new local config file
        if self.local_config_path.exists():
            os.unlink(self.local_config_path)
        self.config.create_local_config()
        
        # Check that the file was created with the merged config
        with open(self.local_config_path, 'r') as f:
            new_local_config = json.load(f)
        
        self.assertEqual(new_local_config["global_option"], "global_value")
        self.assertEqual(new_local_config["local_option"], "local_value")
        self.assertEqual(new_local_config["cli_option"], "cli_value")
        self.assertEqual(new_local_config["shared_option"], "cli_value")
    
    def test_missing_config_file(self):
        """Test behavior with missing config files."""
        # Make sure the files don't exist for this test
        if self.local_config_path.exists():
            os.unlink(self.local_config_path)
        if self.global_config_path.exists():
            os.unlink(self.global_config_path)
        
        # This should not raise an exception
        self.config.load_config()
        
        # Dictionaries should be empty
        self.assertEqual(len(self.config._global_config), 0)
        self.assertEqual(len(self.config._local_config), 0)
    
    def test_invalid_json(self):
        """Test behavior with invalid JSON in config files."""
        # Write invalid JSON
        with open(self.local_config_path, 'w') as f:
            f.write("not valid json")
        
        # This should not raise an exception
        self.config.load_local_config()
        
        # Dictionary should be empty
        self.assertEqual(len(self.config._local_config), 0)
    
    def test_dictionary_interface(self):
        """Test dictionary-like interface."""
        self.config.load_config()
        
        # Test __getitem__
        self.assertEqual(self.config["global_option"], "global_value")
        self.assertEqual(self.config["local_option"], "local_value")
        
        # Test __contains__
        self.assertTrue("global_option" in self.config)
        self.assertTrue("local_option" in self.config)
        self.assertFalse("nonexistent" in self.config)
        
        # Test keys
        keys = self.config.keys()
        self.assertTrue("global_option" in keys)
        self.assertTrue("local_option" in keys)
        self.assertTrue("shared_option" in keys)
        
        # Test as_dict
        config_dict = self.config.as_dict()
        self.assertEqual(config_dict["global_option"], "global_value")
        self.assertEqual(config_dict["local_option"], "local_value")
        self.assertEqual(config_dict["shared_option"], "local_value")


if __name__ == '__main__':
    unittest.main()