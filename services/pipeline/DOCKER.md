# Docker Deployment

## Environment Variables for Containerized Deployment

**Pydantic Settings reads environment variables automatically** - `.env` file is NOT needed in the container.

### Docker Run

```bash
docker build -t llm-classifier .

docker run -e STORAGE=local \
  -e DATE=2026-01-03 \
  -e BASE_PATH=/data \
  -e LLM_CLASSIFICATION=false \
  llm-classifier
```

For AWS credentials:
```bash
docker run -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e STORAGE=s3 \
  -e S3_BUCKET=my-bucket \
  -e AWS_REGION=eu-north-1 \
  -e DATE=2026-01-03 \
  -e LLM_CLASSIFICATION=true \
  -e BEDROCK_REGION=eu-north-1 \
  -e BEDROCK_MODEL_ID=eu.amazon.nova-micro-v1:0 \
  llm-classifier
```

Or use `--env-file`:
```bash
# Create env.prod file with production settings (don't commit!)
docker run --env-file env.prod llm-classifier
```

### ECS Fargate

In ECS task definition, set environment variables:

```json
{
  "containerDefinitions": [{
    "name": "llm-classifier",
    "image": "123456789.dkr.ecr.eu-north-1.amazonaws.com/llm-classifier:latest",
    "environment": [
      {"name": "STORAGE", "value": "s3"},
      {"name": "S3_BUCKET", "value": "prod-llm-data"},
      {"name": "AWS_REGION", "value": "eu-north-1"},
      {"name": "DATE", "value": "2026-01-03"},
      {"name": "LLM_CLASSIFICATION", "value": "true"},
      {"name": "BEDROCK_REGION", "value": "eu-north-1"},
      {"name": "BEDROCK_MODEL_ID", "value": "eu.amazon.nova-micro-v1:0"}
    ],
    "taskRoleArn": "arn:aws:iam::ACCOUNT:role/LLMClassifierTaskRole"
  }]
}
```

**IAM Task Role** handles AWS credentials automatically - no need for `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`.

### How Pydantic Settings Works

```python
# classify_pipeline/config.py
class PipelineConfig(BaseSettings):
    storage: str = "local"
    llm_classification: bool = True
    # ... other fields
    
    model_config = SettingsConfigDict(
        env_file=".env",  # Optional, only if file exists
        case_sensitive=False
    )
```

**Priority:**
1. Environment variables (passed to container)
2. `.env` file (if exists in container - NOT recommended)
3. Defaults in code

**For containers, use environment variables only** - don't bake `.env` into the image.

## Build & Push

```bash
# Build
docker build -t llm-classifier .

# Tag for ECR
docker tag llm-classifier:latest 123456789.dkr.ecr.eu-north-1.amazonaws.com/llm-classifier:latest

# Push to ECR
aws ecr get-login-password --region eu-north-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.eu-north-1.amazonaws.com
docker push 123456789.dkr.ecr.eu-north-1.amazonaws.com/llm-classifier:latest
```
