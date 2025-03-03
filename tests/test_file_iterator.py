"""Tests for the FileIterator class."""

import os
import sys
import json
import tempfile
import unittest
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import time

# Add the parent directory to the path to import from docindexer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from docindexer.config import Configuration
from docindexer.file_iterator import FileIterator, FileInfo, SortOrder
from docindexer.file_iterator import ExtensionFilter, PatternFilter, SizeFilter, DateFilter, CompositeFilter


class TestFileInfo(unittest.TestCase):
    """Tests for the FileInfo class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.temp_file, "w") as f:
            f.write("Test content")
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_from_path(self):
        """Test creating FileInfo from a path."""
        path = Path(self.temp_file)
        file_info = FileInfo.from_path(path)
        
        self.assertEqual(file_info.path, path)
        self.assertEqual(file_info.size, path.stat().st_size)
        self.assertEqual(file_info.modified, path.stat().st_mtime)
        self.assertEqual(file_info.extension, '.txt')
    
    def test_properties(self):
        """Test FileInfo properties."""
        path = Path(self.temp_file)
        file_info = FileInfo.from_path(path)
        
        self.assertEqual(file_info.name, "test.txt")
        self.assertEqual(file_info.absolute_path, str(path.absolute()))


class TestFileFilters(unittest.TestCase):
    """Tests for the file filter classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.file_info = FileInfo(
            path=Path("/tmp/test.txt"),
            size=1024,
            modified=datetime.now().timestamp(),
            extension=".txt"
        )
    
    def test_extension_filter(self):
        """Test extension filter."""
        # Test with matching extension
        filter1 = ExtensionFilter([".txt", ".md"])
        self.assertTrue(filter1.matches(self.file_info))
        
        # Test with non-matching extension
        filter2 = ExtensionFilter([".pdf", ".docx"])
        self.assertFalse(filter2.matches(self.file_info))
        
        # Test with extensions without dots
        filter3 = ExtensionFilter(["txt", "md"])
        self.assertTrue(filter3.matches(self.file_info))
    
    def test_pattern_filter_glob(self):
        """Test pattern filter with glob patterns."""
        # Test with matching glob pattern
        filter1 = PatternFilter("*.txt")
        self.assertTrue(filter1.matches(self.file_info))
        
        # Test with non-matching glob pattern
        filter2 = PatternFilter("*.pdf")
        self.assertFalse(filter2.matches(self.file_info))
    
    def test_pattern_filter_regex(self):
        """Test pattern filter with regex patterns."""
        # Test with matching regex pattern
        filter1 = PatternFilter(r"test\.(txt|md)", glob=False)
        self.assertTrue(filter1.matches(self.file_info))
        
        # Test with non-matching regex pattern
        filter2 = PatternFilter(r"example\.\w+", glob=False)
        self.assertFalse(filter2.matches(self.file_info))
    
    def test_size_filter(self):
        """Test size filter."""
        # Test with size in range
        filter1 = SizeFilter(min_size=500, max_size=2000)
        self.assertTrue(filter1.matches(self.file_info))
        
        # Test with size below minimum
        filter2 = SizeFilter(min_size=2000)
        self.assertFalse(filter2.matches(self.file_info))
        
        # Test with size above maximum
        filter3 = SizeFilter(max_size=500)
        self.assertFalse(filter3.matches(self.file_info))
    
    def test_date_filter(self):
        """Test date filter."""
        now = datetime.now().timestamp()
        old_time = now - 86400  # 1 day ago
        future_time = now + 86400  # 1 day in the future
        
        # Test with date in range
        filter1 = DateFilter(min_date=old_time, max_date=future_time)
        self.assertTrue(filter1.matches(self.file_info))
        
        # Test with date too old
        filter2 = DateFilter(min_date=future_time)
        self.assertFalse(filter2.matches(self.file_info))
        
        # Test with date too new
        filter3 = DateFilter(max_date=old_time)
        self.assertFalse(filter3.matches(self.file_info))
    
    def test_composite_filter(self):
        """Test composite filter."""
        filter1 = ExtensionFilter([".txt"])
        filter2 = SizeFilter(min_size=500, max_size=2000)
        
        # Test with all filters passing
        composite = CompositeFilter([filter1, filter2])
        self.assertTrue(composite.matches(self.file_info))
        
        # Test with one filter failing
        filter3 = SizeFilter(min_size=2000)
        composite = CompositeFilter([filter1, filter3])
        self.assertFalse(composite.matches(self.file_info))


class TestFileIterator(unittest.TestCase):
    """Tests for the FileIterator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory with test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create some test files (make sure there are exactly 5 files for the tests)
        self.files = []
        for i in range(5):
            file_path = os.path.join(self.temp_dir, f"file{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"Test content {i}")
                
            # Set different modification times
            mod_time = datetime.now() - timedelta(hours=i)
            os.utime(file_path, (mod_time.timestamp(), mod_time.timestamp()))
            
            self.files.append(file_path)
            
        # Create a temp catalogue.json file to avoid counting it in tests
        with open(os.path.join(self.temp_dir, ".temp_catalogue.json"), "w") as f:
            f.write("{}")
            
        # Create a subdirectory with more files
        self.subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(self.subdir)
        
        for i in range(3):
            file_path = os.path.join(self.subdir, f"subfile{i}.md")
            with open(file_path, "w") as f:
                f.write(f"Subdir test content {i}")
            
            self.files.append(file_path)
            
        # Create a test catalogue
        self.catalogue_path = os.path.join(self.temp_dir, ".catalogue.json")
        catalogue_data = {
            "files": [
                str(Path(file_path).absolute()) for file_path in self.files[:3]
            ]
        }
        with open(self.catalogue_path, "w") as f:
            json.dump(catalogue_data, f)
            
        # Create a mock configuration
        self.config = Configuration()
    
    def tearDown(self):
        """Tear down test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_scan_directory_flat(self):
        """Test scanning a directory without recursion."""
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": False
        })
        
        iterator = FileIterator(self.config)
        iterator.load()
        
        # Should only find files in the root directory
        files = iterator.get_files()
        self.assertEqual(len(files), 5)
        for file_info in files:
            self.assertTrue(str(file_info.path).startswith(self.temp_dir))
            self.assertFalse("/subdir/" in str(file_info.path))
    
    def test_scan_directory_recursive(self):
        """Test scanning a directory with recursion."""
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": True
        })
        
        iterator = FileIterator(self.config)
        iterator.load()
        
        # Should find all files
        files = iterator.get_files()
        self.assertEqual(len(files), 8)
    
    def test_max_depth(self):
        """Test maximum recursion depth."""
        # Create a nested directory structure
        nested_dir = os.path.join(self.temp_dir, "level1", "level2", "level3")
        os.makedirs(nested_dir)
        
        # Create files at each level
        for level, path in enumerate([
            os.path.join(self.temp_dir, "level1", "file.txt"),
            os.path.join(self.temp_dir, "level1", "level2", "file.txt"),
            os.path.join(self.temp_dir, "level1", "level2", "level3", "file.txt")
        ]):
            with open(path, "w") as f:
                f.write(f"Level {level+1} file")
        
        # Test with max_depth=1
        self.config.set_cli_args({
            "source_folder": os.path.join(self.temp_dir, "level1"),
            "recursive": True,
            "max_depth": 1
        })
        
        iterator = FileIterator(self.config)
        iterator.load()
        
        # Should only find files up to level2
        files = iterator.get_files()
        self.assertEqual(len(files), 2)  # level1/file.txt and level1/level2/file.txt
        for file_info in files:
            self.assertNotIn("level3", str(file_info.path))
    
    def test_load_from_catalogue(self):
        """Test loading files from a catalogue."""
        self.config.set_cli_args({
            "catalogue": self.catalogue_path
        })
        
        iterator = FileIterator(self.config)
        iterator.load()
        
        # Should find the 3 files listed in the catalogue
        files = iterator.get_files()
        self.assertEqual(len(files), 3)
    
    def test_pattern_filter(self):
        """Test pattern filtering."""
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": True,
            "pattern": "*.md"
        })
        
        iterator = FileIterator(self.config)
        iterator.load()
        
        # Should only find .md files
        files = iterator.get_files()
        self.assertEqual(len(files), 3)  # 3 .md files in the subdir
        for file_info in files:
            self.assertEqual(file_info.extension, ".md")
    
    def test_regex_pattern_filter(self):
        """Test regex pattern filtering."""
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": True,
            "pattern": "^file\\d\\.txt$",
            "use_regex": True
        })
        
        iterator = FileIterator(self.config)
        iterator.load()
        
        # Should only find .txt files in the root directory matching the regex
        files = iterator.get_files()
        self.assertEqual(len(files), 5)  # 5 .txt files in the root directory
        for file_info in files:
            self.assertTrue(file_info.name.startswith("file"))
            self.assertTrue(file_info.name.endswith(".txt"))
    
    def test_sort_by_name(self):
        """Test sorting by name."""
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": False,
            "sort_by": "name"
        })
        
        iterator = FileIterator(self.config)
        iterator.load()
        
        # Files should be sorted by name
        files = iterator.get_files()
        names = [f.name for f in files]
        sorted_names = sorted(names)
        self.assertEqual(names, sorted_names)
        
        # Test descending sort
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": False,
            "sort_by": "name",
            "sort_desc": True
        })
        
        iterator = FileIterator(self.config)
        iterator.load()
        
        # Files should be sorted by name in descending order
        files = iterator.get_files()
        names = [f.name for f in files]
        sorted_names = sorted(names, reverse=True)
        self.assertEqual(names, sorted_names)
    
    def test_sort_by_size(self):
        """Test sorting by size."""
        # Create files with different sizes
        for i in range(3):
            file_path = os.path.join(self.temp_dir, f"size_test{i}.txt")
            with open(file_path, "w") as f:
                f.write("x" * (1000 * (i + 1)))  # 1KB, 2KB, 3KB
        
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": False,
            "pattern": "size_test*.txt",
            "sort_by": "size"
        })
        
        iterator = FileIterator(self.config)
        iterator.load()
        
        # Files should be sorted by size
        files = iterator.get_files()
        sizes = [f.size for f in files]
        self.assertEqual(sizes, sorted(sizes))
    
    def test_sort_by_date(self):
        """Test sorting by modification date."""
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": False,
            "sort_by": "date"
        })
        
        iterator = FileIterator(self.config)
        iterator.load()
        
        # Files should be sorted by modification date
        files = iterator.get_files()
        dates = [f.modified for f in files]
        self.assertEqual(dates, sorted(dates))
    
    def test_random_order(self):
        """Test random ordering."""
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": False,
            "random": True
        })
        
        # With random ordering, running multiple times should eventually give different orders
        orders_seen = set()
        for _ in range(5):
            iterator = FileIterator(self.config)
            iterator.load()
            
            files = iterator.get_files()
            order = tuple(f.name for f in files)
            orders_seen.add(order)
            
            # Reset for next iteration
            iterator.reset()
        
        # We should see at least 2 different orderings
        # Note: This is probabilistic and could theoretically fail
        self.assertGreater(len(orders_seen), 1)
    
    def test_iteration(self):
        """Test iteration interface."""
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": False
        })
        
        iterator = FileIterator(self.config)
        
        # Test iterator protocol
        files = list(iterator)
        self.assertEqual(len(files), 5)
        
        # Test that we can iterate multiple times
        files2 = list(iterator)
        self.assertEqual(len(files2), 5)
        
        # Test that the files are the same
        self.assertEqual(
            sorted(f.name for f in files),
            sorted(f.name for f in files2)
        )
    
    def test_limit(self):
        """Test limiting the number of files."""
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": True,
            "limit": 3
        })
        
        iterator = FileIterator(self.config)
        iterator.load()
        
        # Should only return 3 files
        files = iterator.get_files()
        self.assertEqual(len(files), 3)
    
    def test_len(self):
        """Test len() support."""
        self.config.set_cli_args({
            "source_folder": self.temp_dir,
            "recursive": False
        })
        
        iterator = FileIterator(self.config)
        
        # len() should return the number of files
        self.assertEqual(len(iterator), 5)


if __name__ == "__main__":
    unittest.main()