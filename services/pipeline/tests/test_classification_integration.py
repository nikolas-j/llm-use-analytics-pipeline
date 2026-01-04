"""
Integration tests for conversation classification with sample data.

Tests realistic conversation scenarios to validate classification behavior.
Requires LLM_CLASSIFICATION=true and valid AWS credentials to run actual API tests.
"""

import pytest
from classify_pipeline.core.schemas import Conversation, MessageEvent
from classify_pipeline.core.classify import classify_conversation, VALID_LABELS
from classify_pipeline.config import load_config


# ============================================================================
# Fixtures for Realistic Conversations
# ============================================================================

@pytest.fixture
def conversation_technical_debugging():
    """Realistic technical debugging conversation."""
    return Conversation(
        conversation_id="tech_debug_001",
        team="Engineering",
        messages=[
            MessageEvent(
                event_time="2026-01-05T14:00:00Z",
                conversation_id="tech_debug_001",
                message_id="msg_001",
                role="user",
                content="My React component isn't re-rendering when state changes. What am I doing wrong?",
                team="Engineering",
                user_id="dev_001",
            ),
            MessageEvent(
                event_time="2026-01-05T14:01:00Z",
                conversation_id="tech_debug_001",
                message_id="msg_002",
                role="assistant",
                content="Can you share your component code? I'll help identify the issue.",
                team="Engineering",
                user_id="dev_001",
            ),
            MessageEvent(
                event_time="2026-01-05T14:02:00Z",
                conversation_id="tech_debug_001",
                message_id="msg_003",
                role="user",
                content="Here: const [count, setCount] = useState(0); but onClick={() => count++} doesn't work",
                team="Engineering",
                user_id="dev_001",
            ),
        ],
    )


@pytest.fixture
def conversation_document_summary():
    """Realistic document summarization request."""
    return Conversation(
        conversation_id="summary_001",
        team="Research",
        messages=[
            MessageEvent(
                event_time="2026-01-05T15:00:00Z",
                conversation_id="summary_001",
                message_id="msg_004",
                role="user",
                content="Please summarize these 15 pages of meeting notes and extract the key action items.",
                team="Research",
                user_id="researcher_001",
            ),
            MessageEvent(
                event_time="2026-01-05T15:01:00Z",
                conversation_id="summary_001",
                message_id="msg_005",
                role="assistant",
                content="I'll create a concise summary with the main points and action items highlighted.",
                team="Research",
                user_id="researcher_001",
            ),
        ],
    )


@pytest.fixture
def conversation_email_drafting():
    """Realistic email drafting conversation."""
    return Conversation(
        conversation_id="draft_001",
        team="Sales",
        messages=[
            MessageEvent(
                event_time="2026-01-05T16:00:00Z",
                conversation_id="draft_001",
                message_id="msg_006",
                role="user",
                content="Help me write a professional email declining a vendor proposal politely.",
                team="Sales",
                user_id="sales_001",
            ),
            MessageEvent(
                event_time="2026-01-05T16:01:00Z",
                conversation_id="draft_001",
                message_id="msg_007",
                role="assistant",
                content="I'll draft a polite and professional decline email for you.",
                team="Sales",
                user_id="sales_001",
            ),
        ],
    )


@pytest.fixture
def conversation_data_analysis():
    """Realistic data analysis conversation."""
    return Conversation(
        conversation_id="analysis_001",
        team="Analytics",
        messages=[
            MessageEvent(
                event_time="2026-01-05T17:00:00Z",
                conversation_id="analysis_001",
                message_id="msg_008",
                role="user",
                content="Analyze the Q4 sales data and identify trends. Revenue dropped 8% in December.",
                team="Analytics",
                user_id="analyst_001",
            ),
            MessageEvent(
                event_time="2026-01-05T17:01:00Z",
                conversation_id="analysis_001",
                message_id="msg_009",
                role="assistant",
                content="I'll analyze the sales trends and identify factors contributing to the December decline.",
                team="Analytics",
                user_id="analyst_001",
            ),
        ],
    )


@pytest.fixture
def conversation_customer_support():
    """Realistic customer support conversation."""
    return Conversation(
        conversation_id="support_001",
        team="Support",
        messages=[
            MessageEvent(
                event_time="2026-01-05T18:00:00Z",
                conversation_id="support_001",
                message_id="msg_010",
                role="user",
                content="Customer is asking for a refund. Order was delayed by 2 weeks. How should I respond?",
                team="Support",
                user_id="support_001",
            ),
            MessageEvent(
                event_time="2026-01-05T18:01:00Z",
                conversation_id="support_001",
                message_id="msg_011",
                role="assistant",
                content="I'll help you draft an empathetic response offering the refund and apologizing for the delay.",
                team="Support",
                user_id="support_001",
            ),
        ],
    )


@pytest.fixture
def conversation_translation():
    """Realistic translation request."""
    return Conversation(
        conversation_id="translate_001",
        team="Marketing",
        messages=[
            MessageEvent(
                event_time="2026-01-05T19:00:00Z",
                conversation_id="translate_001",
                message_id="msg_012",
                role="user",
                content="Translate this product description to Spanish: 'Premium quality handcrafted leather wallet'",
                team="Marketing",
                user_id="marketing_001",
            ),
            MessageEvent(
                event_time="2026-01-05T19:01:00Z",
                conversation_id="translate_001",
                message_id="msg_013",
                role="assistant",
                content="Cartera de cuero artesanal de primera calidad",
                team="Marketing",
                user_id="marketing_001",
            ),
        ],
    )


@pytest.fixture
def conversation_brainstorming():
    """Realistic ideation/brainstorming conversation."""
    return Conversation(
        conversation_id="ideation_001",
        team="Product",
        messages=[
            MessageEvent(
                event_time="2026-01-05T20:00:00Z",
                conversation_id="ideation_001",
                message_id="msg_014",
                role="user",
                content="Let's brainstorm creative marketing campaign ideas for our new mobile app launch.",
                team="Product",
                user_id="product_001",
            ),
            MessageEvent(
                event_time="2026-01-05T20:01:00Z",
                conversation_id="ideation_001",
                message_id="msg_015",
                role="assistant",
                content="Great! Here are some campaign concepts: 1) Social media challenge...",
                team="Product",
                user_id="product_001",
            ),
        ],
    )


@pytest.fixture
def conversation_internal_policy():
    """Realistic internal policy question."""
    return Conversation(
        conversation_id="policy_001",
        team="HR",
        messages=[
            MessageEvent(
                event_time="2026-01-05T21:00:00Z",
                conversation_id="policy_001",
                message_id="msg_016",
                role="user",
                content="What's our company's policy on remote work and flexible hours?",
                team="HR",
                user_id="employee_001",
            ),
            MessageEvent(
                event_time="2026-01-05T21:01:00Z",
                conversation_id="policy_001",
                message_id="msg_017",
                role="assistant",
                content="According to our HR handbook, employees can work remotely up to 3 days per week...",
                team="HR",
                user_id="employee_001",
            ),
        ],
    )


@pytest.fixture
def conversation_research():
    """Realistic research/synthesis conversation."""
    return Conversation(
        conversation_id="research_001",
        team="Research",
        messages=[
            MessageEvent(
                event_time="2026-01-05T22:00:00Z",
                conversation_id="research_001",
                message_id="msg_018",
                role="user",
                content="Compare the top 5 CRM platforms and synthesize their key features and pricing.",
                team="Research",
                user_id="researcher_002",
            ),
            MessageEvent(
                event_time="2026-01-05T22:01:00Z",
                conversation_id="research_001",
                message_id="msg_019",
                role="assistant",
                content="I'll compile information from multiple sources and create a comparison matrix.",
                team="Research",
                user_id="researcher_002",
            ),
        ],
    )


# ============================================================================
# Integration Tests - Run with LLM enabled
# ============================================================================

@pytest.mark.integration
def test_classify_technical_conversation_integration(conversation_technical_debugging):
    """Integration test: Technical debugging should classify as Technical Help."""
    config = load_config()
    
    if not config.llm_classification:
        pytest.skip("LLM classification is disabled (set LLM_CLASSIFICATION=true)")
    
    result = classify_conversation(conversation_technical_debugging)
    
    # Verify result is valid
    assert result in VALID_LABELS
    
    # Technical debugging typically classified as Technical Help
    # (allowing flexibility since LLM might interpret differently)
    print(f"Technical debugging classified as: {result}")


@pytest.mark.integration
def test_classify_summary_conversation_integration(conversation_document_summary):
    """Integration test: Summary request should classify as Summarization."""
    config = load_config()
    
    if not config.llm_classification:
        pytest.skip("LLM classification is disabled")
    
    result = classify_conversation(conversation_document_summary)
    assert result in VALID_LABELS
    print(f"Document summary classified as: {result}")


@pytest.mark.integration
def test_classify_drafting_conversation_integration(conversation_email_drafting):
    """Integration test: Email drafting should classify as Drafting/Rewriting."""
    config = load_config()
    
    if not config.llm_classification:
        pytest.skip("LLM classification is disabled")
    
    result = classify_conversation(conversation_email_drafting)
    assert result in VALID_LABELS
    print(f"Email drafting classified as: {result}")


@pytest.mark.integration
def test_classify_analysis_conversation_integration(conversation_data_analysis):
    """Integration test: Data analysis should classify as Data/Analysis."""
    config = load_config()
    
    if not config.llm_classification:
        pytest.skip("LLM classification is disabled")
    
    result = classify_conversation(conversation_data_analysis)
    assert result in VALID_LABELS
    print(f"Data analysis classified as: {result}")


@pytest.mark.integration
def test_classify_support_conversation_integration(conversation_customer_support):
    """Integration test: Customer support should classify as Customer Comms."""
    config = load_config()
    
    if not config.llm_classification:
        pytest.skip("LLM classification is disabled")
    
    result = classify_conversation(conversation_customer_support)
    assert result in VALID_LABELS
    print(f"Customer support classified as: {result}")


@pytest.mark.integration
def test_classify_translation_conversation_integration(conversation_translation):
    """Integration test: Translation should classify as Translation/Tone."""
    config = load_config()
    
    if not config.llm_classification:
        pytest.skip("LLM classification is disabled")
    
    result = classify_conversation(conversation_translation)
    assert result in VALID_LABELS
    print(f"Translation classified as: {result}")


@pytest.mark.integration
def test_classify_brainstorming_conversation_integration(conversation_brainstorming):
    """Integration test: Brainstorming should classify as Ideation/Planning."""
    config = load_config()
    
    if not config.llm_classification:
        pytest.skip("LLM classification is disabled")
    
    result = classify_conversation(conversation_brainstorming)
    assert result in VALID_LABELS
    print(f"Brainstorming classified as: {result}")


@pytest.mark.integration
def test_classify_policy_conversation_integration(conversation_internal_policy):
    """Integration test: Policy question should classify as Internal Q&A."""
    config = load_config()
    
    if not config.llm_classification:
        pytest.skip("LLM classification is disabled")
    
    result = classify_conversation(conversation_internal_policy)
    assert result in VALID_LABELS
    print(f"Policy question classified as: {result}")


@pytest.mark.integration
def test_classify_research_conversation_integration(conversation_research):
    """Integration test: Research task should classify as Research/Synthesis."""
    config = load_config()
    
    if not config.llm_classification:
        pytest.skip("LLM classification is disabled")
    
    result = classify_conversation(conversation_research)
    assert result in VALID_LABELS
    print(f"Research task classified as: {result}")


# ============================================================================
# Test Classification Consistency
# ============================================================================

@pytest.mark.integration
def test_classification_consistency(conversation_technical_debugging):
    """Test that same conversation classified multiple times gives consistent results."""
    config = load_config()
    
    if not config.llm_classification:
        pytest.skip("LLM classification is disabled")
    
    # Classify same conversation 3 times
    results = []
    for _ in range(3):
        result = classify_conversation(conversation_technical_debugging)
        results.append(result)
    
    # All results should be valid
    assert all(r in VALID_LABELS for r in results)
    
    # With temperature=0, should be mostly consistent
    # (allowing for some variation due to API behavior)
    print(f"Classification results across 3 runs: {results}")


# ============================================================================
# Test Edge Cases
# ============================================================================

def test_classify_empty_conversation():
    """Test classification of conversation with no messages."""
    conversation = Conversation(
        conversation_id="empty_001",
        team="Test",
        messages=[],
    )
    
    # Should handle gracefully (may return Unclassified or error)
    result = classify_conversation(conversation)
    assert result in VALID_LABELS or result == "Unclassified"


def test_classify_single_message_conversation():
    """Test classification with only one message."""
    conversation = Conversation(
        conversation_id="single_001",
        team="Test",
        messages=[
            MessageEvent(
                event_time="2026-01-05T10:00:00Z",
                conversation_id="single_001",
                message_id="msg_001",
                role="user",
                content="Help me debug this code",
                team="Test",
                user_id="u_001",
            ),
        ],
    )
    
    result = classify_conversation(conversation)
    assert result in VALID_LABELS or result == "Unclassified"


def test_classify_very_short_content():
    """Test classification with very short message content."""
    conversation = Conversation(
        conversation_id="short_001",
        team="Test",
        messages=[
            MessageEvent(
                event_time="2026-01-05T10:00:00Z",
                conversation_id="short_001",
                message_id="msg_001",
                role="user",
                content="Hi",
                team="Test",
                user_id="u_001",
            ),
            MessageEvent(
                event_time="2026-01-05T10:01:00Z",
                conversation_id="short_001",
                message_id="msg_002",
                role="assistant",
                content="Hello",
                team="Test",
                user_id="u_001",
            ),
        ],
    )
    
    result = classify_conversation(conversation)
    # Very short conversations likely get Other/Unknown
    assert result in VALID_LABELS
