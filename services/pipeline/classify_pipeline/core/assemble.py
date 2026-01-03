"""
Conversation assembly module.

Groups message events by conversation_id and sorts them by event_time
to create complete conversation objects.
"""

from collections import defaultdict
from .schemas import MessageEvent, Conversation


def assemble_conversations(events: list[MessageEvent]) -> list[Conversation]:
    """Assemble message events into conversations.
    
    Groups events by conversation_id and sorts messages within each
    conversation by event_time (chronological order).
    
    Args:
        events: List of message events to assemble
        
    Returns:
        List of Conversation objects with sorted messages
    """
    # Group events by conversation_id
    conversation_map: dict[str, list[MessageEvent]] = defaultdict(list)
    
    for event in events:
        conversation_map[event.conversation_id].append(event)
    
    # Create Conversation objects
    conversations = []
    for conv_id, messages in conversation_map.items():
        # Sort messages by event_time chronologically
        sorted_messages = sorted(messages, key=lambda m: m.event_datetime)
        
        # Get team from first message (all messages in a conversation should have same team)
        team = sorted_messages[0].team if sorted_messages else "unknown"
        
        conversation = Conversation(
            conversation_id=conv_id,
            team=team,
            messages=sorted_messages
        )
        conversations.append(conversation)
    
    # Sort conversations by conversation_id for deterministic output
    return sorted(conversations, key=lambda c: c.conversation_id)
