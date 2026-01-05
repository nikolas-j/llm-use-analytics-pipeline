# Pipeline Tests

## Quick Start

```bash
cd services/pipeline

# Unit tests (fast, no AWS) - 37 tests in ~4s
pytest -m "not integration"

# Integration tests (requires AWS credentials) - 11 tests in ~22s
pytest -m integration

# All tests - 48 tests in ~26s
pytest
```

## Test Files

- **test_classification.py** (14 tests) - Classification logic with mocks
- **test_classification_integration.py** (13 tests) - Real Bedrock API calls
- **test_config.py** (9 tests) - Config validation
- **test_end_to_end.py** (4 tests) - Full pipeline flow
- **test_redaction.py** (8 tests) - Email/phone/URL sanitization

## Integration Tests (AWS Required)

**Requirements:**
- AWS credentials configured: `aws configure`
- Bedrock model access enabled in console
- IAM permission: `bedrock:InvokeModel`
- Env vars: `LLM_CLASSIFICATION=true`, `BEDROCK_REGION=eu-north-1`, `BEDROCK_MODEL_ID=eu.amazon.nova-micro-v1:0`

**Cost:** ~$0.01 per run

## Test Output Locations

All tests use temporary directories (auto-cleaned):
- Landing: `{tmp}/landing/date=YYYY-MM-DD/*.jsonl`
- Sanitized: `{tmp}/sanitized/date=YYYY-MM-DD/messages.jsonl`
- Metrics: `{tmp}/curated/metrics_daily/date=YYYY-MM-DD/metrics.json`
- Reports: `{tmp}/reports/date=YYYY-MM-DD/run_latest.json`

## Common Commands

```bash
# Run specific test
pytest tests/test_classification.py::test_classify_snippet_bypass_mode -v

# Skip integration tests (CI/CD)
pytest -m "not integration"

# Run with coverage
pytest --cov=classify_pipeline
```
