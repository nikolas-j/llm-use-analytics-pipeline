# Docker

## Build

```bash
cd services/pipeline
docker build -t llm-classifier .
```

## Run with LLM Bypass

```bash
docker run \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e STORAGE=s3 \
  -e S3_BUCKET=my-bucket \
  -e AWS_REGION=eu-north-1 \
  -e DATE=2026-01-03 \
  -e LLM_CLASSIFICATION=false \
  llm-classifier
```

## Run with LLM Enabled

```bash
docker run \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
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

**Note:** Docker requires `STORAGE=s3`. Pydantic Settings reads environment variables via `-e` flags - no `.env` file needed.

## ECS Deployment

*(Implementation TBD)*
