# LLM Conversation Use Case Classifier

Project demonstrating MLOps pipeline for classifying LLM conversation logs.

## Project Overview

This project implements a modular data pipeline that:
1. **Ingests** JSONL message event logs from conversations
2. **Sanitizes** content by redacting sensitive information (PII)
3. **Assembles** messages into complete conversations
4. **Classifies** conversations into task categories
5. **Aggregates** daily metrics by team and category
6. **Outputs** curated analytics data

Additionally the pipeline results are served via FastAPI.

## Quick Start

```bash
# 1. Install dependencies
cd services/pipeline
pip install -r requirements.txt

# 2. Create configuration file
cp .env.example .env
# (Defaults work out-of-the-box for local development)

# 3. Run pipeline with sample data
python -m classify_pipeline.main

# 4. View results
cat ../../local_data_IO/curated/metrics_daily/date=2026-01-03/metrics.json
```

**Expected output**:
```
✓ Found 1 input file(s)
✓ Parsed 10 valid events
✓ Redactions: 4 total (emails=2, phones=1, urls=1)
✓ Assembled 3 conversations
✓ Classified 3 conversations
✓ Pipeline completed successfully in 0.01s
```


### Storage Abstraction
```python
class StorageIO(ABC):
    """Storage-agnostic interface"""
    def list_objects(prefix: str) -> list[ObjectRef]: ...
    def open_text(key: str) -> Iterator[str]: ...
    def write_json(key: str, data: Any): ...
    def exists(key: str) -> bool: ...

# Implementations:
LocalIO(base_path)      # Filesystem
S3IO(bucket, region)    # AWS S3
```

## Configuration

Environment variables:
```bash
STORAGE=local|s3           # Backend type
DATE=YYYY-MM-DD            # Processing date
BASE_PATH=/path/to/data    # Local filesystem root
S3_BUCKET=my-bucket        # S3 bucket (if storage=s3)
AWS_REGION=us-east-1       # AWS region
WRITE_SANITIZED=true       # Optional sanitized output
```

## Usage Examples

### Local Development
```bash
# Uses .env configuration
python -m classify_pipeline.main
```

### Custom Date
```bash
# Override DATE from .env
DATE=2026-01-04 python -m classify_pipeline.main
```

### AWS S3 Backend
```bash
STORAGE=s3 S3_BUCKET=my-logs DATE=2026-01-03 python -m classify_pipeline.main
```

### Run Tests
```bash
pytest tests/ -v --cov=classify_pipeline
```

## Sample Output

### Metrics (`curated/metrics_daily/date=2026-01-03/metrics.json`)
```json
{
  "date": "2026-01-03",
  "total_conversations": 3,
  "metrics": [
    {
      "team": "Sales",
      "task_category": "uncategorized",
      "conversation_count": 1,
      "total_turns": 4,
      "avg_turns": 4.0,
      "avg_chars_user": 117.0
    }
  ]
}
```

### Run Report (`reports/date=2026-01-03/run_latest.json`)
```json
{
  "date": "2026-01-03",
  "storage_type": "local",
  "events_read": 10,
  "conversations_assembled": 3,
  "redaction_stats": {
    "emails_redacted": 2,
    "phones_redacted": 1,
    "urls_redacted": 1
  },
  "duration_seconds": 0.01,
  "errors": []
}
```

## Content Sanitization

Automatically redacts PII:
- **Emails**: `user@example.com` → `[EMAIL_REDACTED]`
- **Phones**: `(555) 123-4567` → `[PHONE_REDACTED]`
- **URLs**: `https://example.com` → `[URL_REDACTED]`

Redaction statistics tracked in run reports.

## Testing

```bash
# Run all tests
pytest tests/

# With coverage report
pytest --cov=classify_pipeline --cov-report=html tests/

# Specific test file
pytest tests/test_redaction.py -v
```
