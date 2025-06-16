#!/bin/bash
# Fix permissions for the birthday bot data directory

echo "🔧 Fixing data directory permissions..."

# Create data directory if it doesn't exist
mkdir -p data

# Set ownership to match container user (uid 1000)
if command -v sudo >/dev/null 2>&1; then
    sudo chown -R 1000:1000 data
else
    chown -R 1000:1000 data
fi

# Set proper permissions
chmod -R 755 data

echo "✅ Permissions fixed!"
echo ""
echo "Now restart the containers:"
echo "  docker compose down"
echo "  docker compose up -d"