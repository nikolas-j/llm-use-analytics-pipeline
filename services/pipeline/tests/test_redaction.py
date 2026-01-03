"""
Tests for content sanitization (redaction).

Tests email, phone, and URL redaction with various patterns.
"""

import pytest
from classify_pipeline.core.sanitize import (
    sanitize_content,
    sanitize_event,
    EMAIL_PLACEHOLDER,
    PHONE_PLACEHOLDER,
    URL_PLACEHOLDER,
)
from classify_pipeline.core.schemas import MessageEvent, RedactionStats


def test_email_redaction():
    """Test email address redaction."""
    stats = RedactionStats()
    
    content = "Contact me at john.doe@example.com or jane@company.org"
    result = sanitize_content(content, stats)
    
    assert EMAIL_PLACEHOLDER in result
    assert "john.doe@example.com" not in result
    assert "jane@company.org" not in result
    assert stats.emails_redacted == 2


def test_phone_redaction():
    """Test phone number redaction with various formats."""
    stats = RedactionStats()
    
    content = "Call me at (123) 456-7890 or 987-654-3210 or +1-555-123-4567"
    result = sanitize_content(content, stats)
    
    assert PHONE_PLACEHOLDER in result
    assert "(123) 456-7890" not in result
    assert "987-654-3210" not in result
    assert stats.phones_redacted >= 2  # At least 2 phone numbers


def test_url_redaction():
    """Test URL redaction."""
    stats = RedactionStats()
    
    content = "Visit https://www.example.com or http://test.org/path?query=1"
    result = sanitize_content(content, stats)
    
    assert URL_PLACEHOLDER in result
    assert "https://www.example.com" not in result
    assert "http://test.org" not in result
    assert stats.urls_redacted == 2


def test_combined_redaction():
    """Test redaction of multiple types in one content."""
    stats = RedactionStats()
    
    content = (
        "Contact john@example.com at (555) 123-4567 "
        "or visit https://example.com for more info"
    )
    result = sanitize_content(content, stats)
    
    assert EMAIL_PLACEHOLDER in result
    assert PHONE_PLACEHOLDER in result
    assert URL_PLACEHOLDER in result
    assert stats.emails_redacted == 1
    assert stats.phones_redacted >= 1
    assert stats.urls_redacted == 1
    assert stats.total_redactions >= 3


def test_no_redaction_needed():
    """Test content with no sensitive information."""
    stats = RedactionStats()
    
    content = "This is a normal message with no sensitive data"
    result = sanitize_content(content, stats)
    
    assert result == content
    assert stats.total_redactions == 0


def test_sanitize_event():
    """Test sanitizing a complete MessageEvent."""
    stats = RedactionStats()
    
    event = MessageEvent(
        event_time="2026-01-03T10:00:00Z",
        conversation_id="conv_1",
        message_id="msg_1",
        role="user",
        content="Email me at user@example.com",
        team="Sales",
        user_id="u_123"
    )
    
    sanitized = sanitize_event(event, stats)
    
    assert EMAIL_PLACEHOLDER in sanitized.content
    assert "user@example.com" not in sanitized.content
    assert sanitized.conversation_id == event.conversation_id
    assert sanitized.message_id == event.message_id
    assert stats.emails_redacted == 1


def test_multiple_same_pattern():
    """Test multiple instances of the same pattern."""
    stats = RedactionStats()
    
    content = "Email alice@test.com or bob@test.com or charlie@test.com"
    result = sanitize_content(content, stats)
    
    assert stats.emails_redacted == 3
    assert "alice@test.com" not in result
    assert "bob@test.com" not in result
    assert "charlie@test.com" not in result


def test_edge_case_formats():
    """Test edge case formats that should or shouldn't be redacted."""
    stats = RedactionStats()
    
    # Valid email with subdomain
    content = "admin@mail.example.co.uk is the email"
    result = sanitize_content(content, stats)
    assert EMAIL_PLACEHOLDER in result
    assert stats.emails_redacted >= 1
