#!/bin/bash
set -e

echo "🚀 Starting Birthday Bot deployment..."

# Check for .env file
if [ ! -f .env ]; then
    echo "❌ .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Load environment variables
echo "🔧 Loading environment variables..."
set -a
source .env
set +a

# Create required directories
echo "📁 Creating required directories..."
mkdir -p data certs

# Set proper permissions for data directory
echo "🔐 Setting directory permissions..."
chmod 755 data
# Ensure the data directory is writable by the container user (uid 1000)
sudo chown -R 1000:1000 data || chown -R 1000:1000 data 2>/dev/null || true

# Check for certificates
if [ ! -f "certs/ldapcertificate.crt" ] || [ ! -f "certs/ldapcertificate.key" ]; then
    echo "❌ LDAP certificates not found in certs/ directory"
    echo "   Please copy ldapcertificate.crt and ldapcertificate.key to the certs/ directory"
    exit 1
fi

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check for Cloudflare tunnel token
if [ -z "${CLOUDFLARE_TUNNEL_TOKEN}" ]; then
    echo "⚠️  Warning: CLOUDFLARE_TUNNEL_TOKEN not set"
    echo "   The service will only be accessible locally without the tunnel"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# GHCR Authentication for private registries
if [ -n "${GITHUB_TOKEN}" ]; then
    echo "🔐 Authenticating with GitHub Container Registry..."
    echo "${GITHUB_TOKEN}" | docker login ghcr.io -u "${GITHUB_USERNAME:-username}" --password-stdin
fi

# Pull latest images
echo "📦 Pulling latest container images..."
docker compose pull

# Deploy services
echo "🛑 Stopping existing services..."
docker compose down

echo "▶️  Starting services..."
docker compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Verify deployment
echo "🔍 Checking service status..."
docker compose ps

# Check health
echo "🏥 Checking service health..."
if curl -f http://localhost:5000/api/status > /dev/null 2>&1; then
    echo "✅ Birthday Bot is healthy and running!"
    echo "🌐 Dashboard available at: http://localhost:5000"
    
    # Check if Cloudflare tunnel is configured
    if [ -n "${CLOUDFLARE_TUNNEL_TOKEN}" ]; then
        echo "🌍 Cloudflare tunnel is configured - check your tunnel dashboard for the public URL"
    fi
    
    # Check if Slack notifications are enabled
    if [ "${SLACK_NOTIFICATIONS_ENABLED}" = "true" ]; then
        echo "📢 Slack notifications are ENABLED"
    else
        echo "🔕 Slack notifications are DISABLED (test mode)"
    fi
else
    echo "❌ Service health check failed"
    echo "📋 Checking logs..."
    docker compose logs --tail=50 birthdays-to-slack
fi

echo ""
echo "📋 Useful commands:"
echo "   docker compose logs -f          # View logs"
echo "   docker compose down             # Stop services"
echo "   docker compose restart          # Restart services"
echo "   docker compose ps               # Check status"