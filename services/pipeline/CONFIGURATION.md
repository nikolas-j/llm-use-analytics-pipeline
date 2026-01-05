# Configuration

## Overview

Configuration is loaded via **Pydantic Settings** from `.env` file and environment variables. Priority: environment variables > `.env` file > defaults in `config.py`.

**Files:**
- `services/pipeline/.env` - Your active config (git-ignored)
- `services/pipeline/.env.example` - Template with all options
- `services/pipeline/requirements.txt` - Deployment dependencies (boto3, pydantic-settings, etc.)
- `services/pipeline/pyproject.toml` - Pytest configuration only (not deployment)

**No code changes needed between local/dev/ECS deployment.**

## LLM Classification

```bash
# Enable LLM (makes Bedrock API calls)
LLM_CLASSIFICATION=true
BEDROCK_REGION=eu-north-1
BEDROCK_MODEL_ID=eu.amazon.nova-micro-v1:0

# Disable LLM (bypass mode, returns "Unclassified", zero cost)
LLM_CLASSIFICATION=false
```

**Use bypass mode for:**
- Testing pipeline without AWS costs
- CI/CD without credentials
- Developing non-LLM components

## Storage Configuration

```bash
# Local filesystem
STORAGE=local
BASE_PATH=../../local_data_IO

# S3 (requires S3_BUCKET)
STORAGE=s3
S3_BUCKET=my-bucket
AWS_REGION=eu-north-1
```

## Core Settings

```bash
DATE=2026-01-03              # Date partition to process
WRITE_SANITIZED=false        # Write sanitized events (optional)
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
```

## AWS Credentials & IAM

**Local testing:**
- Run `aws configure` or set `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
- Enable model access in AWS Console: Bedrock → Model access (eu-north-1)

**Required IAM permissions:**

Add extra safety with more strict least priviledge.

```json
{
  "Action": ["bedrock:InvokeModel"],
  "Resource": "arn:aws:bedrock:eu-north-1::my-model-here"
}
```

For S3 storage, also add:
```json
{
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::my-bucket/*"
}
```

## Performance Tuning

```bash
BEDROCK_CONNECT_TIMEOUT=2    # Connection timeout (seconds)
BEDROCK_READ_TIMEOUT=5       # Read timeout (seconds)
BEDROCK_MAX_RETRIES=2        # Retry attempts
```

## Code Usage

```python
from classify_pipeline.config import load_config

config = load_config()

if config.llm_classification:
    print(f"Using Bedrock: {config.bedrock_model_id}")
else:
    print("Bypass mode enabled")
```

## Docker & Containers

**Pydantic Settings reads environment variables automatically** - no `.env` file needed in containers.

**Priority:** Environment variables (container runtime) > `.env` file (if exists) > defaults (code)

**Docker run:**
```bash
docker build -t llm-classifier .
docker run -e STORAGE=s3 -e S3_BUCKET=my-bucket -e DATE=2026-01-03 llm-classifier
```

**All config via `-e` flags** - `.env` file is excluded from Docker image (see `.dockerignore`).

## ECS/Fargate Deployment

Set environment variables in ECS task definition:

```json
{
  "environment": [
    {"name": "STORAGE", "value": "s3"},
    {"name": "S3_BUCKET", "value": "prod-bucket"},
    {"name": "AWS_REGION", "value": "eu-north-1"},
    {"name": "DATE", "value": "2026-01-03"},
    {"name": "LLM_CLASSIFICATION", "value": "true"},
    {"name": "BEDROCK_REGION", "value": "eu-north-1"},
    {"name": "BEDROCK_MODEL_ID", "value": "eu.amazon.nova-micro-v1:0"}
  ],
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/LLMTaskRole"
}
```

IAM task role provides AWS credentials automatically - no `AWS_ACCESS_KEY_ID` needed.
