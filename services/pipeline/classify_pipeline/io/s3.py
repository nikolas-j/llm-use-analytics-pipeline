"""
AWS S3 implementation of StorageIO.

Uses boto3 to interact with S3, providing streaming reads and writes.
All operations use the S3-style key paths directly without transformation.
"""

import json
from typing import Iterator, Any

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception

from .base import StorageIO, ObjectRef


class S3IO(StorageIO):
    """AWS S3 storage implementation."""

    def __init__(self, bucket: str, region: str = "us-east-1"):
        """Initialize S3 storage.
        
        Args:
            bucket: S3 bucket name
            region: AWS region
            
        Raises:
            ImportError: If boto3 is not installed
        """
        if boto3 is None:
            raise ImportError(
                "boto3 is required for S3IO. Install with: pip install boto3"
            )
        
        self.bucket = bucket
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)

    def list_objects(self, prefix: str) -> list[ObjectRef]:
        """List all objects matching the prefix in S3.
        
        Args:
            prefix: Key prefix (e.g., "landing/date=2026-01-03/")
            
        Returns:
            List of ObjectRef instances for matching S3 objects
        """
        objects = []
        paginator = self.s3_client.get_paginator('list_objects_v2')
        
        try:
            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    objects.append(ObjectRef(
                        key=obj['Key'],
                        size=obj['Size'],
                        last_modified=obj['LastModified'].isoformat() if 'LastModified' in obj else None
                    ))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                raise ValueError(f"S3 bucket '{self.bucket}' does not exist")
            raise
        
        return sorted(objects, key=lambda x: x.key)

    def open_text(self, key: str) -> Iterator[str]:
        """Stream text content line by line from S3.
        
        Args:
            key: S3 object key to read
            
        Yields:
            Text lines from the S3 object
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            # Stream lines from the body
            for line in response['Body'].iter_lines():
                yield line.decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"S3 object '{key}' not found in bucket '{self.bucket}'")
            raise

    def write_json(self, key: str, data: Any) -> None:
        """Write data as JSON to S3.
        
        Args:
            key: Destination S3 key
            data: Python object to serialize as JSON
        """
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json_str.encode('utf-8'),
            ContentType='application/json'
        )

    def write_text_lines(self, key: str, lines: list[str]) -> None:
        """Write text lines to S3.
        
        Args:
            key: Destination S3 key
            lines: List of text lines to write
        """
        content = ''.join(
            line if line.endswith('\n') else line + '\n'
            for line in lines
        )
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content.encode('utf-8'),
            ContentType='text/plain'
        )

    def exists(self, key: str) -> bool:
        """Check if an object exists in S3.
        
        Args:
            key: S3 object key to check
            
        Returns:
            True if the object exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise
