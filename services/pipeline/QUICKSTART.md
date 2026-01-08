# Quick Start

## Installation

```bash
cd services/pipeline
pip install -r requirements.txt
cp .env.example .env
```

## Local Run (No AWS)

**Fastest way - bypass LLM:**
```bash
# Edit .env:
LLM_CLASSIFICATION=false
STORAGE=local
DATE=2026-01-03

# Run pipeline
python -m classify_pipeline.main
```

**Expected output:**
```
INFO - Found 1 input file(s)
INFO - Parsed 5 valid events
INFO - Assembled 2 conversations
INFO - Classified 2 conversations (bypass mode)
INFO - Pipeline completed in 0.5s
```

**Results:**
- `local_data_IO/curated/metrics_daily/date=2026-01-03/metrics.json`
- `local_data_IO/reports/date=2026-01-03/run_latest.json`

## Local Run with LLM

**Requires AWS credentials:**
```bash
aws configure
```

**Edit .env:**
```bash
LLM_CLASSIFICATION=true
BEDROCK_REGION=eu-north-1
BEDROCK_MODEL_ID=eu.amazon.nova-micro-v1:0
STORAGE=local
```

**Enable model access:**
- AWS Console → Bedrock → Model access (eu-north-1) → Enable Amazon Nova Micro

**Run:**
```bash
python -m classify_pipeline.main
```

## S3 Storage

**Edit .env:**
```bash
STORAGE=s3
S3_BUCKET=my-bucket
AWS_REGION=eu-north-1
```

**IAM permissions needed:**
```json
{
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::my-bucket/*"
}
```

## Docker Run

**Build:**
```bash
cd services/pipeline
docker build -t llm-classifier .
```

**Run bypass mode with S3 (requires AWS credentials):**
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

**Run with AWS S3 (requires AWS credentials):**

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

**Note:** Docker deployments **must use `STORAGE=s3`**. Local storage writes to container filesystem and data is lost when container stops.

**Environment variables are passed via `-e` flags** - no `.env` file needed in container.

## AWS Credentials (CLI)

```bash
# Option 1: Configure AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

For ECS deployment, use IAM task role (no credentials needed in container).

## Run Tests

```bash
# Fast tests (no AWS) - 37 tests in ~4s
pytest -m "not integration"

# All tests (requires AWS credentials) - 48 tests in ~26s
pytest
```

## Troubleshooting

**"No input files found"**
→ Check `landing/date=YYYY-MM-DD/` exists with `.jsonl` files

**"AccessDeniedException" (Bedrock)**
→ Run `aws configure` or enable model access in console

**"BEDROCK_REGION is required"**
→ Set `LLM_CLASSIFICATION=true` and `BEDROCK_REGION=eu-north-1` in `.env`

**Invalid events**
→ Check JSONL format and required fields in run report

## Common Commands

```bash
# Run with different date
DATE=2026-01-04 python -m classify_pipeline.main

# Debug logging
LOG_LEVEL=DEBUG python -m classify_pipeline.main

# Enable sanitized output
WRITE_SANITIZED=true python -m classify_pipeline.main
```

## Run on AWS ECS Fargate

**1. Build and push to ECR:**
```bash
docker build -t llm-classifier .
# Tag and push to your ECR repository
```

**2. Create ECS task definition:**
- Use the container image from ECR
- Set environment variables (STORAGE=s3, S3_BUCKET, AWS_REGION, DATE, etc.)
- Configure memory (recommended: 2 GB) and CPU (0.5 vCPU or higher)

**3. Configure IAM task role:**
- S3 read/write access to your data bucket
- Bedrock invoke model access (if using LLM_CLASSIFICATION=true)
- ECS task execution role for pulling images from ECR

**4. Run task via CLI:**
```bash
aws ecs run-task \
  --region eu-north-1 \
  --cluster YOUR_CLUSTER_NAME \
  --launch-type FARGATE \
  --task-definition bedrock-classifier-task:1 \
  --count 1 \
  --network-configuration "awsvpcConfiguration={subnets=[YOUR_SUBNET],securityGroups=[YOUR_SG],assignPublicIp=ENABLED}"
```

**Or use the shell script:**
```bash
chmod +x run_pipeline_job.sh
./run_pipeline_job.sh
```
