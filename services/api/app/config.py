from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with AWS S3 configuration."""
    
    # AWS S3 Configuration
    aws_s3_bucket_name: str
    aws_region: str = "eu-north-1"
    CORS_ALLOW_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
