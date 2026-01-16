# LLM Use Analytics Pipeline

## Summary

**The Challenge:** Organizations deploying LLMs across teams lack visibility into adoption patterns, use cases, and potential data leakage. We wish to know the answer to: *Which teams are using AI? How are they using it? For what are they using it for?*

**The Solution:** A simple end-to-end analytics pipeline that transforms raw LLM conversation logs into task categories. These metrics can be used as a proxy for LLM integration across the enterprise, identify usage patterns by team and task category, and detect potential data leakage.

## What This Project Demonstrates

- **Cloud-Native ETL Architecture** - Serverless data processing on AWS using S3, ECS Fargate, and Lambda
- **LLM Integration & Inference** - Classification using AWS Bedrock
- **Data Engineering** - Event stream processing, conversation assembly, PII sanitization with custom regex patterns
- **MLOps Best Practices** - Containerized deployments, environment abstraction, testing, automated workflows
- **API Development** - RESTful data serving layer with FastAPI for analytics
- **Security-First Design** - Automated PII detection and redaction

## Architecture Overview

### Components

**1. Data Pipeline (`services/pipeline`)**
- Ingests JSONL conversation logs from S3 (`/landing/date=YYYY-MM-DD/`)
- Sanitizes sensitive information (emails, project names, URLs) with configurable regex patterns
- Assembles message events into complete conversations with team metadata
- Classifies conversations using AWS Bedrock LLM inference (Nova Micro model)
- Aggregates daily metrics by team and task category
- Outputs curated analytics to S3 (`/curated/metrics_daily/`)
- Generates execution reports with redaction statistics and performance metrics
- **Deployed as:** Dockerized batch job on AWS ECS Fargate

**2. REST API (`services/api`)**
- FastAPI service exposing classified data via HTTP endpoints
- `GET /v1/metrics?date=YYYY-MM-DD` - Daily team usage and classification metrics
- `GET /v1/reports?date=YYYY-MM-DD` - Pipeline execution reports
- **Deployed as:** AWS Lambda function with API Gateway trigger

**3. Frontend Demo (`llm-use-frontend`)**
- Simple web interface to demo pipeline results
- **Deployed as:** Static site on AWS CloudFront + S3

### Key Business Insights Delivered

- **Team-level LLM adoption rates** - Which departments are using AI tools
- **Task categorization** - Primary use cases (technical help, writing assistance, analysis, etc.)
- **Usage volume metrics** - Total conversations, turns, character counts per team
- **Security incidents** - PII leakage detection for targeted cybersecurity training
- **Trend analysis** - Daily/weekly adoption and usage patterns

## Technology Stack

**Cloud & Infrastructure:**
- AWS S3 (data lake storage)
- AWS ECS Fargate (serverless container orchestration)
- AWS Lambda (API serving)
- AWS Bedrock (managed LLM inference)
- AWS ECR (container registry)
- AWS CloudFront (CDN)
- Docker (containerization)

**Data & ML:**
- AWS Bedrock SDK (LLM integration)
- Pydantic (data validation)
- Custom NLP pipelines (PII detection, conversation assembly)

**API & Web:**
- FastAPI (REST API framework)
- Uvicorn (ASGI server)
- HTML/CSS/JavaScript (frontend)

**DevOps:**
- pytest (testing framework)
- Environment-based configuration (.env)
- Shell scripts for automated deployments

## AWS Deployment Workflow

### 1. Initial Setup
- **S3 Bucket:** Create bucket with folder structure (`landing/`, `sanitized/`, `curated/`, `reports/`)
- **IAM Roles:** 
  - ECS Task Role: S3 read/write + Bedrock invoke permissions
  - Lambda Execution Role: S3 read + CloudWatch Logs
  - ECS Task Execution Role: ECR image pull
- **Bedrock:** Enable model access (Amazon Nova Micro in eu-north-1)

### 2. Pipeline Deployment (ECS Fargate)
- Build Docker image: `docker build -f services/pipeline/Dockerfile -t llm-classifier .`
- Push to ECR repository
- Create ECS task definition with environment variables (S3_BUCKET, BEDROCK_REGION, etc.)
- Configure VPC networking (subnets, security groups)
- Run task via CLI: `aws ecs run-task --cluster <cluster> --task-definition bedrock-classifier-task`
- Schedule with EventBridge (optional) for daily execution

### 3. API Deployment (Lambda)
- Build Lambda container: `docker build -f services/api/Dockerfile.lambda -t llm-api-lambda .`
- Push to ECR
- Create Lambda function from container image (512 MB memory, 30s timeout)
- Set environment variables (S3_BUCKET, CORS_ALLOW_ORIGINS)
- Add HTTP API Gateway trigger
- Configure CORS for frontend domain
- (Add authentication for real use)

### 4. Frontend Deployment (CloudFront)
- Upload static files (index.html, script.js, styles.css) to S3 bucket
- Enable static website hosting
- Create CloudFront distribution pointing to S3
- Update frontend API endpoint URL to Lambda/API Gateway URL

### 5. Execution
- Upload conversation logs to S3: `s3://bucket/landing/date=2026-01-08/conversations.jsonl`
- Trigger pipeline: `./run_pipeline_job.sh` or scheduled ECS task
- Access results via API: `https://<api-gateway-url>/v1/metrics?date=2026-01-08`
- View dashboard: `https://<cloudfront-url>`

## Project Structure

```
LLM-use-classifier/
├── services/
│   ├── pipeline/          # ETL pipeline (ECS Fargate)
│   │   ├── classify_pipeline/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── api/              # REST API (Lambda)
│       ├── app/
│       ├── tests/
│       ├── Dockerfile.lambda
│       └── requirements.txt
├── llm-use-frontend/     # Web UI (CloudFront)
├── local_data_IO/        # Local development data
└── run_pipeline_job.sh   # ECS deployment script
```

## Design Principles

**Modularity & Extensibility:**
- **Clean separation of concerns** - Pipeline stages (sanitize, assemble, classify, aggregate) are independent modules
- **Trivial to extend** - Add new pipeline steps by creating a new module and updating the main orchestration function
- **Flexible classification logic** - Swap LLM models or classification strategies by modifying a single function in `classify_pipeline/core/classify.py`

**Deployment-Ready:**
- **Abstracted storage layer** - Single interface (`StorageIO`) for local filesystem and S3; switch environments with one environment variable
- **API versioning** - Built-in folder structure (`endpoints/v1/`) enables versioned endpoints and easy rollbacks
- **Testing** - Unit and integration tests with high coverage
- **Environment-based config** - Zero code changes between local development and AWS production deployments

## Getting Started

**For local development and testing:**
- Pipeline: See [services/pipeline/QUICKSTART.md](services/pipeline/QUICKSTART.md)
- API: See [services/api/README.md](services/api/README.md)

**For AWS deployment:**
- Pipeline configuration: [services/pipeline/CONFIGURATION.md](services/pipeline/CONFIGURATION.md)
- ECS deployment: [services/pipeline/QUICKSTART.md](services/pipeline/QUICKSTART.md#run-on-aws-ecs-fargate)
- Lambda deployment: [services/api/README.md](services/api/README.md#deploy-to-aws-lambda)

## Use Cases

This project demonstrates:
- Building ML/LLM pipelines for enterprise data pipelines
- Designing serverless ETL workflows for analytics products
- Integrating managed AI services (Bedrock, OpenAI) into business applications
- Implementing data privacy and compliance features (PII detection/redaction)
- Architecting pay-for-use cloud infrastructure
- Developing simple AI/MLOps workflows with containerization and AWS deployment
