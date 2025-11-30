# Multi-stage build (Python example). Adjust to your language/project as needed.
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies if requirements.txt exists
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc git \
    && pip install --upgrade pip \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi \
    && apt-get remove -y build-essential gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . .

# Startup script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Default startup command using START_CMD
ENV START_CMD="python main.py"
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sh", "-c", "$START_CMD"]
