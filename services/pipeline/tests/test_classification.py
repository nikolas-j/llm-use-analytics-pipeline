"""
Unit tests for conversation classification.

Tests classification logic including:
- Bypass mode (LLM disabled)
- Real classification (LLM enabled)
- Different conversation types
- Error handling
- Batch classification
"""

import pytest
from unittest.mock import patch, MagicMock

from classify_pipeline.core.classify import (
    classify_snippet,
    classify_conversation,
    classify_conversations,
    VALID_LABELS,
)
from classify_pipeline.core.schemas import Conversation, MessageEvent


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_messages_technical():
    """Create sample messages for a technical help conversation."""
    return [
        MessageEvent(
            event_time="2026-01-05T10:00:00Z",
            conversation_id="tech_001",
            message_id="msg_001",
            role="user",
            content="I'm getting a KeyError in my Python script when accessing user_id",
            team="Engineering",
            user_id="u_100",
        ),
        MessageEvent(
            event_time="2026-01-05T10:01:00Z",
            conversation_id="tech_001",
            message_id="msg_002",
            role="assistant",
            content="Can you share the full traceback? That will help me understand the issue.",
            team="Engineering",
            user_id="u_100",
        ),
        MessageEvent(
            event_time="2026-01-05T10:02:00Z",
            conversation_id="tech_001",
            message_id="msg_003",
            role="user",
            content="Here it is: KeyError: 'user_id' at line 42 in process_data()",
            team="Engineering",
            user_id="u_100",
        ),
    ]


@pytest.fixture
def sample_messages_customer_support():
    """Create sample messages for customer support conversation."""
    return [
        MessageEvent(
            event_time="2026-01-05T11:00:00Z",
            conversation_id="support_001",
            message_id="msg_004",
            role="user",
            content="My order #12345 hasn't arrived yet. It's been 10 days.",
            team="Support",
            user_id="u_200",
        ),
        MessageEvent(
            event_time="2026-01-05T11:01:00Z",
            conversation_id="support_001",
            message_id="msg_005",
            role="assistant",
            content="I'll check the status of your order right away and get back to you.",
            team="Support",
            user_id="u_200",
        ),
    ]


@pytest.fixture
def sample_messages_summarization():
    """Create sample messages for summarization task."""
    return [
        MessageEvent(
            event_time="2026-01-05T12:00:00Z",
            conversation_id="sum_001",
            message_id="msg_006",
            role="user",
            content="Can you summarize this 10-page report for me? I need the key points.",
            team="Sales",
            user_id="u_300",
        ),
        MessageEvent(
            event_time="2026-01-05T12:01:00Z",
            conversation_id="sum_001",
            message_id="msg_007",
            role="assistant",
            content="I'll create a concise summary highlighting the main findings.",
            team="Sales",
            user_id="u_300",
        ),
    ]


@pytest.fixture
def technical_conversation(sample_messages_technical):
    """Create a complete technical conversation."""
    return Conversation(
        conversation_id="tech_001",
        team="Engineering",
        messages=sample_messages_technical,
    )


@pytest.fixture
def support_conversation(sample_messages_customer_support):
    """Create a complete customer support conversation."""
    return Conversation(
        conversation_id="support_001",
        team="Support",
        messages=sample_messages_customer_support,
    )


@pytest.fixture
def summarization_conversation(sample_messages_summarization):
    """Create a complete summarization conversation."""
    return Conversation(
        conversation_id="sum_001",
        team="Sales",
        messages=sample_messages_summarization,
    )


# ============================================================================
# Test Bypass Mode (LLM_CLASSIFICATION=false)
# ============================================================================

@patch('classify_pipeline.core.classify._config')
def test_classify_snippet_bypass_mode(mock_config):
    """Test that bypass mode returns 'Unclassified' without API calls."""
    # Configure bypass mode
    mock_config.llm_classification = False
    
    result = classify_snippet("Any text here")
    
    assert result["label"] == "Unclassified"
    assert result["confidence"] == 0.0
    assert "disabled" in result["reason"].lower()


@patch('classify_pipeline.core.classify._config')
def test_classify_conversation_bypass_mode(mock_config, technical_conversation):
    """Test conversation classification in bypass mode."""
    mock_config.llm_classification = False
    
    label = classify_conversation(technical_conversation)
    
    assert label == "Unclassified"


@patch('classify_pipeline.core.classify._config')
def test_classify_conversations_bypass_mode(
    mock_config, technical_conversation, support_conversation
):
    """Test batch classification in bypass mode."""
    mock_config.llm_classification = False
    
    conversations = [technical_conversation, support_conversation]
    result = classify_conversations(conversations)
    
    assert len(result) == 2
    assert all(conv.task_category == "Unclassified" for conv in result)


# ============================================================================
# Test Classification Output Schema
# ============================================================================

@patch('classify_pipeline.core.classify._config')
@patch('classify_pipeline.core.classify.boto3')
def test_classify_snippet_output_schema(mock_boto3, mock_config):
    """Test that classification returns correct schema."""
    # Configure for LLM mode
    mock_config.llm_classification = True
    mock_config.bedrock_region = "eu-north-1"
    mock_config.bedrock_model_id = "eu.amazon.nova-micro-v1:0"
    mock_config.bedrock_connect_timeout = 2
    mock_config.bedrock_read_timeout = 5
    mock_config.bedrock_max_retries = 2
    
    # Mock successful Bedrock response
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.converse.return_value = {
        "output": {
            "message": {
                "content": [
                    {
                        "toolUse": {
                            "input": {
                                "label": "Technical Help",
                                "confidence": 0.95,
                                "reason": "User requesting code debugging",
                            }
                        }
                    }
                ]
            }
        }
    }
    
    result = classify_snippet("Debug my code")
    
    # Verify schema
    assert "label" in result
    assert "confidence" in result
    assert "reason" in result
    
    # Verify types
    assert isinstance(result["label"], str)
    assert isinstance(result["confidence"], float)
    assert isinstance(result["reason"], str)
    
    # Verify constraints
    assert result["label"] in VALID_LABELS
    assert 0.0 <= result["confidence"] <= 1.0
    assert len(result["reason"]) <= 100


@patch('classify_pipeline.core.classify._config')
@patch('classify_pipeline.core.classify.boto3')
def test_classify_snippet_valid_labels(mock_boto3, mock_config):
    """Test that only valid labels are returned."""
    mock_config.llm_classification = True
    mock_config.bedrock_region = "eu-north-1"
    mock_config.bedrock_model_id = "eu.amazon.nova-micro-v1:0"
    mock_config.bedrock_connect_timeout = 2
    mock_config.bedrock_read_timeout = 5
    mock_config.bedrock_max_retries = 2
    
    # Mock response with valid label
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.converse.return_value = {
        "output": {
            "message": {
                "content": [
                    {
                        "toolUse": {
                            "input": {
                                "label": "Summarization",
                                "confidence": 0.88,
                                "reason": "User wants summary",
                            }
                        }
                    }
                ]
            }
        }
    }
    
    result = classify_snippet("Summarize this document")
    
    assert result["label"] in VALID_LABELS


# ============================================================================
# Test Error Handling
# ============================================================================

@patch('classify_pipeline.core.classify._config')
@patch('classify_pipeline.core.classify.boto3')
def test_classify_snippet_api_error(mock_boto3, mock_config):
    """Test graceful handling of Bedrock API errors."""
    mock_config.llm_classification = True
    mock_config.bedrock_region = "eu-north-1"
    mock_config.bedrock_model_id = "eu.amazon.nova-micro-v1:0"
    mock_config.bedrock_connect_timeout = 2
    mock_config.bedrock_read_timeout = 5
    mock_config.bedrock_max_retries = 2
    
    # Mock API error
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.converse.side_effect = Exception("API Error")
    
    result = classify_snippet("Test snippet")
    
    # Should return Other/Unknown with error message
    assert result["label"] == "Other/Unknown"
    assert result["confidence"] == 0.0
    assert "error" in result["reason"].lower()


@patch('classify_pipeline.core.classify._config')
@patch('classify_pipeline.core.classify.boto3')
def test_classify_snippet_missing_tool_use(mock_boto3, mock_config):
    """Test handling when model doesn't return tool use."""
    mock_config.llm_classification = True
    mock_config.bedrock_region = "eu-north-1"
    mock_config.bedrock_model_id = "eu.amazon.nova-micro-v1:0"
    mock_config.bedrock_connect_timeout = 2
    mock_config.bedrock_read_timeout = 5
    mock_config.bedrock_max_retries = 2
    
    # Mock response without toolUse
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.converse.return_value = {
        "output": {
            "message": {
                "content": [
                    {
                        "text": "Regular text response"
                    }
                ]
            }
        }
    }
    
    result = classify_snippet("Test snippet")
    
    assert result["label"] == "Other/Unknown"
    assert result["confidence"] == 0.0
    assert "tool_use_missing" in result["reason"]


@patch('classify_pipeline.core.classify._config')
@patch('classify_pipeline.core.classify.boto3')
def test_classify_snippet_invalid_label_returned(mock_boto3, mock_config):
    """Test handling when model returns invalid label."""
    mock_config.llm_classification = True
    mock_config.bedrock_region = "eu-north-1"
    mock_config.bedrock_model_id = "eu.amazon.nova-micro-v1:0"
    mock_config.bedrock_connect_timeout = 2
    mock_config.bedrock_read_timeout = 5
    mock_config.bedrock_max_retries = 2
    
    # Mock response with invalid label
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.converse.return_value = {
        "output": {
            "message": {
                "content": [
                    {
                        "toolUse": {
                            "input": {
                                "label": "InvalidCategory",
                                "confidence": 0.75,
                                "reason": "Some reason",
                            }
                        }
                    }
                ]
            }
        }
    }
    
    result = classify_snippet("Test snippet")
    
    # Should default to Other/Unknown for invalid labels
    assert result["label"] == "Other/Unknown"


# ============================================================================
# Test Confidence Clamping
# ============================================================================

@patch('classify_pipeline.core.classify._config')
@patch('classify_pipeline.core.classify.boto3')
def test_classify_snippet_confidence_clamping(mock_boto3, mock_config):
    """Test that confidence values are clamped to [0, 1]."""
    mock_config.llm_classification = True
    mock_config.bedrock_region = "eu-north-1"
    mock_config.bedrock_model_id = "eu.amazon.nova-micro-v1:0"
    mock_config.bedrock_connect_timeout = 2
    mock_config.bedrock_read_timeout = 5
    mock_config.bedrock_max_retries = 2
    
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    
    # Test confidence > 1.0
    mock_client.converse.return_value = {
        "output": {
            "message": {
                "content": [
                    {
                        "toolUse": {
                            "input": {
                                "label": "Technical Help",
                                "confidence": 1.5,
                                "reason": "High confidence",
                            }
                        }
                    }
                ]
            }
        }
    }
    
    result = classify_snippet("Test")
    assert result["confidence"] == 1.0
    
    # Test confidence < 0.0
    mock_client.converse.return_value = {
        "output": {
            "message": {
                "content": [
                    {
                        "toolUse": {
                            "input": {
                                "label": "Technical Help",
                                "confidence": -0.5,
                                "reason": "Negative confidence",
                            }
                        }
                    }
                ]
            }
        }
    }
    
    result = classify_snippet("Test")
    assert result["confidence"] == 0.0


# ============================================================================
# Test Batch Classification
# ============================================================================

@patch('classify_pipeline.core.classify._config')
@patch('classify_pipeline.core.classify.boto3')
def test_classify_conversations_multiple(
    mock_boto3, mock_config, technical_conversation, support_conversation, summarization_conversation
):
    """Test classifying multiple conversations."""
    mock_config.llm_classification = True
    mock_config.bedrock_region = "eu-north-1"
    mock_config.bedrock_model_id = "eu.amazon.nova-micro-v1:0"
    mock_config.bedrock_connect_timeout = 2
    mock_config.bedrock_read_timeout = 5
    mock_config.bedrock_max_retries = 2
    
    # Mock different responses for each call
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    
    responses = [
        {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "input": {
                                    "label": "Technical Help",
                                    "confidence": 0.95,
                                    "reason": "Code debugging",
                                }
                            }
                        }
                    ]
                }
            }
        },
        {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "input": {
                                    "label": "Customer Comms (support/sales)",
                                    "confidence": 0.92,
                                    "reason": "Order inquiry",
                                }
                            }
                        }
                    ]
                }
            }
        },
        {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "input": {
                                    "label": "Summarization",
                                    "confidence": 0.88,
                                    "reason": "Summary request",
                                }
                            }
                        }
                    ]
                }
            }
        },
    ]
    
    mock_client.converse.side_effect = responses
    
    conversations = [technical_conversation, support_conversation, summarization_conversation]
    result = classify_conversations(conversations)
    
    assert len(result) == 3
    assert result[0].task_category == "Technical Help"
    assert result[1].task_category == "Customer Comms (support/sales)"
    assert result[2].task_category == "Summarization"
    
    # Verify all conversations were classified
    assert all(conv.task_category is not None for conv in result)


# ============================================================================
# Test Snippet Truncation
# ============================================================================

@patch('classify_pipeline.core.classify._config')
@patch('classify_pipeline.core.classify.boto3')
def test_classify_snippet_long_text_truncation(mock_boto3, mock_config):
    """Test that very long snippets are truncated."""
    mock_config.llm_classification = True
    mock_config.bedrock_region = "eu-north-1"
    mock_config.bedrock_model_id = "eu.amazon.nova-micro-v1:0"
    mock_config.bedrock_connect_timeout = 2
    mock_config.bedrock_read_timeout = 5
    mock_config.bedrock_max_retries = 2
    
    mock_client = MagicMock()
    mock_boto3.client.return_value = mock_client
    mock_client.converse.return_value = {
        "output": {
            "message": {
                "content": [
                    {
                        "toolUse": {
                            "input": {
                                "label": "Other/Unknown",
                                "confidence": 0.5,
                                "reason": "Truncated text",
                            }
                        }
                    }
                ]
            }
        }
    }
    
    # Create very long snippet (>2000 chars)
    long_snippet = "A" * 3000
    
    result = classify_snippet(long_snippet)
    
    # Should still return valid result (truncation happens internally)
    assert "label" in result
    assert result["label"] in VALID_LABELS


# ============================================================================
# Test Conversation to Snippet Conversion
# ============================================================================

def test_conversation_to_snippet_basic(technical_conversation):
    """Test conversion of conversation to snippet format."""
    from classify_pipeline.core.classify import _conversation_to_snippet
    
    snippet = _conversation_to_snippet(technical_conversation)
    
    # Should contain only user messages
    assert "user:" in snippet.lower()
    assert "KeyError" in snippet
    assert "Python script" in snippet


def test_conversation_to_snippet_truncates_long_conversations():
    """Test that very long conversations are truncated."""
    from classify_pipeline.core.classify import _conversation_to_snippet
    
    # Create conversation with many messages
    messages = []
    for i in range(20):
        messages.append(
            MessageEvent(
                event_time=f"2026-01-05T10:{i:02d}:00Z",
                conversation_id="long_conv",
                message_id=f"msg_{i:03d}",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i} content",
                team="Test",
                user_id="u_test",
            )
        )
    
    conversation = Conversation(
        conversation_id="long_conv",
        team="Test",
        messages=messages,
    )
    
    snippet = _conversation_to_snippet(conversation)
    
    # Should indicate truncation for >8 messages
    assert "more messages" in snippet.lower() or len(snippet) < len(" ".join([m.content for m in messages]))


# ============================================================================
# Test Valid Labels
# ============================================================================

def test_valid_labels_list():
    """Test that VALID_LABELS contains expected categories."""
    expected_labels = [
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
    
    assert len(VALID_LABELS) == len(expected_labels)
    for label in expected_labels:
        assert label in VALID_LABELS
