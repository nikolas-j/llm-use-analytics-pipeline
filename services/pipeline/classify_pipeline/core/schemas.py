"""
Data schemas for pipeline entities.

Defines Pydantic models for:
- MessageEvent: Raw input event from JSONL logs
- Conversation: Assembled group of messages
- DailyMetrics: Aggregated metrics by team and category
- RunReport: Pipeline execution metadata
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class MessageEvent(BaseModel):
    """Raw message event from JSONL input.
    
    Example:
        {
            "event_time": "2026-01-03T10:15:00Z",
            "conversation_id": "c_123",
            "message_id": "m_456",
            "role": "user",
            "content": "Hello, I need help with...",
            "team": "Sales",
            "user_id": "u_789"
        }
    """
    event_time: str  # ISO 8601 format
    conversation_id: str
    message_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    team: str
    user_id: str

    @property
    def event_datetime(self) -> datetime:
        """Parse event_time as datetime."""
        return datetime.fromisoformat(self.event_time.replace('Z', '+00:00'))


class Conversation(BaseModel):
    """Assembled conversation with all messages sorted by time."""
    conversation_id: str
    team: str
    messages: list[MessageEvent]
    task_category: str | None = None  # Set after classification
    
    @property
    def turn_count(self) -> int:
        """Number of messages in the conversation."""
        return len(self.messages)
    
    @property
    def total_chars_user(self) -> int:
        """Total characters in user messages."""
        return sum(
            len(msg.content) 
            for msg in self.messages 
            if msg.role == "user"
        )
    
    @property
    def total_chars_assistant(self) -> int:
        """Total characters in assistant messages."""
        return sum(
            len(msg.content) 
            for msg in self.messages 
            if msg.role == "assistant"
        )


class CategoryMetrics(BaseModel):
    """Metrics for a specific team and task category."""
    team: str
    task_category: str
    conversation_count: int = 0
    total_turns: int = 0
    total_chars_user: int = 0
    total_chars_assistant: int = 0
    
    @property
    def avg_turns(self) -> float:
        """Average turns per conversation."""
        if self.conversation_count == 0:
            return 0.0
        return self.total_turns / self.conversation_count
    
    @property
    def avg_chars_user(self) -> float:
        """Average user characters per conversation."""
        if self.conversation_count == 0:
            return 0.0
        return self.total_chars_user / self.conversation_count
    
    @property
    def avg_chars_assistant(self) -> float:
        """Average assistant characters per conversation."""
        if self.conversation_count == 0:
            return 0.0
        return self.total_chars_assistant / self.conversation_count


class DailyMetrics(BaseModel):
    """Daily aggregated metrics."""
    date: str  # YYYY-MM-DD
    metrics: list[CategoryMetrics] = Field(default_factory=list)
    total_conversations: int = 0
    total_events_processed: int = 0


class RedactionStats(BaseModel):
    """Statistics from content sanitization."""
    emails_redacted: int = 0
    phones_redacted: int = 0
    urls_redacted: int = 0
    
    @property
    def total_redactions(self) -> int:
        """Total number of redactions performed."""
        return self.emails_redacted + self.phones_redacted + self.urls_redacted


class RunReport(BaseModel):
    """Pipeline execution report."""
    date: str  # YYYY-MM-DD
    run_timestamp: str  # ISO 8601
    storage_type: Literal["local", "s3"]
    
    # Input stats
    input_files_count: int = 0
    events_read: int = 0
    events_valid: int = 0
    events_invalid: int = 0
    
    # Processing stats
    conversations_assembled: int = 0
    conversations_classified: int = 0
    redaction_stats: RedactionStats = Field(default_factory=RedactionStats)
    
    # Output stats
    metrics_written: bool = False
    sanitized_written: bool = False
    
    # Timing
    duration_seconds: float = 0.0
    
    # Errors
    errors: list[str] = Field(default_factory=list)
