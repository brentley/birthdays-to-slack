#!/bin/bash
# Trigger Watchtower to update containers immediately

# Set default values
WATCHTOWER_HOST="${WATCHTOWER_HOST:-localhost}"
WATCHTOWER_PORT="${WATCHTOWER_PORT:-8080}"
WATCHTOWER_API_TOKEN="${WATCHTOWER_API_TOKEN}"

# Check if token is provided
if [ -z "$WATCHTOWER_API_TOKEN" ]; then
    echo "Error: WATCHTOWER_API_TOKEN environment variable is not set"
    echo "Usage: WATCHTOWER_API_TOKEN=your-token ./trigger-update.sh"
    exit 1
fi

echo "Triggering Watchtower update..."

# Call Watchtower HTTP API to trigger update
response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer ${WATCHTOWER_API_TOKEN}" \
    "http://${WATCHTOWER_HOST}:${WATCHTOWER_PORT}/v1/update")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 204 ]; then
    echo "✅ Update triggered successfully!"
    if [ -n "$body" ]; then
        echo "Response: $body"
    fi
else
    echo "❌ Failed to trigger update. HTTP Status: $http_code"
    if [ -n "$body" ]; then
        echo "Error: $body"
    fi
    exit 1
fi