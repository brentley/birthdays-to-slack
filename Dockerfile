# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF

# Labels
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="https://github.com/visiquate/birthdays-to-slack" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.title="Birthday Bot" \
      org.opencontainers.image.description="Automated birthday notifications for Slack with AI-generated messages"

# Set the working directory in the container
WORKDIR /app

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

# Create non-root user (ec2-user with uid=1000)
RUN useradd -m -u 1000 ec2-user

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY birthday_bot/ ./birthday_bot/

# Create necessary directories
RUN mkdir -p data logs && \
    chown -R ec2-user:ec2-user /app

# Switch to non-root user
USER ec2-user

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Command to run the Flask app
CMD ["python", "-m", "birthday_bot"]

