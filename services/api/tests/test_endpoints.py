import pytest
import json
from unittest.mock import Mock, patch
from fastapi import HTTPException

from app.endpoints.v1.endpoints import fetch_s3_json, get_metrics, get_reports
from app.schemas import DateQuery


class TestFetchS3Json:
    """Unit tests for fetch_s3_json function."""
    
    def test_fetch_s3_json_success(self):
        """Test successful S3 JSON fetch."""
        mock_client = Mock()
        mock_client.get_object.return_value = {
            "Body": Mock(read=lambda: b'{"key": "value"}')
        }
        
        result = fetch_s3_json(mock_client, "test-bucket", "test-key.json")
        
        assert result == {"key": "value"}
        mock_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test-key.json"
        )
    
    def test_fetch_s3_json_not_found(self):
        """Test S3 file not found error."""
        mock_client = Mock()
        error_response = {"Error": {"Code": "NoSuchKey"}}
        mock_client.get_object.side_effect = Exception("NoSuchKey")
        
        from botocore.exceptions import ClientError
        mock_client.get_object.side_effect = ClientError(
            error_response, "GetObject"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            fetch_s3_json(mock_client, "test-bucket", "missing.json")
        
        assert exc_info.value.status_code == 404


class TestDateQuery:
    """Unit tests for DateQuery schema."""
    
    def test_valid_date(self):
        """Test valid date format."""
        query = DateQuery(date="2026-01-03")
        assert query.date == "2026-01-03"
    
    def test_invalid_date_format(self):
        """Test invalid date format."""
        with pytest.raises(ValueError):
            DateQuery(date="01-03-2026")
    
    def test_invalid_date_value(self):
        """Test invalid date value."""
        with pytest.raises(ValueError):
            DateQuery(date="2026-13-45")
