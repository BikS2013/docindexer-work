"""Integration tests for the CLI controller with FileIterator."""

import os
import sys
import json
import tempfile
import unittest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Add the parent directory to the path to import from docindexer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from docindexer.cli import main
from docindexer.file_iterator import FileIterator, FileInfo


class TestCliIntegration(unittest.TestCase):
    """Integration tests for the CLI with FileIterator."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory with test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create some test files with different extensions
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f"file{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"Test content {i}")
                
        for i in range(2):
            file_path = os.path.join(self.temp_dir, f"document{i}.md")
            with open(file_path, "w") as f:
                f.write(f"Markdown content {i}")
        
        # Create a subdirectory with more files
        self.subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(self.subdir)
        
        for i in range(2):
            file_path = os.path.join(self.subdir, f"subfile{i}.json")
            with open(file_path, "w") as f:
                json.dump({"index": i, "content": f"JSON content {i}"}, f)
        
        # Create a CLI runner
        self.runner = CliRunner()
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_list_command_basic(self):
        """Test the basic functionality of the 'list' command."""
        # Run the command
        result = self.runner.invoke(main, ['list', '--source-folder', self.temp_dir])
        
        # Check that the command succeeded
        self.assertEqual(result.exit_code, 0)
        
        # Check that the output contains the expected information
        self.assertIn("Found", result.output)
        self.assertIn("file0.txt", result.output)
        self.assertIn("file1.txt", result.output)
        self.assertIn("file2.txt", result.output)
        self.assertIn("document0.md", result.output)
        self.assertIn("document1.md", result.output)
    
    def test_list_command_recursive(self):
        """Test 'list' command with recursive option."""
        # Run the command with recursive option
        result = self.runner.invoke(main, ['list', '--source-folder', self.temp_dir, '--recursive'])
        
        # Check that the command succeeded
        self.assertEqual(result.exit_code, 0)
        
        # Check that the output contains files from subdirectory
        self.assertIn("subfile0.json", result.output)
        self.assertIn("subfile1.json", result.output)
    
    def test_list_command_non_recursive(self):
        """Test 'list' command with non-recursive option."""
        # Run the command with non-recursive option
        result = self.runner.invoke(main, ['list', '--source-folder', self.temp_dir, '--no-recursive'])
        
        # Check that the command succeeded
        self.assertEqual(result.exit_code, 0)
        
        # Check that the output doesn't contain files from subdirectory
        self.assertNotIn("subfile0.json", result.output)
        self.assertNotIn("subfile1.json", result.output)
    
    def test_list_command_pattern(self):
        """Test 'list' command with pattern filtering."""
        # Run the command with a pattern
        result = self.runner.invoke(main, [
            'list', '--source-folder', self.temp_dir, '--pattern', '*.md'
        ])
        
        # Check that the command succeeded
        self.assertEqual(result.exit_code, 0)
        
        # Check that only markdown files are included
        self.assertIn("document0.md", result.output)
        self.assertIn("document1.md", result.output)
        self.assertNotIn("file0.txt", result.output)
        self.assertNotIn("file1.txt", result.output)
    
    def test_list_command_regex(self):
        """Test 'list' command with regex pattern filtering."""
        # Run the command with a regex pattern
        result = self.runner.invoke(main, [
            'list', '--source-folder', self.temp_dir, '--pattern', '^file\\d\\.txt$', '--regex'
        ])
        
        # Check that the command succeeded
        self.assertEqual(result.exit_code, 0)
        
        # Check that only matching files are included
        self.assertIn("file0.txt", result.output)
        self.assertIn("file1.txt", result.output)
        self.assertNotIn("document0.md", result.output)
        self.assertNotIn("document1.md", result.output)
    
    def test_list_command_limit(self):
        """Test 'list' command with limit option."""
        # Run the command with a limit
        result = self.runner.invoke(main, [
            'list', '--source-folder', self.temp_dir, '--limit', '2'
        ])
        
        # Check that the command succeeded
        self.assertEqual(result.exit_code, 0)
        
        # Count how many file entries are in the output
        file_lines = [line for line in result.output.split('\n') if '.txt' in line or '.md' in line]
        self.assertEqual(len(file_lines), 2)
    
    def test_list_command_sort_by_name(self):
        """Test 'list' command with name sorting."""
        # Run the command with name sorting
        result = self.runner.invoke(main, [
            'list', '--source-folder', self.temp_dir, '--sort-by', 'name'
        ])
        
        # Check that the command succeeded
        self.assertEqual(result.exit_code, 0)
        
        # Extract file names from output
        lines = result.output.split('\n')
        file_lines = [line for line in lines if '.txt' in line or '.md' in line]
        
        # Check that they're sorted by name
        for i in range(1, len(file_lines)):
            self.assertLessEqual(file_lines[i-1], file_lines[i])
    
    def test_list_command_debug(self):
        """Test 'list' command with debug option."""
        # Run the command with debug option
        result = self.runner.invoke(main, [
            'list', '--source-folder', self.temp_dir, '--debug'
        ])
        
        # Check that the command succeeded
        self.assertEqual(result.exit_code, 0)
        
        # Check that debug info is included
        self.assertIn("Configuration", result.output)
    
    def test_list_command_single_file(self):
        """Test 'list' command with a specific file."""
        file_path = os.path.join(self.temp_dir, "file0.txt")
        
        # Run the command with a file path
        result = self.runner.invoke(main, [
            'list', '--file-name', file_path, '--no-recursive'
        ])
        
        # Check that the command succeeded
        self.assertEqual(result.exit_code, 0)
        
        # Check that only the specified file is included
        self.assertIn("file0.txt", result.output)
        self.assertNotIn("file1.txt", result.output)
        self.assertNotIn("document0.md", result.output)
    
    def test_list_command_nonexistent_path(self):
        """Test 'list' command with a non-existent path."""
        # Run the command with a non-existent path
        result = self.runner.invoke(main, [
            'list', '--source-folder', os.path.join(self.temp_dir, "nonexistent")
        ])
        
        # Check that the command succeeded (the command itself shouldn't fail,
        # even though no files are found)
        self.assertEqual(result.exit_code, 0)
        
        # Check that the output indicates no files were found
        self.assertIn("No files found", result.output)
    
    def test_list_command_with_max_depth(self):
        """Test 'list' command with max_depth option."""
        # Create a nested directory structure
        level1 = os.path.join(self.temp_dir, "level1")
        level2 = os.path.join(level1, "level2")
        level3 = os.path.join(level2, "level3")
        os.makedirs(level3)
        
        # Create files at each level
        for level, path in [
            (1, os.path.join(level1, "file1.txt")),
            (2, os.path.join(level2, "file2.txt")),
            (3, os.path.join(level3, "file3.txt"))
        ]:
            with open(path, "w") as f:
                f.write(f"Level {level} file")
        
        # Run the command with max_depth=1
        result = self.runner.invoke(main, [
            'list', '--source-folder', level1, '--recursive', '--max-depth', '1'
        ])
        
        # Check that the command succeeded
        self.assertEqual(result.exit_code, 0)
        
        # Check that only files up to level 2 are included
        self.assertIn("file1.txt", result.output)
        self.assertIn("file2.txt", result.output)
        self.assertNotIn("file3.txt", result.output)


if __name__ == "__main__":
    unittest.main()