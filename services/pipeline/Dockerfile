FROM python:3.11-slim

WORKDIR /app

# Copy only runtime dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir boto3 pydantic pydantic-settings python-dotenv

# Copy application code
COPY classify_pipeline/ classify_pipeline/
COPY __init__.py .

# Run as non-root user
RUN useradd -m -u 1000 pipeline && chown -R pipeline:pipeline /app
USER pipeline

# Default command
CMD ["python", "-m", "classify_pipeline.main"]
