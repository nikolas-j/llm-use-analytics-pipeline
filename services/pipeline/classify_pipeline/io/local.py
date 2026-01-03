"""
Local filesystem implementation of StorageIO.

Maps S3-style keys to local file paths under a configurable base directory.
Example: key "landing/date=2026-01-03/input.jsonl" -> {base_path}/landing/date=2026-01-03/input.jsonl
"""

import json
from pathlib import Path
from typing import Iterator, Any

from .base import StorageIO, ObjectRef


class LocalIO(StorageIO):
    """Local filesystem storage implementation."""

    def __init__(self, base_path: str):
        """Initialize local storage.
        
        Args:
            base_path: Root directory for all storage operations
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        """Convert S3-style key to local filesystem path.
        
        Args:
            key: S3-style key (e.g., "landing/date=2026-01-03/file.jsonl")
            
        Returns:
            Resolved absolute path
        """
        return self.base_path / key

    def list_objects(self, prefix: str) -> list[ObjectRef]:
        """List all objects matching the prefix.
        
        Args:
            prefix: Key prefix (e.g., "landing/date=2026-01-03/")
            
        Returns:
            List of ObjectRef instances for matching files
        """
        prefix_path = self._resolve_path(prefix)
        
        if not prefix_path.exists():
            return []
        
        objects = []
        if prefix_path.is_file():
            # Exact file match
            rel_path = prefix_path.relative_to(self.base_path)
            objects.append(ObjectRef(
                key=str(rel_path).replace("\\", "/"),
                size=prefix_path.stat().st_size,
                last_modified=None
            ))
        else:
            # Directory: glob all files recursively
            for file_path in prefix_path.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(self.base_path)
                    objects.append(ObjectRef(
                        key=str(rel_path).replace("\\", "/"),
                        size=file_path.stat().st_size,
                        last_modified=None
                    ))
        
        return sorted(objects, key=lambda x: x.key)

    def open_text(self, key: str) -> Iterator[str]:
        """Stream text content line by line.
        
        Args:
            key: Object key to read
            
        Yields:
            Text lines from the file
        """
        file_path = self._resolve_path(key)
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                yield line

    def write_json(self, key: str, data: Any) -> None:
        """Write data as JSON to the specified key.
        
        Args:
            key: Destination key
            data: Python object to serialize as JSON
        """
        file_path = self._resolve_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def write_text_lines(self, key: str, lines: list[str]) -> None:
        """Write text lines to the specified key.
        
        Args:
            key: Destination key
            lines: List of text lines to write
        """
        file_path = self._resolve_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line)
                if not line.endswith('\n'):
                    f.write('\n')

    def exists(self, key: str) -> bool:
        """Check if an object exists at the given key.
        
        Args:
            key: Object key to check
            
        Returns:
            True if the file exists, False otherwise
        """
        return self._resolve_path(key).exists()
