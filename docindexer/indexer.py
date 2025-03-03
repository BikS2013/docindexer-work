"""Document indexing functionality."""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union


class DocIndexer:
    """Document indexing class."""

    def __init__(self, output_path: Optional[str] = None):
        """Initialize the indexer.

        Args:
            output_path: Path to save the index file
        """
        self.output_path = output_path
        self.index: Dict[str, Dict] = {}

    def index_directory(self, path: Union[str, Path], recursive: bool = False) -> Dict:
        """Index documents in a directory.

        Args:
            path: Directory path to index
            recursive: Whether to index subdirectories

        Returns:
            Dictionary containing the document index
        """
        path = Path(path)
        if not path.is_dir():
            raise ValueError(f"{path} is not a directory")

        # Process files in the directory
        for item in path.iterdir():
            if item.is_file():
                self._index_file(item)
            elif recursive and item.is_dir():
                self.index_directory(item, recursive=True)

        # Save index if output path is provided
        if self.output_path:
            self._save_index()

        return self.index

    def _index_file(self, file_path: Path) -> None:
        """Index a single file.

        Args:
            file_path: Path to the file to index
        """
        # Skip non-document files
        if not self._is_supported_doc(file_path):
            return

        file_info = {
            "path": str(file_path.absolute()),
            "size": file_path.stat().st_size,
            "modified": file_path.stat().st_mtime,
            "extension": file_path.suffix,
        }

        # Add file to index
        self.index[str(file_path)] = file_info

    def _save_index(self) -> None:
        """Save the index to a file."""
        if not self.output_path:
            return

        with open(self.output_path, 'w') as f:
            json.dump(self.index, f, indent=2)

    def _is_supported_doc(self, file_path: Path) -> bool:
        """Check if the file is a supported document type.

        Args:
            file_path: Path to the file

        Returns:
            True if the file is a supported document type
        """
        # List of supported document extensions
        supported_extensions = [
            '.txt', '.md', '.pdf', '.docx', '.doc',
            '.html', '.htm', '.xml', '.json'
        ]
        return file_path.suffix.lower() in supported_extensions