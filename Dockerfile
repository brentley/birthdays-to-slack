# Multi-stage build for Python apps
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# Add build arguments
ARG GIT_COMMIT=unknown
ARG GIT_COMMIT_SHORT=unknown
ARG BUILD_DATE=unknown
ARG VERSION=1.0.0

# Set as environment variables
ENV GIT_COMMIT=$GIT_COMMIT \
    GIT_COMMIT_SHORT=$GIT_COMMIT_SHORT \
    BUILD_DATE=$BUILD_DATE \
    VERSION=$VERSION \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser birthday_bot/ ./birthday_bot/

# Create necessary directories
RUN mkdir -p data logs prompts/history && \
    chown -R appuser:appuser /app

# Create version info file from build args
RUN echo "{\"git_commit\":\"${GIT_COMMIT}\",\"git_commit_short\":\"${GIT_COMMIT_SHORT}\",\"build_date\":\"${BUILD_DATE}\",\"version\":\"${VERSION}\",\"build_number\":\"0\",\"workflow_run\":\"0\",\"commitHash\":\"${GIT_COMMIT_SHORT}\",\"buildTimestamp\":\"${BUILD_DATE}\"}" > /version.json

# Update PATH
ENV PATH=/home/appuser/.local/bin:$PATH

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "-m", "birthday_bot"]