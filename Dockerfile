FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY requirements.txt .
COPY setup.py .
COPY README.md .
COPY cross_validated_search/ ./cross_validated_search/
COPY free_web_search/ ./free_web_search/

# Install the package
RUN pip install --no-cache-dir -e .

# Expose the MCP server
ENTRYPOINT ["cross-validated-search-mcp"]
