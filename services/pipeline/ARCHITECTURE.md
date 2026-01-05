# Architecture

## Data Flow

```
Input (JSONL)  →  Sanitize  →  Assemble  →  Classify  →  Aggregate  →  Output (JSON)
     ↓              ↓           ↓            ↓            ↓             ↓
  landing/     redact PII   group by ID   LLM/rules   metrics by   curated/
                                                      team+category  reports/
```

**Systems:**
- **Storage Layer** (`io/`): Local filesystem or S3 via `StorageIO` interface
- **Pipeline** (`main.py`): Orchestrates stages, reads from `landing/`, writes to `curated/` and `reports/`
- **LLM Service** (`classify.py`): Amazon Bedrock Nova Micro via boto3 (optional, bypass mode available)

## Pipeline Responsibilities

**Data Ingestion:**
- Reads: `landing/date=YYYY-MM-DD/*.jsonl` (raw message events)
- Parses: JSONL to `MessageEvent` Pydantic models

**Processing Stages:**
1. **Sanitize** (`sanitize.py`) - Redact emails, phones, URLs via regex
2. **Assemble** (`assemble.py`) - Group events by `conversation_id`, sort by time
3. **Classify** (`classify.py`) - Categorize conversations (LLM or bypass mode)
4. **Aggregate** (`aggregate.py`) - Compute metrics by team + task category

**Data Output:**
- `curated/metrics_daily/date=YYYY-MM-DD/metrics.json` - Daily aggregated metrics
- `reports/date=YYYY-MM-DD/run_latest.json` - Execution report with stats/errors
- `sanitized/date=YYYY-MM-DD/messages.jsonl` - Sanitized events (optional)

## Design Principles

- **Storage Agnostic**: Core logic never imports boto3/pathlib, only uses `StorageIO` interface
- **Type Safe**: Pydantic models with validation for all data structures
- **Config-Driven**: `.env` file controls storage backend, LLM mode, no code changes needed
- **Testable**: Dependency injection, deterministic outputs, fast in-memory tests

## Safety

- **PII Redaction**: Regex patterns redact emails, phones, URLs before classification
- **Input Validation**: Invalid JSONL logged and skipped, doesn't crash pipeline
- **Error Tracking**: All errors captured in `RunReport.errors[]`
- **Bypass Mode**: `LLM_CLASSIFICATION=false` skips AWS calls for safe testing

## Extensibility

- **Storage Backends**: Implement `StorageIO` interface (current: Local, S3)
- **Classification**: Replace `classify_conversation()` function or change model in `.env`
- **Metrics**: Extend `CategoryMetrics` schema, modify `aggregate_metrics()`
- **Pipeline Stages**: Add new stages in `main.py` flow

## Observability

- **Logging**: Structured logs at INFO level for all stages
- **Run Reports**: JSON output with counts, duration, redaction stats, errors
- **Metrics**: Total conversations, events, invalid records, classifications

## Monitoring and Alerting

*(Implementation TBD)*

**Planned metrics:**
- Pipeline success/failure rate
- Processing duration (p50, p95, p99)
- Invalid event rate
- LLM classification latency and errors
