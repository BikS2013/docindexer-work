"""File iteration functionality for DocIndexer."""

import os
import fnmatch
import re
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Set, Iterator, Pattern, Union, Callable, Any, Iterable
from dataclasses import dataclass
from enum import Enum, auto
import logging
from functools import lru_cache
from abc import ABC, abstractmethod

from .config import Configuration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SortOrder(Enum):
    """Enumeration for file sorting options."""
    NAME_ASC = auto()
    NAME_DESC = auto()
    DATE_ASC = auto()
    DATE_DESC = auto()
    SIZE_ASC = auto()
    SIZE_DESC = auto()
    RANDOM = auto()
    NONE = auto()


@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    size: int
    modified: float
    extension: str
    
    @property
    def name(self) -> str:
        """Get the file name."""
        return self.path.name
    
    @property
    def absolute_path(self) -> str:
        """Get the absolute path as a string."""
        return str(self.path.absolute())
    
    @classmethod
    def from_path(cls, path: Path) -> 'FileInfo':
        """Create a FileInfo instance from a Path object.
        
        Args:
            path: Path to the file
            
        Returns:
            FileInfo object containing file details
        """
        stat = path.stat()
        return cls(
            path=path,
            size=stat.st_size,
            modified=stat.st_mtime,
            extension=path.suffix.lower(),
        )


class FileFilter(ABC):
    """Abstract base class for file filters."""
    
    @abstractmethod
    def matches(self, file_info: FileInfo) -> bool:
        """Check if a file matches the filter.
        
        Args:
            file_info: FileInfo object to check
            
        Returns:
            True if the file matches, False otherwise
        """
        pass


class ExtensionFilter(FileFilter):
    """Filter files by extension."""
    
    def __init__(self, extensions: List[str]):
        """Initialize an extension filter.
        
        Args:
            extensions: List of allowed file extensions (with or without dots)
        """
        self.extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions]
    
    def matches(self, file_info: FileInfo) -> bool:
        """Check if a file's extension matches the allowed extensions.
        
        Args:
            file_info: FileInfo object to check
            
        Returns:
            True if the file's extension is in the allowed list, False otherwise
        """
        return file_info.extension in self.extensions


class PatternFilter(FileFilter):
    """Filter files by name pattern."""
    
    def __init__(self, pattern: str, glob: bool = True):
        """Initialize a pattern filter.
        
        Args:
            pattern: Pattern to match against file names
            glob: Whether to use glob pattern matching (True) or regex (False)
        """
        self.pattern = pattern
        self.glob = glob
        if not glob:
            self.regex = re.compile(pattern)
    
    def matches(self, file_info: FileInfo) -> bool:
        """Check if a file's name matches the pattern.
        
        Args:
            file_info: FileInfo object to check
            
        Returns:
            True if the file's name matches the pattern, False otherwise
        """
        if self.glob:
            return fnmatch.fnmatch(file_info.name, self.pattern)
        else:
            return bool(self.regex.search(file_info.name))


class SizeFilter(FileFilter):
    """Filter files by size."""
    
    def __init__(self, min_size: Optional[int] = None, max_size: Optional[int] = None):
        """Initialize a size filter.
        
        Args:
            min_size: Minimum file size in bytes (inclusive)
            max_size: Maximum file size in bytes (inclusive)
        """
        self.min_size = min_size
        self.max_size = max_size
    
    def matches(self, file_info: FileInfo) -> bool:
        """Check if a file's size is within the specified range.
        
        Args:
            file_info: FileInfo object to check
            
        Returns:
            True if the file's size is within range, False otherwise
        """
        if self.min_size is not None and file_info.size < self.min_size:
            return False
        if self.max_size is not None and file_info.size > self.max_size:
            return False
        return True


class DateFilter(FileFilter):
    """Filter files by modification date."""
    
    def __init__(self, min_date: Optional[float] = None, max_date: Optional[float] = None):
        """Initialize a date filter.
        
        Args:
            min_date: Minimum modification time as Unix timestamp (inclusive)
            max_date: Maximum modification time as Unix timestamp (inclusive)
        """
        self.min_date = min_date
        self.max_date = max_date
    
    def matches(self, file_info: FileInfo) -> bool:
        """Check if a file's modification date is within the specified range.
        
        Args:
            file_info: FileInfo object to check
            
        Returns:
            True if the file's modification date is within range, False otherwise
        """
        if self.min_date is not None and file_info.modified < self.min_date:
            return False
        if self.max_date is not None and file_info.modified > self.max_date:
            return False
        return True


class CompositeFilter(FileFilter):
    """Compose multiple filters with AND logic."""
    
    def __init__(self, filters: List[FileFilter]):
        """Initialize a composite filter.
        
        Args:
            filters: List of filters to apply
        """
        self.filters = filters
    
    def matches(self, file_info: FileInfo) -> bool:
        """Check if a file matches all filters.
        
        Args:
            file_info: FileInfo object to check
            
        Returns:
            True if the file matches all filters, False otherwise
        """
        return all(f.matches(file_info) for f in self.filters)


class FileIterator:
    """Iterator for files based on configuration parameters."""
    
    def __init__(self, config: Configuration):
        """Initialize a file iterator with configuration.
        
        Args:
            config: Configuration object with file discovery settings
        """
        self.config = config
        self.file_filter = self._create_filter()
        self._files: List[FileInfo] = []
        self._index = 0
        self._loaded = False
        self._include_hidden = self.config.get('include_hidden', False)
    
    def _create_filter(self) -> FileFilter:
        """Create a composite filter based on configuration parameters.
        
        Returns:
            FileFilter to apply to files
        """
        filters = []
        
        # Add extension filter if specified
        supported_extensions = [
            '.txt', '.md', '.pdf', '.docx', '.doc',
            '.html', '.htm', '.xml', '.json'
        ]
        filters.append(ExtensionFilter(supported_extensions))
        
        # Add pattern filter if specified
        pattern = self.config.get('pattern')
        if pattern:
            use_regex = self.config.get('use_regex', False)
            filters.append(PatternFilter(pattern, glob=not use_regex))
        
        # Add size filter if specified
        min_size = self.config.get('min_size')
        max_size = self.config.get('max_size')
        if min_size is not None or max_size is not None:
            filters.append(SizeFilter(min_size, max_size))
        
        # Add date filter if specified
        min_date = self.config.get('min_date')
        max_date = self.config.get('max_date')
        if min_date is not None or max_date is not None:
            filters.append(DateFilter(min_date, max_date))
        
        return CompositeFilter(filters)
    
    def _get_sort_key(self) -> Callable[[FileInfo], Any]:
        """Get a sort key function based on configuration.
        
        Returns:
            Function to use as key for sorting
        """
        sort_order = self._get_sort_order()
        
        if sort_order == SortOrder.NAME_ASC:
            return lambda f: f.name
        elif sort_order == SortOrder.NAME_DESC:
            return lambda f: f.name
        elif sort_order == SortOrder.DATE_ASC:
            return lambda f: f.modified
        elif sort_order == SortOrder.DATE_DESC:
            return lambda f: f.modified
        elif sort_order == SortOrder.SIZE_ASC:
            return lambda f: f.size
        elif sort_order == SortOrder.SIZE_DESC:
            return lambda f: f.size
        else:  # Default or NONE
            return lambda f: f.path
    
    def _get_sort_order(self) -> SortOrder:
        """Determine sort order from configuration.
        
        Returns:
            SortOrder enum value
        """
        if self.config.get('random', False):
            return SortOrder.RANDOM
        
        sort_by = self.config.get('sort_by', 'name').lower()
        sort_desc = self.config.get('sort_desc', False)
        
        if sort_by == 'name':
            return SortOrder.NAME_DESC if sort_desc else SortOrder.NAME_ASC
        elif sort_by == 'date':
            return SortOrder.DATE_DESC if sort_desc else SortOrder.DATE_ASC
        elif sort_by == 'size':
            return SortOrder.SIZE_DESC if sort_desc else SortOrder.SIZE_ASC
        else:
            return SortOrder.NONE
    
    def _discover_files(self) -> None:
        """Discover files based on configuration parameters."""
        self._files = []
        
        # Check if we have a catalogue file
        catalogue_path = self.config.get('catalogue')
        if catalogue_path:
            self._load_from_catalogue(catalogue_path)
            return
        
        # Check if we have a single file
        file_name = self.config.get('file_name')
        if file_name:
            path = Path(file_name)
            if path.exists() and path.is_file():
                file_info = FileInfo.from_path(path)
                if self.file_filter.matches(file_info):
                    self._files.append(file_info)
            else:
                logger.warning(f"File not found: {file_name}")
            return
        
        # Default: process files in a directory
        source_folder = self.config.get('source_folder', '.')
        recursive = self.config.get('recursive', True)
        max_depth = self.config.get('max_depth')
        
        self._scan_directory(Path(source_folder), recursive, max_depth=max_depth)
    
    def _load_from_catalogue(self, catalogue_path: str) -> None:
        """Load files from a catalogue JSON file.
        
        Args:
            catalogue_path: Path to the catalogue file
        """
        try:
            with open(catalogue_path, 'r') as f:
                catalogue = json.load(f)
            
            # Process file entries in the catalogue
            for entry in catalogue.get('files', []):
                if isinstance(entry, str):
                    # Simple string path entry
                    path = Path(entry)
                    if path.exists() and path.is_file():
                        file_info = FileInfo.from_path(path)
                        if self.file_filter.matches(file_info):
                            self._files.append(file_info)
                elif isinstance(entry, dict) and 'path' in entry:
                    # Dictionary entry with path key
                    path = Path(entry['path'])
                    if path.exists() and path.is_file():
                        # Use provided metadata if available, otherwise get from path
                        if all(k in entry for k in ['size', 'modified', 'extension']):
                            file_info = FileInfo(
                                path=path,
                                size=entry['size'],
                                modified=entry['modified'],
                                extension=entry['extension'],
                            )
                        else:
                            file_info = FileInfo.from_path(path)
                            
                        if self.file_filter.matches(file_info):
                            self._files.append(file_info)
                        
            logger.info(f"Loaded {len(self._files)} files from catalogue: {catalogue_path}")
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error loading catalogue file: {str(e)}")
    
    def _scan_directory(self, directory: Path, recursive: bool, 
                        current_depth: int = 0, max_depth: Optional[int] = None) -> None:
        """Scan a directory for files recursively.
        
        Args:
            directory: Directory path to scan
            recursive: Whether to scan subdirectories
            current_depth: Current recursion depth
            max_depth: Maximum recursion depth (None for unlimited)
        """
        if not directory.exists():
            logger.warning(f"Directory not found: {directory}")
            return
        
        if not directory.is_dir():
            logger.warning(f"Not a directory: {directory}")
            return
            
        # Check max depth
        if max_depth is not None and current_depth > max_depth:
            return
        
        try:
            for item in directory.iterdir():
                # Skip hidden files/directories unless explicitly included
                if not self._include_hidden and item.name.startswith('.'):
                    continue
                    
                if item.is_file():
                    file_info = FileInfo.from_path(item)
                    if self.file_filter.matches(file_info):
                        self._files.append(file_info)
                elif recursive and item.is_dir():
                    self._scan_directory(item, recursive, current_depth + 1, max_depth)
        except (PermissionError, OSError) as e:
            logger.warning(f"Error accessing {directory}: {str(e)}")
    
    def load(self) -> None:
        """Discover and load files based on configuration."""
        if self._loaded:
            return
            
        self._discover_files()
        
        # Apply limit if specified
        limit = self.config.get('limit')
        if limit is not None and limit > 0 and limit < len(self._files):
            self._files = self._files[:limit]
        
        # Apply sorting
        sort_order = self._get_sort_order()
        if sort_order == SortOrder.RANDOM:
            random.shuffle(self._files)
        else:
            sort_key = self._get_sort_key()
            reverse = sort_order in [SortOrder.NAME_DESC, SortOrder.DATE_DESC, SortOrder.SIZE_DESC]
            self._files.sort(key=sort_key, reverse=reverse)
        
        self._loaded = True
        self._index = 0
    
    def reset(self) -> None:
        """Reset the iterator."""
        self._loaded = False
        self._files = []
        self._index = 0
    
    def __iter__(self) -> 'FileIterator':
        """Get an iterator over the files.
        
        Returns:
            Self as iterator
        """
        if not self._loaded:
            self.load()
        self._index = 0
        return self
    
    def __next__(self) -> FileInfo:
        """Get the next file.
        
        Returns:
            Next FileInfo object
            
        Raises:
            StopIteration: When no more files are available
        """
        if not self._loaded:
            self.load()
            
        if self._index >= len(self._files):
            raise StopIteration
            
        file_info = self._files[self._index]
        self._index += 1
        return file_info
    
    def get_files(self) -> List[FileInfo]:
        """Get all files as a list.
        
        Returns:
            List of FileInfo objects
        """
        if not self._loaded:
            self.load()
        return self._files.copy()
    
    def count(self) -> int:
        """Get the number of files.
        
        Returns:
            Number of files
        """
        if not self._loaded:
            self.load()
        return len(self._files)
    
    def __len__(self) -> int:
        """Get the number of files.
        
        Returns:
            Number of files
        """
        return self.count()


class CatalogueBuilder:
    """Builder for creating file catalogues."""
    
    def __init__(self, output_path: str):
        """Initialize a catalogue builder.
        
        Args:
            output_path: Path to save the catalogue file
        """
        self.output_path = output_path
        self.files: List[Dict[str, Any]] = []
    
    def add_file(self, file_info: FileInfo) -> None:
        """Add a file to the catalogue.
        
        Args:
            file_info: FileInfo object to add
        """
        self.files.append({
            "path": file_info.absolute_path,
            "size": file_info.size,
            "modified": file_info.modified,
            "extension": file_info.extension,
        })
    
    def add_files(self, file_iterator: FileIterator) -> None:
        """Add all files from a FileIterator to the catalogue.
        
        Args:
            file_iterator: FileIterator containing files to add
        """
        for file_info in file_iterator:
            self.add_file(file_info)
    
    def save(self) -> None:
        """Save the catalogue to a file."""
        catalogue = {
            "files": self.files
        }
        
        with open(self.output_path, 'w') as f:
            json.dump(catalogue, f, indent=2)
        
        logger.info(f"Saved catalogue with {len(self.files)} files to {self.output_path}")