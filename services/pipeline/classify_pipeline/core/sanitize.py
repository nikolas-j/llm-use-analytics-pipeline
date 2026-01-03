"""
Content sanitization module.

Implements regex-based redaction of sensitive information:
- Email addresses
- Phone numbers (US and international formats)
- URLs

Tracks redaction statistics for reporting.
"""

import re
from .schemas import MessageEvent, RedactionStats


# Regex patterns for sensitive data
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

# US: (123) 456-7890, 123-456-7890, 123.456.7890, +1-123-456-7890
# International: +XX-XXX-XXX-XXXX
PHONE_PATTERN = re.compile(
    r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
)

URL_PATTERN = re.compile(
    r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
)

# Replacement placeholders
EMAIL_PLACEHOLDER = "[EMAIL_REDACTED]"
PHONE_PLACEHOLDER = "[PHONE_REDACTED]"
URL_PLACEHOLDER = "[URL_REDACTED]"


def sanitize_content(content: str, stats: RedactionStats) -> str:
    """Redact sensitive information from content.
    
    Replaces emails, phone numbers, and URLs with placeholders.
    Updates the provided stats object with counts.
    
    Args:
        content: Text content to sanitize
        stats: RedactionStats object to update with counts
        
    Returns:
        Sanitized content with redactions applied
    """
    # Count and replace emails
    email_matches = EMAIL_PATTERN.findall(content)
    stats.emails_redacted += len(email_matches)
    content = EMAIL_PATTERN.sub(EMAIL_PLACEHOLDER, content)
    
    # Count and replace phone numbers
    phone_matches = PHONE_PATTERN.findall(content)
    stats.phones_redacted += len(phone_matches)
    content = PHONE_PATTERN.sub(PHONE_PLACEHOLDER, content)
    
    # Count and replace URLs
    url_matches = URL_PATTERN.findall(content)
    stats.urls_redacted += len(url_matches)
    content = URL_PATTERN.sub(URL_PLACEHOLDER, content)
    
    return content


def sanitize_event(event: MessageEvent, stats: RedactionStats) -> MessageEvent:
    """Sanitize a message event's content.
    
    Creates a new MessageEvent with sanitized content.
    Updates stats with redaction counts.
    
    Args:
        event: Original message event
        stats: RedactionStats object to update
        
    Returns:
        New MessageEvent with sanitized content
    """
    sanitized_content = sanitize_content(event.content, stats)
    
    # Create new event with sanitized content
    return MessageEvent(
        event_time=event.event_time,
        conversation_id=event.conversation_id,
        message_id=event.message_id,
        role=event.role,
        content=sanitized_content,
        team=event.team,
        user_id=event.user_id
    )


def sanitize_events(events: list[MessageEvent]) -> tuple[list[MessageEvent], RedactionStats]:
    """Sanitize a batch of message events.
    
    Args:
        events: List of message events to sanitize
        
    Returns:
        Tuple of (sanitized events, redaction statistics)
    """
    stats = RedactionStats()
    sanitized = [sanitize_event(event, stats) for event in events]
    return sanitized, stats