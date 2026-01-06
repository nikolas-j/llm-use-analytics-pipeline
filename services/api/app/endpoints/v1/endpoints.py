from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any
import json
from botocore.exceptions import ClientError

from app.config import Settings, get_settings
from app.schemas import DateQuery

router = APIRouter()


def get_s3_client(settings: Settings = Depends(get_settings)):
    """Create and return S3 client with configuration from settings."""
    import boto3
    
    session_kwargs = {"region_name": settings.aws_region}
    
    # Use explicit credentials if provided
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        session_kwargs.update({
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key
        })
    
    return boto3.client("s3", **session_kwargs)


def fetch_s3_json(
    s3_client, 
    bucket: str, 
    key: str
) -> Dict[str, Any]:
    """Fetch and parse JSON file from S3."""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        return json.loads(content)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            raise HTTPException(
                status_code=404,
                detail=f"File not found for the specified date: {key}"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving file from S3: {str(e)}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/metrics", response_class=JSONResponse)
async def get_metrics(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    settings: Settings = Depends(get_settings),
    s3_client = Depends(get_s3_client)
) -> Dict[str, Any]:
    """
    Retrieve daily metrics for a specific date.
    
    Args:
        date: Date string in YYYY-MM-DD format
        
    Returns:
        JSON metrics data for the specified date
    """
    # Validate date format
    date_query = DateQuery(date=date)
    
    # Construct S3 key
    s3_key = f"curated/metrics_daily/date={date_query.date}/metrics.json"
    
    # Fetch and return data
    return fetch_s3_json(s3_client, settings.aws_s3_bucket_name, s3_key)


@router.get("/reports", response_class=JSONResponse)
async def get_reports(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    settings: Settings = Depends(get_settings),
    s3_client = Depends(get_s3_client)
) -> Dict[str, Any]:
    """
    Retrieve daily reports for a specific date.
    
    Args:
        date: Date string in YYYY-MM-DD format
        
    Returns:
        JSON report data for the specified date
    """
    # Validate date format
    date_query = DateQuery(date=date)
    
    # Construct S3 key
    s3_key = f"reports/date={date_query.date}/run_latest.json"
    
    # Fetch and return data
    return fetch_s3_json(s3_client, settings.aws_s3_bucket_name, s3_key)
