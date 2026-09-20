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
COPY zero_api_key_web_search/ ./zero_api_key_web_search/
COPY zero_api_key_web_search_compat/ ./zero_api_key_web_search_compat/

# Install the package
RUN pip install --no-cache-dir -e .

# Expose the MCP server
ENTRYPOINT ["zero-mcp"]
