# Birthday Bot Deployment Guide

This guide covers deploying the Birthday Bot to your production server.

## Prerequisites

- SSH access to server: `ec2-user@18.118.142.110`
- Docker and Docker Compose installed on server
- LDAP certificates (ldapcertificate.crt and ldapcertificate.key)
- OpenAI API key (optional, for AI-generated messages)
- Slack webhook URL

## Local Deployment Preparation

### 1. Configure Environment

**Note:** The `deploy/.env` file WILL be synced to the server. Make sure it contains your production values before deploying.

Local preparation:
```bash
# Create and configure your production environment
cp deploy/.env.example deploy/.env
nano deploy/.env
```

Required environment variables in deploy/.env:
- `ICS_URL` - Your BambooHR calendar feed URL
- `WEBHOOK_URL` - Slack webhook URL for notifications
- `FLASK_SECRET_KEY` - Generate with: `python -c 'import secrets; print(secrets.token_hex(32))'`
- `OPENAI_API_KEY` - Your OpenAI API key (optional)
- `CLOUDFLARE_TUNNEL_TOKEN` - Your Cloudflare tunnel token for external access
- `SLACK_NOTIFICATIONS_ENABLED` - Set to `true` when ready to send messages

### 2. Add LDAP Certificates

```bash
# Create certs directory if it doesn't exist
mkdir -p certs

# Copy your LDAP certificates
cp /path/to/ldapcertificate.crt certs/
cp /path/to/ldapcertificate.key certs/

# Set appropriate permissions
chmod 600 certs/*
```

## Deployment Process

### Option 1: Using Make (Recommended)

```bash
# Deploy to server
make deploy
```

### Option 2: Manual Deployment

```bash
# Run the sync script directly
./sync-deploy.sh
```

## Server Setup (First Time Only)

After syncing files to the server:

### 1. SSH to Server

```bash
ssh ec2-user@18.118.142.110
cd birthdays-to-slack/
```

### 2. Verify Environment

```bash
# The .env file should already be synced from deploy/.env
# Verify it exists and has correct values
cat .env

# If you need to make server-specific changes:
nano .env
```

### 3. Verify Configuration

```bash
# Check environment file exists and is configured
cat .env

# Verify certificates exist
ls -la certs/

# Ensure deploy script is executable
chmod +x deploy.sh
```

### 4. Initial Deployment

```bash
# Run the deployment
./deploy.sh
```

### 5. Verify Service

```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f birthdays-to-slack

# Test the web interface
curl http://localhost:5000/api/status
```

## Ongoing Management

### Updating the Service

The service uses Watchtower for automatic updates:

1. Push changes to GitHub
2. GitHub Actions builds and pushes new image
3. Watchtower automatically pulls and updates within 5 minutes

### Manual Update

```bash
# On the server
cd birthdays-to-slack/
docker compose pull
docker compose up -d
```

### Viewing Logs

```bash
# All logs
docker compose logs -f

# Just birthday bot logs
docker compose logs -f birthdays-to-slack

# Just watchtower logs
docker compose logs -f watchtower
```

### Monitoring

Local access:
- Web Dashboard: http://your-server:5000
- Health Check: http://your-server:5000/api/status
- Upcoming Birthdays: http://your-server:5000/api/birthdays

Cloudflare Tunnel access:
- Check your Cloudflare Zero Trust dashboard for the public URL
- The tunnel provides secure HTTPS access without exposing port 5000

### Troubleshooting

#### Service Won't Start
```bash
# Check logs for errors
docker compose logs birthdays-to-slack

# Verify environment variables
docker compose config

# Check certificate permissions
ls -la certs/
```

#### LDAP Connection Issues
```bash
# Test LDAP connectivity from container
docker compose exec birthdays-to-slack bash
# Then test LDAP connection manually
```

#### OpenAI API Issues
- Verify API key is correct in `.env`
- Check API key has sufficient credits
- Monitor logs for rate limiting

## Security Considerations

1. **Environment File**: Keep `.env` secure and never commit to git
2. **Certificates**: Ensure proper permissions (600) on LDAP certificates
3. **Flask Secret**: Use a strong, random secret key
4. **Cloudflare Tunnel**: Provides secure HTTPS access without exposing ports
5. **Network**: The Cloudflare tunnel eliminates need for port forwarding
6. **Access Control**: Configure access policies in Cloudflare Zero Trust dashboard

## Backup and Recovery

### Backup Generated Messages

```bash
# On server
cd birthdays-to-slack/
tar -czf data-backup-$(date +%Y%m%d).tar.gz data/
```

### Restore from Backup

```bash
# Stop service
docker compose down

# Restore data
tar -xzf data-backup-YYYYMMDD.tar.gz

# Restart service
docker compose up -d
```

## Scheduling Notes

- Birthday checks run daily at 7:00 AM Central Time
- Message generation happens during cache updates (every 6 hours)
- All times are stored in UTC internally
- Dashboard shows times in user's local timezone

## Testing Mode

To test without sending real Slack messages:

1. Set `SLACK_NOTIFICATIONS_ENABLED=false` in `.env`
2. Use the web dashboard to preview messages
3. Check logs to see what would be sent
4. Enable when ready: `SLACK_NOTIFICATIONS_ENABLED=true`

## Support

For issues or questions:
1. Check the logs first: `docker compose logs`
2. Verify all environment variables are set
3. Ensure certificates are present and readable
4. Check the GitHub repository for updates