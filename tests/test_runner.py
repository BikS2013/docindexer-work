#!/usr/bin/env python3
"""Test runner for CLI schema validator and configuration management."""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import from docindexer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

from docindexer.validator import SchemaValidator, ValidationError
from docindexer.config import Configuration
from docindexer.cli import main


class TestResult:
    """Stores the result of a test scenario."""
    
    def __init__(self, scenario_id: int, description: str, category: str, success: bool, details: str = ""):
        """Initialize a test result.
        
        Args:
            scenario_id: ID of the test scenario
            description: Description of the test scenario
            category: Category of the test scenario
            success: Whether the test succeeded
            details: Additional details about the test result
        """
        self.scenario_id = scenario_id
        self.description = description
        self.category = category
        self.success = success
        self.details = details


class TestRunner:
    """Runner for CLI test scenarios."""
    
    def __init__(self, scenarios_file: Path):
        """Initialize a test runner.
        
        Args:
            scenarios_file: Path to the JSON file containing test scenarios
        """
        self.scenarios_file = scenarios_file
        self.scenarios: List[Dict[str, Any]] = []
        self.results: List[TestResult] = []
        self.console = Console()
        
        self._load_scenarios()
    
    def _load_scenarios(self) -> None:
        """Load test scenarios from the JSON file."""
        try:
            with open(self.scenarios_file, 'r') as f:
                data = json.load(f)
                self.scenarios = data.get('test_scenarios', [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.console.print(f"[bold red]Error loading test scenarios:[/] {str(e)}")
            sys.exit(1)
    
    def _setup_config_files(self, scenario: Dict[str, Any]) -> Tuple[Optional[Path], Optional[Path]]:
        """Set up configuration files for the test scenario.
        
        Args:
            scenario: The test scenario
            
        Returns:
            Tuple of (local_config_path, global_config_path)
        """
        if 'config_files' not in scenario:
            return None, None
            
        local_config_path = None
        global_config_path = None
        
        if 'local' in scenario['config_files']:
            local_config_dir = tempfile.mkdtemp()
            local_config_path = Path(local_config_dir) / "config.json"
            with open(local_config_path, 'w') as f:
                json.dump(scenario['config_files']['local'], f)
        
        if 'global' in scenario['config_files']:
            global_config_dir = tempfile.mkdtemp()
            global_config_path = Path(global_config_dir) / "config.json"
            # Create parent directory
            (Path(global_config_dir) / ".docindexer").mkdir(exist_ok=True)
            with open(global_config_path, 'w') as f:
                json.dump(scenario['config_files']['global'], f)
                
        return local_config_path, global_config_path
    
    def _cleanup_config_files(self, local_path: Optional[Path], global_path: Optional[Path]) -> None:
        """Clean up temporary configuration files.
        
        Args:
            local_path: Path to the local config file
            global_path: Path to the global config file
        """
        if local_path and local_path.exists():
            os.unlink(local_path)
            os.rmdir(local_path.parent)
            
        if global_path and global_path.exists():
            os.unlink(global_path)
            # Also remove the .docindexer directory
            docindexer_dir = global_path.parent / ".docindexer"
            if docindexer_dir.exists():
                os.rmdir(docindexer_dir)
            os.rmdir(global_path.parent)
    
    def run_all_tests(self) -> None:
        """Run all test scenarios."""
        self.console.print(Panel.fit(
            f"[bold]Running {len(self.scenarios)} test scenarios[/]",
            title="DocIndexer CLI Test Runner",
            border_style="blue"
        ))
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn()
        ) as progress:
            task = progress.add_task("[cyan]Running tests...", total=len(self.scenarios))
            
            for scenario in self.scenarios:
                # Update progress description
                scenario_id = scenario.get('id', 0)
                description = scenario.get('description', 'Unnamed test')
                category = scenario.get('test_category', 'Uncategorized')
                
                progress.update(task, description=f"[cyan]Running test {scenario_id}: {description}")
                
                # Run the test
                success, details = self._run_scenario(scenario)
                
                # Store the result
                self.results.append(TestResult(scenario_id, description, category, success, details))
                
                # Update progress
                progress.update(task, advance=1)
        
        # Show test results
        self._show_results()
    
    def _run_scenario(self, scenario: Dict[str, Any]) -> Tuple[bool, str]:
        """Run a single test scenario.
        
        Args:
            scenario: The test scenario
            
        Returns:
            Tuple of (success, details)
        """
        command = scenario.get('command', '')
        args = scenario.get('args', {})
        expected = scenario.get('expected', {})
        
        # Set up configuration files if provided
        local_config_path, global_config_path = self._setup_config_files(scenario)
        
        try:
            # Mock the CLI execution
            with patch('docindexer.cli.config') as mock_config:
                # Set up the configuration mock
                mock_config.as_dict.return_value = args
                
                # Prepare command arguments
                cli_args = [command]
                for flag, value in args.items():
                    if isinstance(value, bool):
                        if value:
                            cli_args.append(f"--{flag.replace('_', '-')}")
                    else:
                        cli_args.append(f"--{flag.replace('_', '-')}")
                        cli_args.append(str(value))
                
                # Run the command
                result = main.main(cli_args, standalone_mode=False)
                
                # Check if the result matches the expected outcome
                if expected.get('success', True):
                    if result != 0:
                        return False, f"Expected success, but command failed with exit code {result}"
                else:
                    if result == 0:
                        return False, "Expected failure, but command succeeded"
                
                return True, "Test passed"
                
        except Exception as e:
            if expected.get('success', True):
                return False, f"Unexpected exception: {str(e)}"
            else:
                # Check if the error matches the expected error
                if 'error' in expected:
                    if expected['error'].lower() in str(e).lower():
                        return True, "Expected error occurred"
                    else:
                        return False, f"Error occurred but did not match expected error: {str(e)}"
                return True, "Expected error occurred"
        finally:
            # Clean up configuration files
            self._cleanup_config_files(local_config_path, global_config_path)
    
    def _show_results(self) -> None:
        """Show the test results."""
        # Calculate statistics
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        
        # Display summary
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold]Test Summary: {passed}/{total} passed ({passed/total:.1%})[/]",
            title="Test Results",
            border_style="green" if failed == 0 else "red"
        ))
        
        # Display results by category
        categories = set(r.category for r in self.results)
        
        for category in sorted(categories):
            category_results = [r for r in self.results if r.category == category]
            category_passed = sum(1 for r in category_results if r.success)
            
            self.console.print(f"\n[bold]{category}[/] ({category_passed}/{len(category_results)} passed)")
            
            # Create a table for this category
            table = Table(show_header=True, header_style="bold")
            table.add_column("ID", justify="right", style="cyan")
            table.add_column("Description")
            table.add_column("Result", justify="center")
            table.add_column("Details")
            
            for result in sorted(category_results, key=lambda r: r.scenario_id):
                result_style = "green" if result.success else "red"
                result_text = "[bold green]PASS[/]" if result.success else "[bold red]FAIL[/]"
                
                table.add_row(
                    str(result.scenario_id),
                    result.description,
                    result_text,
                    result.details
                )
            
            self.console.print(table)


if __name__ == '__main__':
    # Find the test scenarios file
    scenarios_file = Path(__file__).parent / "test_scenarios.json"
    
    # Run all tests
    runner = TestRunner(scenarios_file)
    runner.run_all_tests()