"""
Conversation classification module.

Classifies conversations into task categories.
PLACEHOLDER IMPLEMENTATION: Returns 'uncategorized' for all conversations.
TODO: Implement actual classification logic (e.g., using LLM, rules, or ML model).
"""

from .schemas import Conversation


def classify_conversation(conversation: Conversation) -> str:
    """Classify a conversation into a task category.
    
    PLACEHOLDER: Currently returns 'uncategorized' for all conversations.
    
    Future implementation will analyze conversation content and return
    categories like:
    - "technical_support"
    - "sales_inquiry"
    - "billing_question"
    - "feature_request"
    - "complaint"
    - etc.
    
    Args:
        conversation: Conversation to classify
        
    Returns:
        Task category string
    """
    # TODO: Implement classification logic
    # This could use:
    # - LLM prompt with conversation summary
    # - Rule-based keyword matching
    # - Trained ML classifier
    # - Hybrid approach
    
    return "uncategorized"


def classify_conversations(conversations: list[Conversation]) -> list[Conversation]:
    """Classify multiple conversations and update their task_category field.
    
    Args:
        conversations: List of conversations to classify
        
    Returns:
        List of conversations with task_category set
    """
    for conversation in conversations:
        conversation.task_category = classify_conversation(conversation)
    
    return conversations
