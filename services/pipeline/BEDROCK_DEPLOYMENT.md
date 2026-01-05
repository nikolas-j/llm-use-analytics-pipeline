# Bedrock Classification

## Model: Amazon Nova Micro

- **Model ID**: `eu.amazon.nova-micro-v1:0` (inference profile format)
- **Region**: eu-north-1
- **API**: Bedrock Converse API with Tool Use

## JSON Enforcement

Uses **Tool Use** feature to guarantee strict JSON output:
- `toolChoice={"any": {}}` forces model to call classification tool
- `inputSchema` defines exact JSON structure: `{label, confidence, reason}`
- Model cannot return free-form text, only structured tool calls

## Changing Models

Edit `.env` file:
```bash
BEDROCK_MODEL_ID=eu.amazon.nova-micro-v1:0  # Current
# BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0  # Example alternative
BEDROCK_REGION=eu-north-1
```

For different models, adjust timeouts and maxTokens in [classify.py](classify_pipeline/core/classify.py) as needed.

## Performance

| Metric | Value |
|--------|-------|
| **Latency (p50)** | ~200-400ms |
| **Latency (p99)** | ~1-2s |
| **Input Tokens** | ~30-80 |
| **Output Tokens** | ~20-40 |
| **Cost (per 1K calls)** | ~$0.01-0.02 |

## IAM Requirements

ECS Task Role needs:
```json
{
  "Action": "bedrock:InvokeModel",
  "Resource": "arn:aws:bedrock:eu-north-1::foundation-model/eu.amazon.nova-micro-v1:0"
}
```

Enable model access in AWS Console → Bedrock → Model access (eu-north-1).
