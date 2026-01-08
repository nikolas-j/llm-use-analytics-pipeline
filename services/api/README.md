# LLM Classifier API

REST API for retrieving classified conversation data from S3. Provides access to daily metrics and reports stored in `curated/metrics_daily/date=YYYY-MM-DD/metrics.json` and `reports/date=YYYY-MM-DD/run_latest.json` paths.

**Endpoints:**
- `GET /v1/metrics?date=YYYY-MM-DD` - Daily classification metrics
- `GET /v1/reports?date=YYYY-MM-DD` - Daily pipeline reports

## Run Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```env
AWS_S3_BUCKET_NAME=your-bucket-name
AWS_REGION=eu-north-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:8000
```

3. Start the server:
```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`

## Run Tests

```bash
pytest tests/
```

## Run with Docker

1. Build the image:
```bash
docker build -t llm-classifier-api .
```

2. Run the container:
```bash
docker run -p 8000:8000 \
  -e AWS_S3_BUCKET_NAME=your-bucket-name \
  -e AWS_REGION=eu-north-1 \
  -e AWS_ACCESS_KEY_ID=your-key \
  -e AWS_SECRET_ACCESS_KEY=your-secret \
  llm-classifier-api
```

Or use an `.env` file:
```bash
docker run -p 8000:8000 --env-file .env llm-classifier-api
```

API available at `http://localhost:8000`

Interactive docs at `http://localhost:8000/docs`

## Deploy to AWS Lambda

1. **Build the Lambda image:**
```bash
docker build -f Dockerfile.lambda -t llm-classifier-api-lambda .
```

2. **Push to Amazon ECR:**
   - Create an ECR repository
   - Tag and push the image to ECR

3. **Create Lambda function:**
   - Create function from container image
   - Configure environment variables (AWS_S3_BUCKET_NAME, AWS_REGION, CORS_ALLOW_ORIGINS)
   - Set timeout to at least 30 seconds
   - Configure memory (recommended: 512 MB or higher)

4. **Configure IAM role:**
   - Lambda execution role needs:
     - Basic Lambda execution permissions
     - S3 read access to your data bucket

5. **Add API Gateway trigger:**
   - Create HTTP API or REST API
   - Configure CORS settings to match your frontend domain

6. **Test the endpoint:**
   - Use the API Gateway URL to access metrics and reports

