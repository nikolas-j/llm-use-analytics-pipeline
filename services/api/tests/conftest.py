import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
import boto3
from moto import mock_aws

from app.main import app
from app.config import Settings


@pytest.fixture
def test_settings():
    """Provide test settings."""
    return Settings(
        aws_s3_bucket_name="test-bucket",
        aws_region="us-east-1",
        aws_access_key_id="test-key",
        aws_secret_access_key="test-secret"
    )


@pytest.fixture
def client():
    """Provide test client."""
    return TestClient(app)


@pytest.fixture
def mock_s3_client():
    """Provide mocked S3 client."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="test-bucket")
        yield s3
