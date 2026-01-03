#!/usr/bin/env python3
"""
Quick run script for the LLM Classification Pipeline.

Usage:
    python run.py                    # Run with defaults
    python run.py --date 2026-01-04  # Custom date
    python run.py --s3 my-bucket     # Use S3 backend
"""

import os
import sys
from argparse import ArgumentParser


def main():
    parser = ArgumentParser(description="Run LLM Classification Pipeline")
    parser.add_argument(
        "--storage",
        choices=["local", "s3"],
        default="local",
        help="Storage backend (default: local)"
    )
    parser.add_argument(
        "--date",
        default="2026-01-03",
        help="Processing date YYYY-MM-DD (default: 2026-01-03)"
    )
    parser.add_argument(
        "--base-path",
        default="../../local_data_IO",
        help="Local filesystem base path (default: ../../local_data_IO)"
    )
    parser.add_argument(
        "--s3-bucket",
        help="S3 bucket name (required if storage=s3)"
    )
    parser.add_argument(
        "--aws-region",
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )
    parser.add_argument(
        "--write-sanitized",
        action="store_true",
        help="Write sanitized events to storage"
    )
    
    args = parser.parse_args()
    
    # Validate
    if args.storage == "s3" and not args.s3_bucket:
        print("Error: --s3-bucket required when storage=s3", file=sys.stderr)
        sys.exit(1)
    
    # Set environment variables
    os.environ["STORAGE"] = args.storage
    os.environ["DATE"] = args.date
    os.environ["BASE_PATH"] = args.base_path
    os.environ["WRITE_SANITIZED"] = "true" if args.write_sanitized else "false"
    
    if args.s3_bucket:
        os.environ["S3_BUCKET"] = args.s3_bucket
    if args.aws_region:
        os.environ["AWS_REGION"] = args.aws_region
    
    # Import and run pipeline
    from classify_pipeline.main import run_pipeline
    
    print(f"Running pipeline with:")
    print(f"  Storage: {args.storage}")
    print(f"  Date: {args.date}")
    if args.storage == "local":
        print(f"  Base Path: {args.base_path}")
    else:
        print(f"  S3 Bucket: {args.s3_bucket}")
        print(f"  AWS Region: {args.aws_region}")
    print()
    
    exit_code = run_pipeline()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
