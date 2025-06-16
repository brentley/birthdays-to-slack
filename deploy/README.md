# Birthday Bot Deployment

This directory contains deployment configuration for the Birthday Bot service.

## Quick Start

1. **Copy and configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

2. **Add LDAP certificates:**
   ```bash
   mkdir -p certs
   # Copy your ldapcertificate.crt and ldapcertificate.key to certs/
   ```

3. **Deploy the service:**
   ```bash
   ./deploy.sh
   ```

## Configuration

### Required Environment Variables

- `ICS_URL` - BambooHR calendar feed URL
- `WEBHOOK_URL` - Slack webhook URL for notifications
- `FLASK_SECRET_KEY` - Secret key for Flask sessions (generate a random string)
- `SLACK_NOTIFICATIONS_ENABLED` - Set to `true` to enable Slack notifications

### Optional Configuration

- GitHub Container Registry authentication (for private images)
- Watchtower email notifications for deployment updates

## Service Management

- **View logs:** `docker compose logs -f`
- **Stop services:** `docker compose down`
- **Restart services:** `docker compose restart`
- **Check status:** `docker compose ps`

## Automatic Updates

Watchtower automatically checks for new container images every 5 minutes and updates the service with zero downtime.

## Security Notes

- Keep `.env` file secure and never commit it to version control
- Ensure LDAP certificates have appropriate permissions (read-only)
- Regularly update the Flask secret key
- Monitor Watchtower logs for deployment notifications