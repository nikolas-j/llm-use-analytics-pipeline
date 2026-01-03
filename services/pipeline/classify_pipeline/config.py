"""Configuration management for the LLM classification pipeline."""

import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageType(str, Enum):
    """Supported storage backends."""

    LOCAL = "local"
    S3 = "s3"


class PipelineConfig(BaseSettings):
    """
    Pipeline configuration loaded from environment variables or .env file.
    
    Priority order:
    1. Explicit environment variables
    2. .env file in services/pipeline/
    3. Default values
    
    Example .env file:
        STORAGE=local
        BASE_PATH=../../local_data_IO
        DATE=2026-01-03
        WRITE_SANITIZED=false
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env
    )

    # Storage configuration
    storage: StorageType = Field(
        default=StorageType.LOCAL,
        description="Storage backend: local or s3",
    )

    # Date to process
    date: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="Date to process in YYYY-MM-DD format",
    )

    # Local storage configuration
    base_path: str = Field(
        default="../../local_data_IO",
        description="Base directory for local storage (relative to services/pipeline)",
    )

    # S3 configuration
    s3_bucket: Optional[str] = Field(
        default=None,
        description="S3 bucket name (required when storage=s3)",
    )
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for S3",
    )

    # Pipeline options
    write_sanitized: bool = Field(
        default=False,
        description="Write sanitized events to storage",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR",
    )

    def validate_s3_config(self) -> None:
        """Validate S3-specific configuration."""
        if self.storage == StorageType.S3 and not self.s3_bucket:
            raise ValueError("S3_BUCKET is required when STORAGE=s3")

    def __repr__(self) -> str:
        """Safe repr that doesn't expose AWS credentials."""
        if self.storage == StorageType.S3:
            return (
                f"PipelineConfig(storage={self.storage.value}, "
                f"date={self.date}, "
                f"s3_bucket={self.s3_bucket}, "
                f"aws_region={self.aws_region})"
            )
        return (
            f"PipelineConfig(storage={self.storage.value}, "
            f"date={self.date}, "
            f"base_path={self.base_path})"
        )


def load_config() -> PipelineConfig:
    """
    Load pipeline configuration from environment variables or .env file.
    
    Returns:
        PipelineConfig instance with settings from:
        1. Environment variables (highest priority)
        2. .env file in services/pipeline/
        3. Default values (lowest priority)
        
    Raises:
        ValueError: If S3 is selected but S3_BUCKET is not provided
    """
    config = PipelineConfig()
    config.validate_s3_config()
    return config
