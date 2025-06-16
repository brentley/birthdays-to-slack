#!/bin/bash
set -e

# Deployment sync script for Birthday Bot

SERVER="ec2-user@18.118.142.110"
REMOTE_PATH="birthdays-to-slack/"

echo "🎂 Syncing Birthday Bot deployment files to ${SERVER}:${REMOTE_PATH}"

# Check if deploy directory exists
if [ ! -d "deploy" ]; then
    echo "❌ Deploy directory not found"
    exit 1
fi

# Check if .env exists in deploy directory
if [ ! -f "deploy/.env" ]; then
    echo "⚠️  Warning: deploy/.env not found"
    echo "   You should create deploy/.env with your configuration"
    echo "   Copy deploy/.env.example to deploy/.env and configure it"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Found deploy/.env - this will be synced to the server"
fi

# Check if certificates exist
if [ ! -d "certs" ]; then
    echo "⚠️  Warning: certs/ directory not found"
    echo "LDAP certificates are required for the service to work"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Sync deployment files
echo "📤 Syncing deployment files..."
rsync -avz --delete \
    --exclude '.gitignore' \
    --exclude '*.example' \
    --exclude 'README.md' \
    --exclude '.DS_Store' \
    --exclude '*.swp' \
    --exclude '*.swo' \
    --progress \
    deploy/ ${SERVER}:${REMOTE_PATH}

# Sync certificates if they exist
if [ -d "certs" ]; then
    echo "🔐 Syncing certificates..."
    rsync -avz \
        --exclude '.DS_Store' \
        --progress \
        certs/ ${SERVER}:${REMOTE_PATH}certs/
fi

echo "✅ Sync complete!"
echo ""
echo "📝 Note: Your deploy/.env file has been synced to the server"
echo "   - Make sure it contains production values"
echo "   - Especially FLASK_SECRET_KEY and CLOUDFLARE_TUNNEL_TOKEN"
echo ""
echo "Next steps:"
echo "1. SSH to server: ssh ${SERVER}"
echo "2. Navigate to directory: cd ${REMOTE_PATH}"
echo "3. Verify configuration: cat .env"
echo "4. Run deployment: ./deploy.sh"
echo ""
echo "⚠️  Security reminder:"
echo "   - Keep deploy/.env in .gitignore"
echo "   - Use unique FLASK_SECRET_KEY for production"
echo "   - Set SLACK_NOTIFICATIONS_ENABLED=true when ready"