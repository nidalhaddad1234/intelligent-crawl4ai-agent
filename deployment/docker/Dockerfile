# Multi-stage build for AI-First Web Scraping Agent
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for Playwright
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-feature8.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-feature8.txt

# Install Playwright browsers
RUN playwright install chromium firefox webkit
RUN playwright install-deps

# Production stage
FROM base as production

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/config

# Set permissions
RUN chmod +x /app/start.sh

# Create non-root user
RUN useradd --create-home --shell /bin/bash scraper
RUN chown -R scraper:scraper /app
USER scraper

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

# Expose port
EXPOSE 8888

# Start command
CMD ["python", "web_ui_server.py"]
