"""
Metrics aggregation module.

Computes daily metrics grouped by team and task category.
Aggregates conversation counts, turn counts, and character counts.
"""

from collections import defaultdict
from .schemas import Conversation, CategoryMetrics, DailyMetrics


def aggregate_metrics(
    conversations: list[Conversation], 
    date: str
) -> DailyMetrics:
    """Aggregate conversations into daily metrics.
    
    Groups conversations by (team, task_category) and computes:
    - conversation_count: number of conversations
    - total_turns: sum of message counts
    - total_chars_user: sum of user message characters
    - total_chars_assistant: sum of assistant message characters
    
    Derived metrics (computed via properties):
    - avg_turns: average turns per conversation
    - avg_chars_user: average user chars per conversation
    - avg_chars_assistant: average assistant chars per conversation
    
    Args:
        conversations: List of classified conversations
        date: Date string (YYYY-MM-DD)
        
    Returns:
        DailyMetrics object with aggregated data
    """
    # Group by (team, task_category)
    metrics_map: dict[tuple[str, str], CategoryMetrics] = {}
    
    for conv in conversations:
        # Skip if not classified
        if conv.task_category is None:
            continue
        
        key = (conv.team, conv.task_category)
        
        if key not in metrics_map:
            metrics_map[key] = CategoryMetrics(
                team=conv.team,
                task_category=conv.task_category
            )
        
        metric = metrics_map[key]
        metric.conversation_count += 1
        metric.total_turns += conv.turn_count
        metric.total_chars_user += conv.total_chars_user
        metric.total_chars_assistant += conv.total_chars_assistant
    
    # Convert to list and sort for deterministic output
    metrics_list = sorted(
        metrics_map.values(),
        key=lambda m: (m.team, m.task_category)
    )
    
    # Count total events processed
    total_events = sum(len(conv.messages) for conv in conversations)
    
    return DailyMetrics(
        date=date,
        metrics=metrics_list,
        total_conversations=len(conversations),
        total_events_processed=total_events
    )
