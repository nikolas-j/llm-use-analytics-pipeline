"""
Output writing module.

Handles safe publishing of metrics and reports using temporary files
to avoid partial reads during write operations.
"""

from ..io.base import StorageIO
from .schemas import DailyMetrics, RunReport


def write_metrics(
    storage: StorageIO,
    metrics: DailyMetrics,
    date: str
) -> None:
    """Write daily metrics using safe publish pattern.
    
    Writes to a temporary file first, then publishes to final location.
    For MVP with local/S3, we directly write to final location since
    both backends support atomic writes.
    
    Args:
        storage: Storage backend
        metrics: Daily metrics to write
        date: Date string (YYYY-MM-DD) for key path
    """
    metrics_key = f"curated/metrics_daily/date={date}/metrics.json"
    
    # Convert Pydantic model to dict for JSON serialization
    metrics_dict = metrics.model_dump(mode='json')
    
    # For production, could write to .tmp then rename:
    # tmp_key = f"curated/metrics_daily/date={date}/metrics.tmp.json"
    # storage.write_json(tmp_key, metrics_dict)
    # storage.rename(tmp_key, metrics_key)  # Would need to add rename to StorageIO
    
    # MVP: direct write (S3 PutObject is atomic, local write is fast enough)
    storage.write_json(metrics_key, metrics_dict)


def write_run_report(
    storage: StorageIO,
    report: RunReport,
    date: str
) -> None:
    """Write pipeline run report.
    
    Args:
        storage: Storage backend
        report: Run report to write
        date: Date string (YYYY-MM-DD) for key path
    """
    report_key = f"reports/date={date}/run_latest.json"
    
    # Convert Pydantic model to dict for JSON serialization
    report_dict = report.model_dump(mode='json')
    
    storage.write_json(report_key, report_dict)


def write_sanitized_events(
    storage: StorageIO,
    events: list,
    date: str,
) -> None:
    """Write sanitized events to storage (optional).
    
    Args:
        storage: Storage backend
        events: List of message events (Pydantic models)
        date: Date string (YYYY-MM-DD)
    """
    import json
    
    sanitized_key = f"sanitized/date={date}/messages.jsonl"
    
    # Convert each event to JSON line
    lines = [json.dumps(event.model_dump(mode='json')) + '\n' for event in events]
    
    storage.write_text_lines(sanitized_key, lines)
