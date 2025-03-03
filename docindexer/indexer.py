"""Document indexing functionality."""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .config import Configuration
from .file_iterator import FileIterator, FileInfo


class DocIndexer:
    """Document indexing class."""

    def __init__(self, output_path: Optional[str] = None, config: Optional[Configuration] = None):
        """Initialize the indexer.

        Args:
            output_path: Path to save the index file
            config: Configuration object for file discovery
        """
        self.output_path = output_path
        self.config = config or Configuration()
        self.index: Dict[str, Dict] = {}

    def index_directory(self, path: Union[str, Path], recursive: bool = False, **kwargs) -> Dict:
        """Index documents in a directory.

        Args:
            path: Directory path to index
            recursive: Whether to index subdirectories
            **kwargs: Additional options for file discovery and filtering

        Returns:
            Dictionary containing the document index
        """
        # Update configuration with method parameters
        config_updates = {'source_folder': str(path), 'recursive': recursive}
        config_updates.update(kwargs)
        self.config.set_cli_args(config_updates)
        
        # Use FileIterator to discover and filter files
        file_iterator = FileIterator(self.config)
        
        # Clear existing index
        self.index = {}
        
        # Process files using the iterator
        for file_info in file_iterator:
            self._index_file(file_info)
        
        # Save index if output path is provided
        if self.output_path:
            self._save_index()

        return self.index

    def _index_file(self, file_info: FileInfo) -> None:
        """Index a single file.

        Args:
            file_info: FileInfo object containing file metadata
        """
        file_path = file_info.path
        
        file_data = {
            "path": file_info.absolute_path,
            "size": file_info.size,
            "modified": file_info.modified,
            "extension": file_info.extension,
        }

        # Add file to index
        self.index[str(file_path)] = file_data

    def _save_index(self) -> None:
        """Save the index to a file."""
        if not self.output_path:
            return

        with open(self.output_path, 'w') as f:
            json.dump(self.index, f, indent=2)