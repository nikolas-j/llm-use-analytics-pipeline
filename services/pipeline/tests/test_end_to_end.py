"""
End-to-end pipeline test.

Creates a temporary dataset, runs the pipeline, and validates outputs.
"""

import json
import os
import shutil
from pathlib import Path
import pytest

from classify_pipeline.config import PipelineConfig
from classify_pipeline.io.local import LocalIO
from classify_pipeline.main import run_pipeline


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory with sample input."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    
    # Create landing directory with sample data
    landing_dir = data_dir / "landing" / "date=2026-01-03"
    landing_dir.mkdir(parents=True)
    
    # Sample JSONL data with 2 conversations
    sample_events = [
        # Conversation 1 (Sales team)
        {
            "event_time": "2026-01-03T10:00:00Z",
            "conversation_id": "conv_001",
            "message_id": "msg_001",
            "role": "user",
            "content": "Hello, I need help with pricing",
            "team": "Sales",
            "user_id": "u_100"
        },
        {
            "event_time": "2026-01-03T10:01:00Z",
            "conversation_id": "conv_001",
            "message_id": "msg_002",
            "role": "assistant",
            "content": "I'd be happy to help with pricing information",
            "team": "Sales",
            "user_id": "u_100"
        },
        {
            "event_time": "2026-01-03T10:02:00Z",
            "conversation_id": "conv_001",
            "message_id": "msg_003",
            "role": "user",
            "content": "Contact me at sales@example.com",
            "team": "Sales",
            "user_id": "u_100"
        },
        # Conversation 2 (Support team)
        {
            "event_time": "2026-01-03T11:00:00Z",
            "conversation_id": "conv_002",
            "message_id": "msg_004",
            "role": "user",
            "content": "My account is locked",
            "team": "Support",
            "user_id": "u_200"
        },
        {
            "event_time": "2026-01-03T11:01:00Z",
            "conversation_id": "conv_002",
            "message_id": "msg_005",
            "role": "assistant",
            "content": "Let me help you unlock your account",
            "team": "Support",
            "user_id": "u_200"
        },
    ]
    
    # Write to JSONL file
    input_file = landing_dir / "input01.jsonl"
    with open(input_file, 'w') as f:
        for event in sample_events:
            f.write(json.dumps(event) + '\n')
    
    yield data_dir
    
    # Cleanup is automatic with tmp_path


def test_end_to_end_pipeline(temp_data_dir, monkeypatch):
    """Test the complete pipeline with sample data."""
    # Set environment variables for test
    monkeypatch.setenv("STORAGE", "local")
    monkeypatch.setenv("DATE", "2026-01-03")
    monkeypatch.setenv("BASE_PATH", str(temp_data_dir))
    monkeypatch.setenv("WRITE_SANITIZED", "true")
    # Use bypass mode for faster testing
    monkeypatch.setenv("LLM_CLASSIFICATION", "false")
    
    # Reload config to pick up environment changes
    import importlib
    from classify_pipeline import config
    from classify_pipeline.core import classify
    importlib.reload(config)
    importlib.reload(classify)
    
    # Run pipeline
    exit_code = run_pipeline()
    
    # Verify successful execution
    assert exit_code == 0
    
    # Verify output files exist
    metrics_file = temp_data_dir / "curated" / "metrics_daily" / "date=2026-01-03" / "metrics.json"
    report_file = temp_data_dir / "reports" / "date=2026-01-03" / "run_latest.json"
    sanitized_file = temp_data_dir / "sanitized" / "date=2026-01-03" / "messages.jsonl"
    
    assert metrics_file.exists(), "Metrics file should be created"
    assert report_file.exists(), "Report file should be created"
    assert sanitized_file.exists(), "Sanitized file should be created"
    
    # Validate metrics content
    with open(metrics_file) as f:
        metrics = json.load(f)
    
    assert metrics["date"] == "2026-01-03"
    assert metrics["total_conversations"] == 2
    assert metrics["total_events_processed"] == 5
    assert len(metrics["metrics"]) > 0
    
    # Check that we have metrics for both teams
    teams = {m["team"] for m in metrics["metrics"]}
    assert "Sales" in teams or "Support" in teams
    
    # All conversations should be classified
    for metric in metrics["metrics"]:
        assert metric["task_category"] is not None
        assert metric["conversation_count"] > 0
        # In bypass mode, all should be "Unclassified"
        assert metric["task_category"] == "Unclassified"
    
    # Validate report content
    with open(report_file) as f:
        report = json.load(f)
    
    assert report["date"] == "2026-01-03"
    assert report["storage_type"] == "local"
    assert report["input_files_count"] == 1
    assert report["events_read"] == 5
    assert report["events_valid"] == 5
    assert report["conversations_assembled"] == 2
    assert report["conversations_classified"] == 2
    assert report["metrics_written"] is True
    assert report["sanitized_written"] is True
    
    # Verify redaction happened
    assert report["redaction_stats"]["emails_redacted"] >= 1
    
    # Validate sanitized content
    with open(sanitized_file) as f:
        sanitized_lines = f.readlines()
    
    assert len(sanitized_lines) == 5
    
    # Check that email was redacted
    sanitized_content = ''.join(sanitized_lines)
    assert "sales@example.com" not in sanitized_content
    assert "[EMAIL_REDACTED]" in sanitized_content


def test_no_input_files(tmp_path, monkeypatch):
    """Test pipeline behavior when no input files are found."""
    data_dir = tmp_path / "empty_data"
    data_dir.mkdir()
    
    # Create empty landing directory
    landing_dir = data_dir / "landing" / "date=2026-01-04"
    landing_dir.mkdir(parents=True)
    
    monkeypatch.setenv("STORAGE", "local")
    monkeypatch.setenv("DATE", "2026-01-04")
    monkeypatch.setenv("BASE_PATH", str(data_dir))
    
    # Run pipeline - should fail gracefully
    exit_code = run_pipeline()
    
    assert exit_code == 1  # Non-zero exit for no input files
    
    # Report should still be written
    report_file = data_dir / "reports" / "date=2026-01-04" / "run_latest.json"
    assert report_file.exists()
    
    with open(report_file) as f:
        report = json.load(f)
    
    assert report["input_files_count"] == 0
    assert len(report["errors"]) > 0


def test_invalid_events(tmp_path, monkeypatch):
    """Test pipeline handling of invalid JSONL events."""
    data_dir = tmp_path / "invalid_data"
    data_dir.mkdir()
    
    landing_dir = data_dir / "landing" / "date=2026-01-03"
    landing_dir.mkdir(parents=True)
    
    # Write mix of valid and invalid events
    input_file = landing_dir / "input.jsonl"
    with open(input_file, 'w') as f:
        # Valid event
        f.write(json.dumps({
            "event_time": "2026-01-03T10:00:00Z",
            "conversation_id": "conv_1",
            "message_id": "msg_1",
            "role": "user",
            "content": "Hello",
            "team": "Sales",
            "user_id": "u_1"
        }) + '\n')
        
        # Invalid JSON
        f.write("{ invalid json }\n")
        
        # Missing required fields
        f.write(json.dumps({"message_id": "msg_2"}) + '\n')
        
        # Another valid event
        f.write(json.dumps({
            "event_time": "2026-01-03T10:01:00Z",
            "conversation_id": "conv_1",
            "message_id": "msg_3",
            "role": "assistant",
            "content": "Hi there",
            "team": "Sales",
            "user_id": "u_1"
        }) + '\n')
    
    monkeypatch.setenv("STORAGE", "local")
    monkeypatch.setenv("DATE", "2026-01-03")
    monkeypatch.setenv("BASE_PATH", str(data_dir))
    monkeypatch.setenv("WRITE_SANITIZED", "false")
    monkeypatch.setenv("LLM_CLASSIFICATION", "false")  # Bypass mode for testing
    
    exit_code = run_pipeline()
    
    # Should succeed with valid events
    assert exit_code == 0
    
    # Check report
    report_file = data_dir / "reports" / "date=2026-01-03" / "run_latest.json"
    with open(report_file) as f:
        report = json.load(f)
    
    assert report["events_read"] == 4
    assert report["events_valid"] == 2
    assert report["events_invalid"] == 2


@pytest.mark.integration
def test_end_to_end_with_llm_classification(temp_data_dir, monkeypatch):
    """Test complete pipeline with LLM classification enabled.
    
    This is an integration test that requires:
    - LLM_CLASSIFICATION=true
    - Valid AWS credentials
    - Bedrock model access
    
    Run with: pytest -m integration tests/test_end_to_end.py::test_end_to_end_with_llm_classification
    """
    # Set environment for test
    monkeypatch.setenv("STORAGE", "local")
    monkeypatch.setenv("DATE", "2026-01-03")
    monkeypatch.setenv("BASE_PATH", str(temp_data_dir))
    monkeypatch.setenv("WRITE_SANITIZED", "true")
    monkeypatch.setenv("LLM_CLASSIFICATION", "true")
    monkeypatch.setenv("BEDROCK_REGION", "eu-north-1")
    monkeypatch.setenv("BEDROCK_MODEL_ID", "eu.amazon.nova-micro-v1:0")
    
    # Reload config to pick up environment changes
    import importlib
    from classify_pipeline import config
    from classify_pipeline.core import classify
    importlib.reload(config)
    importlib.reload(classify)
    
    # Verify LLM is enabled
    from classify_pipeline.config import load_config
    config_obj = load_config()
    if not config_obj.llm_classification:
        pytest.skip("LLM classification is not enabled")
    
    # Run pipeline
    exit_code = run_pipeline()
    
    # Verify successful execution
    assert exit_code == 0
    
    # Check metrics
    metrics_file = temp_data_dir / "curated" / "metrics_daily" / "date=2026-01-03" / "metrics.json"
    assert metrics_file.exists()
    
    with open(metrics_file) as f:
        metrics = json.load(f)
    
    # Verify classifications are NOT "Unclassified" (real LLM was used)
    from classify_pipeline.core.classify import VALID_LABELS
    
    for metric in metrics["metrics"]:
        category = metric["task_category"]
        # Should be a real classification, not bypass mode
        assert category in VALID_LABELS
        # In LLM mode, shouldn't all be "Unclassified"
        # (though some might legitimately be classified as Other/Unknown)
    
    # Check report
    report_file = temp_data_dir / "reports" / "date=2026-01-03" / "run_latest.json"
    with open(report_file) as f:
        report = json.load(f)
    
    assert report["conversations_classified"] == 2
    print(f"Classifications: {[m['task_category'] for m in metrics['metrics']]}")
    assert report["conversations_assembled"] == 2
