"""
LLM Conversation Classification Pipeline - Main Entry Point

Orchestrates the complete pipeline:
1. Load configuration
2. Initialize storage backend (LocalIO or S3IO)
3. Discover input files for the specified date
4. Stream and parse JSONL events
5. Sanitize content (redact emails, phones, URLs)
6. Assemble conversations from events
7. Classify conversations into task categories
8. Aggregate daily metrics
9. Write outputs (metrics, reports, optional sanitized data)

Usage:
    # Local filesystem (default)
    python -m classify_pipeline.main
    
    # With custom settings
    STORAGE=local DATE=2026-01-03 BASE_PATH=local_data_IO python -m classify_pipeline.main
    
    # S3 backend
    STORAGE=s3 S3_BUCKET=my-bucket DATE=2026-01-03 python -m classify_pipeline.main
"""

import json
import logging
import sys
from datetime import datetime, UTC
from time import time

from .config import load_config
from .io.local import LocalIO
from .io.s3 import S3IO
from .core.schemas import MessageEvent, RunReport, RedactionStats
from .core.sanitize import sanitize_event
from .core.assemble import assemble_conversations
from .core.classify import classify_conversations
from .core.aggregate import aggregate_metrics
from .core.outputs import write_metrics, write_run_report, write_sanitized_events


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def parse_jsonl_line(line: str) -> MessageEvent | None:
    """Parse a single JSONL line into a MessageEvent.
    
    Args:
        line: JSON string representing a message event
        
    Returns:
        MessageEvent if valid, None if parsing fails
    """
    try:
        data = json.loads(line.strip())
        return MessageEvent(**data)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse event: {e}")
        return None


def run_pipeline() -> int:
    """Run the complete classification pipeline.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    start_time = time()
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        logger.info(f"Configuration: storage={config.storage}, date={config.date}")
        
        # Initialize storage backend
        logger.info(f"Initializing {config.storage.value} storage backend...")
        if config.storage.value == "local":
            storage = LocalIO(base_path=config.base_path)
            logger.info(f"Local storage initialized at: {config.base_path}")
        else:  # s3
            storage = S3IO(bucket=config.s3_bucket, region=config.aws_region)
            logger.info(f"S3 storage initialized: bucket={config.s3_bucket}, region={config.aws_region}")
        
        # Initialize run report
        report = RunReport(
            date=config.date,
            run_timestamp=datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
            storage_type=config.storage.value
        )
        
        # Discover input files
        landing_prefix = f"landing/date={config.date}/"
        logger.info(f"Discovering input files with prefix: {landing_prefix}")
        input_objects = storage.list_objects(landing_prefix)
        
        if not input_objects:
            logger.warning(f"No input files found for date {config.date}")
            report.errors.append(f"No input files found at {landing_prefix}")
            write_run_report(storage, report, config.date)
            return 1
        
        logger.info(f"Found {len(input_objects)} input file(s)")
        report.input_files_count = len(input_objects)
        
        # Read and parse events
        logger.info("Reading and parsing events...")
        events: list[MessageEvent] = []
        redaction_stats = RedactionStats()
        
        for obj in input_objects:
            logger.info(f"Processing file: {obj.key}")
            try:
                for line in storage.open_text(obj.key):
                    report.events_read += 1
                    
                    # Parse event
                    event = parse_jsonl_line(line)
                    if event is None:
                        report.events_invalid += 1
                        continue
                    
                    report.events_valid += 1
                    
                    # Sanitize event
                    sanitized_event = sanitize_event(event, redaction_stats)
                    events.append(sanitized_event)
                    
            except Exception as e:
                error_msg = f"Error processing file {obj.key}: {e}"
                logger.error(error_msg)
                report.errors.append(error_msg)
        
        logger.info(f"Parsed {len(events)} valid events ({report.events_invalid} invalid)")
        report.redaction_stats = redaction_stats
        logger.info(f"Redactions: {redaction_stats.total_redactions} total "
                   f"(emails={redaction_stats.emails_redacted}, "
                   f"phones={redaction_stats.phones_redacted}, "
                   f"urls={redaction_stats.urls_redacted})")
        
        if not events:
            logger.warning("No valid events to process")
            report.errors.append("No valid events found")
            write_run_report(storage, report, config.date)
            return 1
        
        # Write sanitized events (optional)
        if config.write_sanitized:
            logger.info("Writing sanitized events...")
            write_sanitized_events(storage, events, config.date)
            report.sanitized_written = True
        
        # Assemble conversations
        logger.info("Assembling conversations...")
        conversations = assemble_conversations(events)
        report.conversations_assembled = len(conversations)
        logger.info(f"Assembled {len(conversations)} conversations")
        
        # Classify conversations
        logger.info("Classifying conversations...")
        classified_conversations = classify_conversations(conversations)
        report.conversations_classified = len(classified_conversations)
        logger.info(f"Classified {len(classified_conversations)} conversations")
        
        # Aggregate metrics
        logger.info("Aggregating metrics...")
        daily_metrics = aggregate_metrics(classified_conversations, config.date)
        logger.info(f"Generated {len(daily_metrics.metrics)} metric groups")
        
        # Write metrics
        logger.info("Writing metrics...")
        write_metrics(storage, daily_metrics, config.date)
        report.metrics_written = True
        
        # Write run report
        report.duration_seconds = time() - start_time
        logger.info(f"Writing run report...")
        write_run_report(storage, report, config.date)
        
        logger.info(f"Pipeline completed successfully in {report.duration_seconds:.2f}s")
        logger.info(f"Metrics written to: curated/metrics_daily/date={config.date}/metrics.json")
        logger.info(f"Report written to: reports/date={config.date}/run_latest.json")
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


def main():
    """Entry point for CLI execution."""
    sys.exit(run_pipeline())


if __name__ == "__main__":
    main()
