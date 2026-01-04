"""
Conversation classification module using Amazon Bedrock.

Classifies conversation snippets into task categories using Nova Micro
with ultra-low latency and token-optimized prompts.

Configuration is loaded from .env file via PipelineConfig.
Set LLM_CLASSIFICATION=false in .env to bypass LLM calls (returns "Unclassified").
"""

import logging
from typing import Any

import boto3
from botocore.config import Config

from .schemas import Conversation
from ..config import load_config


# Logger
logger = logging.getLogger(__name__)

# Load config once at module level
_config = load_config()

# Valid classification labels (exact strings)
VALID_LABELS = [
    "Summarization",
    "Drafting/Rewriting",
    "Research/Synthesis",
    "Ideation/Planning",
    "Data/Analysis (general)",
    "Translation/Tone",
    "Internal Q&A (policy/process)",
    "Customer Comms (support/sales)",
    "Technical Help",
    "Other/Unknown",
]

# Tool definition for Bedrock Converse API
CLASSIFICATION_TOOL = {
    "toolSpec": {
        "name": "classify",
        "description": "Classify the conversation snippet into exactly one category",
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "The classification label",
                        "enum": VALID_LABELS,
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score between 0 and 1",
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief reason for classification (max 12 words)",
                        "maxLength": 100,
                    },
                },
                "required": ["label", "confidence", "reason"],
            }
        },
    }
}

# System and user prompt templates
SYSTEM_PROMPT = "You are a strict classifier. Select exactly one label. Output only a tool call."

USER_PROMPT_TEMPLATE = """Classify this snippet into one label. Snippet:
{snippet}"""


def _get_bedrock_client():
    """Create boto3 bedrock-runtime client with optimal config for low latency.
    
    Configuration is loaded from .env file via PipelineConfig.
    No code changes needed between local and ECS deployment.
    """
    # Boto3 config with timeouts from config
    config = Config(
        region_name=_config.bedrock_region,
        connect_timeout=_config.bedrock_connect_timeout,
        read_timeout=_config.bedrock_read_timeout,
        retries={
            "max_attempts": _config.bedrock_max_retries,
            "mode": "standard",
        },
    )
    
    return boto3.client("bedrock-runtime", config=config)


def _get_model_id() -> str:
    """Get Bedrock model ID from config."""
    return _config.bedrock_model_id


def classify_snippet(snippet: str) -> dict[str, Any]:
    """Classify a conversation snippet using Amazon Bedrock Nova Micro.
    
    Uses Bedrock Converse API with Tool Use to enforce strict JSON schema.
    Optimized for ultra-low latency and minimal token usage.
    
    If LLM_CLASSIFICATION is disabled in config, returns "Unclassified" immediately.
    
    Args:
        snippet: Text snippet to classify (typically a few conversation turns)
        
    Returns:
        Dictionary with keys:
        - label: str (one of VALID_LABELS or "Unclassified")
        - confidence: float (0.0 to 1.0)
        - reason: str (brief explanation, <=12 words)
        
    Example:
        >>> result = classify_snippet("Can you help me debug this Python error?")
        >>> print(result)
        {
            "label": "Technical Help",
            "confidence": 0.95,
            "reason": "User requesting debugging assistance"
        }
    """
    # Bypass LLM if classification is disabled (cost-saving mode)
    if not _config.llm_classification:
        logger.info("LLM classification disabled, returning 'Unclassified'")
        return {
            "label": "Unclassified",
            "confidence": 0.0,
            "reason": "LLM classification disabled",
        }
    
    client = _get_bedrock_client()
    model_id = _get_model_id()
    
    # Truncate snippet if too long (stay under token limits)
    max_chars = 2000
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars] + "..."
        logger.warning(f"Snippet truncated to {max_chars} chars")
    
    # Build user prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(snippet=snippet)
    
    # Converse API request
    try:
        response = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": user_prompt}],
                }
            ],
            system=[{"text": SYSTEM_PROMPT}],
            toolConfig={
                "tools": [CLASSIFICATION_TOOL],
                "toolChoice": {"any": {}},  # Force tool use
            },
            inferenceConfig={
                "temperature": 0.0,
                "maxTokens": 60,
            },
        )
        
        # Extract tool use from response
        output = response.get("output", {})
        message = output.get("message", {})
        content = message.get("content", [])
        
        # Find toolUse block
        tool_use = None
        for block in content:
            if "toolUse" in block:
                tool_use = block["toolUse"]
                break
        
        if not tool_use:
            logger.error("No toolUse block in response")
            return {
                "label": "Other/Unknown",
                "confidence": 0.0,
                "reason": "tool_use_missing",
            }
        
        # Extract tool input (this is our classification JSON)
        tool_input = tool_use.get("input", {})
        
        # Validate and return
        label = tool_input.get("label", "Other/Unknown")
        confidence = float(tool_input.get("confidence", 0.0))
        reason = tool_input.get("reason", "")
        
        # Ensure label is valid
        if label not in VALID_LABELS:
            logger.warning(f"Invalid label '{label}', defaulting to Other/Unknown")
            label = "Other/Unknown"
        
        # Clamp confidence
        confidence = max(0.0, min(1.0, confidence))
        
        # Truncate reason if needed
        if len(reason) > 100:
            reason = reason[:97] + "..."
        
        return {
            "label": label,
            "confidence": confidence,
            "reason": reason,
        }
        
    except Exception as e:
        logger.error(f"Bedrock API error: {e}")
        return {
            "label": "Other/Unknown",
            "confidence": 0.0,
            "reason": f"error: {str(e)[:50]}",
        }


def _conversation_to_snippet(conversation: Conversation) -> str:
    """Convert Conversation object to a text snippet for classification.
    
    Creates a compact representation of the conversation for the classifier.
    
    Args:
        conversation: Conversation object with messages
        
    Returns:
        Text snippet (multi-line string with role and content)
    """
    lines = []
    # Take up to 8 messages (to keep snippet short)
    messages = conversation.messages[:8]
    
    for msg in messages:
        # Truncate long messages
        content = msg.content[:200]
        if len(msg.content) > 200:
            content += "..."
        lines.append(f"{msg.role}: {content}")
    
    if len(conversation.messages) > 8:
        lines.append(f"... ({len(conversation.messages) - 8} more messages)")
    
    return "\n".join(lines)


def classify_conversation(conversation: Conversation) -> str:
    """Classify a conversation into a task category.
    
    Converts the conversation to a snippet and calls classify_snippet().
    Returns the label string to be stored in conversation.task_category.
    
    Args:
        conversation: Conversation to classify
        
    Returns:
        Task category string (one of VALID_LABELS)
    """
    snippet = _conversation_to_snippet(conversation)
    result = classify_snippet(snippet)
    
    # Log classification for debugging
    logger.info(
        f"Classified conversation {conversation.conversation_id}: "
        f"{result['label']} (confidence={result['confidence']:.2f})"
    )
    
    return result["label"]


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
