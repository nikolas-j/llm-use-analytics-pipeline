"""
Storage-agnostic IO interface.

This module defines the abstract interface for storage operations.
Implementations must provide methods for listing, reading, and writing objects
using S3-style key paths, allowing the core pipeline logic to remain storage-agnostic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Any


@dataclass
class ObjectRef:
    """Reference to a storage object with metadata."""
    key: str
    size: int = 0
    last_modified: str | None = None


class StorageIO(ABC):
    """Abstract interface for storage operations.
    
    Implementations must support S3-style key paths:
    - landing/date=YYYY-MM-DD/*.jsonl
    - sanitized/date=YYYY-MM-DD/shard=NN/messages.jsonl
    - curated/metrics_daily/date=YYYY-MM-DD/metrics.json
    - reports/date=YYYY-MM-DD/run_latest.json
    """

    @abstractmethod
    def list_objects(self, prefix: str) -> list[ObjectRef]:
        """List all objects with the given prefix.
        
        Args:
            prefix: Key prefix to filter objects (e.g., "landing/date=2026-01-03/")
            
        Returns:
            List of ObjectRef instances matching the prefix
        """
        pass

    @abstractmethod
    def open_text(self, key: str) -> Iterator[str]:
        """Stream text content line by line.
        
        Args:
            key: Object key to read
            
        Yields:
            Text lines from the object
        """
        pass

    @abstractmethod
    def write_json(self, key: str, data: Any) -> None:
        """Write data as JSON to the specified key.
        
        Args:
            key: Destination key
            data: Python object to serialize as JSON
        """
        pass

    @abstractmethod
    def write_text_lines(self, key: str, lines: list[str]) -> None:
        """Write text lines to the specified key.
        
        Args:
            key: Destination key
            lines: List of text lines to write
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if an object exists at the given key.
        
        Args:
            key: Object key to check
            
        Returns:
            True if the object exists, False otherwise
        """
        pass
