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

