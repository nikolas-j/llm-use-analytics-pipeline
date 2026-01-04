"""
Configuration tests for pipeline settings.

Tests configuration loading, validation, and environment variable handling.
"""

import pytest
from unittest.mock import patch
from classify_pipeline.config import load_config, PipelineConfig


def test_config_default_values():
    """Test that config has sensible defaults."""
    with patch.dict('os.environ', {}, clear=True):
        config = PipelineConfig()
        
        # LLM defaults
        assert config.llm_classification is True
        assert config.bedrock_region == "eu-north-1"
        assert config.bedrock_model_id == "eu.amazon.nova-micro-v1:0"
        assert config.bedrock_connect_timeout == 2
        assert config.bedrock_read_timeout == 5
        assert config.bedrock_max_retries == 2


def test_config_llm_bypass_mode(monkeypatch):
    """Test LLM bypass mode configuration."""
    monkeypatch.setenv("LLM_CLASSIFICATION", "false")
    
    config = load_config()
    
    assert config.llm_classification is False


def test_config_llm_enabled_mode(monkeypatch):
    """Test LLM enabled mode configuration."""
    monkeypatch.setenv("LLM_CLASSIFICATION", "true")
    monkeypatch.setenv("BEDROCK_REGION", "us-east-1")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "us.amazon.nova-micro-v1:0")
    
    config = load_config()
    
    assert config.llm_classification is True
    assert config.bedrock_region == "us-east-1"
    assert config.bedrock_model_id == "us.amazon.nova-micro-v1:0"


def test_config_bedrock_validation_when_enabled(monkeypatch):
    """Test that Bedrock config is validated when LLM is enabled."""
    monkeypatch.setenv("LLM_CLASSIFICATION", "true")
    monkeypatch.setenv("BEDROCK_REGION", "")
    
    with pytest.raises(ValueError, match="BEDROCK_REGION is required"):
        load_config()


def test_config_bedrock_validation_skipped_when_disabled(monkeypatch):
    """Test that Bedrock validation is skipped when LLM is disabled."""
    monkeypatch.setenv("LLM_CLASSIFICATION", "false")
    monkeypatch.setenv("BEDROCK_REGION", "")  # Invalid but shouldn't matter
    
    # Should not raise error
    config = load_config()
    assert config.llm_classification is False


def test_config_custom_timeouts(monkeypatch):
    """Test custom Bedrock timeout configuration."""
    monkeypatch.setenv("BEDROCK_CONNECT_TIMEOUT", "5")
    monkeypatch.setenv("BEDROCK_READ_TIMEOUT", "10")
    monkeypatch.setenv("BEDROCK_MAX_RETRIES", "3")
    
    config = load_config()
    
    assert config.bedrock_connect_timeout == 5
    assert config.bedrock_read_timeout == 10
    assert config.bedrock_max_retries == 3


def test_config_storage_types(monkeypatch):
    """Test different storage configurations."""
    # Test local storage
    monkeypatch.setenv("STORAGE", "local")
    monkeypatch.setenv("BASE_PATH", "/tmp/data")
    
    config = load_config()
    assert config.storage.value == "local"
    assert config.base_path == "/tmp/data"
    
    # Test S3 storage
    monkeypatch.setenv("STORAGE", "s3")
    monkeypatch.setenv("S3_BUCKET", "my-bucket")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    
    config = load_config()
    assert config.storage.value == "s3"
    assert config.s3_bucket == "my-bucket"
    assert config.aws_region == "us-west-2"


def test_config_s3_validation(monkeypatch):
    """Test S3 configuration validation."""
    # Must explicitly set to empty string to override .env file
    monkeypatch.setenv("STORAGE", "s3")
    monkeypatch.setenv("S3_BUCKET", "")  # Empty bucket
    
    with pytest.raises(ValueError, match="S3_BUCKET is required"):
        load_config()


def test_config_case_insensitive(monkeypatch):
    """Test that environment variables are case-insensitive."""
    monkeypatch.setenv("llm_classification", "false")  # lowercase
    
    config = load_config()
    assert config.llm_classification is False
