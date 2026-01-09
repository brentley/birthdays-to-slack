# Production Server Setup

This guide covers setting up the production EC2 instance with manual environment configuration.

## Prerequisites

- SSH access to production server (ec2-user@18.118.142.110)
- Docker and Docker Compose installed on server
- All required secrets and credentials documented

## Installation Steps

### 1. Connect to Production Server

```bash
ssh ec2-user@18.118.142.110
```

### 2. Deploy Application Files

```bash
# Navigate to project directory
cd /home/ec2-user/birthdays-to-slack

# Pull latest code
git pull origin main
```

### 3. Create Environment Configuration

Create a `.env` file with your production secrets:

```bash
# Navigate to project directory
cd /home/ec2-user/birthdays-to-slack

# Create .env file with secure permissions
cat > .env << 'EOF'
# Slack Configuration
SLACK_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=C1234567890

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key

# Calendar Configuration
ICS_URL=https://example.com/birthdays.ics

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here

# Slack Notifications
SLACK_NOTIFICATIONS_ENABLED=true

# LDAP Configuration (optional)
LDAP_ENABLED=false
# LDAP_SERVER=ldap://ldap.example.com
# LDAP_BASE_DN=dc=example,dc=com
# LDAP_USER=cn=admin,dc=example,dc=com
# LDAP_PASSWORD=your-password

# Webhook Configuration (optional)
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_SECRET=your-webhook-secret

# Cloudflare Tunnel (optional)
# CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token
EOF

# Set restrictive permissions
chmod 600 .env
```

Ensure all values are properly filled in with your actual credentials.

### 4. Verify Environment File

```bash
# Verify .env file exists and is readable
cat .env | grep -v "^#" | grep -v "^$"

# Check file permissions (should show -rw-------)
ls -la .env
```

### 5. Deploy with Docker Compose

```bash
# Pull latest Docker images
docker compose pull

# Start services
docker compose up -d

# Verify services are running
docker compose ps
```

### 6. Verify Deployment

```bash
# Check service status
docker compose ps

# Check health endpoint
curl http://localhost:5000/health

# View logs
docker compose logs -f
```

Expected health response:
```json
{
  "status": "healthy",
  "service": "birthdays-to-slack",
  "version": "1.0.0",
  "uptime": 45.2
}
```

## Systemd Service Integration

### Create Systemd Service

For automatic startup on server reboot:

```bash
sudo tee /etc/systemd/system/birthdays-to-slack.service << 'EOF'
[Unit]
Description=Birthdays to Slack Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ec2-user/birthdays-to-slack
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=ec2-user
Group=ec2-user

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable birthdays-to-slack

# Start service
sudo systemctl start birthdays-to-slack

# Check status
sudo systemctl status birthdays-to-slack
```

### Service Management Commands

```bash
# Start service
sudo systemctl start birthdays-to-slack

# Stop service
sudo systemctl stop birthdays-to-slack

# Restart service
sudo systemctl restart birthdays-to-slack

# View logs
sudo journalctl -u birthdays-to-slack -f

# Check status
sudo systemctl status birthdays-to-slack
```

## Watchtower Auto-Deployment

Watchtower is included in the docker-compose file and will automatically update containers.

### Watchtower Configuration

The `docker-compose.yml` includes Watchtower with:
- Auto-update every 30 seconds
- Cleanup of old images
- Scoped to birthdays-to-slack only
- Polls Docker registries for new images

### Manual Image Update

To manually trigger an image update without waiting for the scheduled check:

```bash
# Force Watchtower to check for updates immediately
docker compose logs watchtower

# Or manually pull and restart
docker compose pull
docker compose up -d
```

## Monitoring and Health Checks

### Application Health

```bash
# Check health endpoint
curl http://localhost:5000/health

# Detailed health check
curl http://localhost:5000/health | jq
```

### Docker Health

```bash
# Container status
docker compose ps

# Container logs
docker compose logs -f

# Resource usage
docker stats
```

### System Health

```bash
# Disk space
df -h

# Memory usage
free -h

# Docker disk usage
docker system df
```

## Backup and Recovery

### Backup Current State

```bash
# Backup directory
BACKUP_DIR="backups/production-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup configuration (IMPORTANT: Keep .env secure)
cp docker-compose.yml "$BACKUP_DIR/"

# Backup database/state files
docker compose exec birthdays-to-slack tar -czf - /app/data | \
  cat > "$BACKUP_DIR/app-data.tar.gz"
```

Note: The `.env` file contains sensitive secrets and should be backed up to a secure, encrypted storage system separate from this backup process.

### Recovery Procedure

See [BACKUP_STRATEGY.md](BACKUP_STRATEGY.md) for detailed recovery procedures.

## Troubleshooting

### Issue: Environment variables not loaded

```bash
# Verify .env file exists and is readable
ls -la .env

# Check specific environment variable
docker compose exec birthdays-to-slack env | grep SLACK_TOKEN

# Verify Docker Compose is reading the .env file
docker compose config | grep -A5 "environment:"
```

### Issue: Container health check failing

```bash
# Check container logs
docker compose logs birthdays-to-slack

# Check health status
docker inspect birthdays-to-slack | jq '.[0].State.Health'

# Manual health check
docker compose exec birthdays-to-slack curl -f http://localhost:5000/health
```

### Issue: Watchtower not updating

```bash
# Check Watchtower logs
docker compose logs watchtower

# Manually pull latest images
docker compose pull

# Restart all services
docker compose up -d

# Restart Watchtower
docker compose restart watchtower
```

### Issue: Slack API errors

```bash
# Check if SLACK_TOKEN is set
docker compose exec birthdays-to-slack env | grep SLACK_TOKEN

# Verify Slack connection
docker compose exec birthdays-to-slack python -c "from app import test_slack_connection; test_slack_connection()"

# Check application logs for Slack errors
docker compose logs birthdays-to-slack | grep -i slack
```

### Issue: OpenAI API errors

```bash
# Check if OPENAI_API_KEY is set
docker compose exec birthdays-to-slack env | grep OPENAI_API_KEY

# Verify API key is valid
docker compose logs birthdays-to-slack | grep -i openai
```

## Security Best Practices

### 1. Environment File Security

- **Never** commit `.env` file to git (already in `.gitignore`)
- Store `.env` only on the production server
- Use restrictive file permissions: `chmod 600 .env`
- Rotate secrets regularly
- Use separate credentials for staging/production
- Consider using AWS Secrets Manager or similar for credential rotation

### 2. Network Security

```bash
# Ensure firewall is configured
sudo ufw status

# Only allow necessary ports
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP (if using reverse proxy)
sudo ufw allow 443   # HTTPS (if using reverse proxy)

# Block direct access to application port
sudo ufw deny 5000
```

### 3. Access Control

```bash
# Limit SSH access
sudo vim /etc/ssh/sshd_config
# Set: PermitRootLogin no
# Set: PasswordAuthentication no

# Restart SSH
sudo systemctl restart sshd
```

### 4. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker
sudo apt install --only-upgrade docker-ce docker-ce-cli
```

## Maintenance Tasks

### Daily
- [ ] Check application logs for errors
- [ ] Verify health endpoint responds
- [ ] Check Watchtower updated containers

### Weekly
- [ ] Review system resource usage
- [ ] Check disk space
- [ ] Review Docker logs
- [ ] Verify backups are running

### Monthly
- [ ] Test backup/restore procedure
- [ ] Update system packages
- [ ] Review and rotate secrets if needed

### Quarterly
- [ ] Full disaster recovery test
- [ ] Security audit
- [ ] Review and update documentation
- [ ] Performance tuning

## Additional Resources

- [Backup Strategy](BACKUP_STRATEGY.md)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Docker Documentation](https://docs.docker.com/)
