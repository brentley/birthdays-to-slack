# Deployment Summary

## Overview

Deployment procedures for the birthdays-to-slack application using Docker Compose. The application is configured for both development and production environments with manual secret management via .env files.

## Configuration Files

1. **docker-compose.yml**
   - Production Docker Compose configuration
   - Services: app, watchtower
   - Loads secrets from `.env` file
   - Health checks configured
   - Watchtower configured for automatic image updates

2. **docker-compose.dev.yml**
   - Development environment overlay
   - Dev-specific services and settings
   - Volume mounts for live code editing
   - Enhanced logging

3. **docker-compose.test.yml**
   - Test environment overlay
   - Test services and settings
   - Test database configuration

4. **.env.example**
   - Template file with all required variables
   - Safe to commit to git (contains example values only)
   - Reference for required secrets: ICS_URL, WEBHOOK_URL, FLASK_SECRET_KEY, OPENAI_API_KEY, SLACK_NOTIFICATIONS_ENABLED

## Documentation

5. **docs/DEPLOYMENT_SUMMARY.md**
   - This file - complete deployment overview
   - Prerequisites and setup instructions
   - Local development and production deployment
   - Deployment procedures
   - Monitoring and health checks
   - Maintenance tasks

## How It Works

### Secret Management Flow

```
.env (manual configuration)
         ↓
  Docker Compose
         ↓
  Environment variables
         ↓
    Containers
```

### Example Usage

```bash
# Development
docker compose -f docker-compose.dev.yml up

# Production
docker compose up -d

# Testing
docker compose -f docker-compose.test.yml up
```

## Security Best Practices

When managing secrets in `.env` files:

- **Never commit .env to git** - Add to `.gitignore` (already configured)
- **Use strong values** - Generate cryptographically secure secrets
- **Restrict file permissions** - `.env` file should be readable by application user only
- **Rotate secrets regularly** - Update API keys and tokens periodically
- **Use different secrets per environment** - Development, staging, and production should have distinct secrets
- **Audit secret access** - Monitor who has access to `.env` files on production servers
- **Backup securely** - Store encrypted backups of `.env` configurations

## Environment Setup

### Local Development

1. **Copy environment template**
   ```bash
   cp .env.example .env
   ```

2. **Update .env with your values**
   ```bash
   # Required variables
   ICS_URL=https://your-calendar-url/birthdays.ics
   WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   FLASK_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   OPENAI_API_KEY=sk-your-api-key-here
   SLACK_NOTIFICATIONS_ENABLED=true
   ```

3. **Verify permissions**
   ```bash
   chmod 600 .env
   ```

### Production Deployment

1. **SSH to production server**
   ```bash
   ssh ec2-user@18.118.142.110
   cd /home/ec2-user/birthdays-to-slack
   ```

2. **Create .env file on server**
   ```bash
   # Use secure methods to transfer the .env file
   # Option 1: scp
   scp .env ec2-user@18.118.142.110:/home/ec2-user/birthdays-to-slack/.env

   # Option 2: SSH and create interactively
   ssh ec2-user@18.118.142.110
   nano .env  # or vi .env
   ```

3. **Set restrictive permissions**
   ```bash
   chmod 600 .env
   chown ec2-user:ec2-user .env
   ```

## Production Deployment Checklist

### Prerequisites
- [ ] EC2 instance running with Docker and Docker Compose installed
- [ ] SSH access to production server configured
- [ ] Application repository cloned on server
- [ ] All required secrets gathered and validated
- [ ] SSL certificates configured (if using HTTPS)

### Required Secrets in .env

1. **ICS_URL** - Calendar ICS feed URL
2. **WEBHOOK_URL** - Slack webhook URL
3. **FLASK_SECRET_KEY** - Flask session secret (use `python -c 'import secrets; print(secrets.token_hex(32))'` to generate)
4. **OPENAI_API_KEY** - OpenAI API key

### Deployment Steps

1. **Login to EC2 Instance**
   ```bash
   ssh ec2-user@18.118.142.110
   ```

2. **Navigate to application directory**
   ```bash
   cd /home/ec2-user/birthdays-to-slack
   ```

3. **Pull latest changes**
   ```bash
   git pull origin main
   ```

4. **Create .env file**
   ```bash
   nano .env  # or vi .env
   # Add your secrets here
   ```

5. **Set proper permissions**
   ```bash
   chmod 600 .env
   chown ec2-user:ec2-user .env
   ```

6. **Pull latest Docker images**
   ```bash
   docker compose pull
   ```

7. **Start application**
   ```bash
   docker compose up -d
   ```

8. **Verify Deployment**
   ```bash
   curl http://localhost:5002/health
   docker compose ps
   docker compose logs -f
   ```

## CI/CD Integration

### GitHub Actions

The build-and-deploy workflow includes:

- **Build stage**: Runs tests and linting
- **Security scanning**: Code and dependency analysis
- **Docker image building**: Creates and pushes container images
- **Deployment trigger**: Can trigger production deployment via webhook

Security scanning includes:
- Python linting and formatting checks
- Dependency vulnerability scanning
- Container image scanning
- Code quality analysis

See `.github/workflows/build-and-deploy.yml` for complete workflow configuration.

## Watchtower Auto-Updates

Watchtower is configured to automatically pull and update Docker images. Configuration:

- **Polling interval**: Checks for new images every 6 hours
- **Auto-restart**: Automatically restarts services when images are updated
- **Notifications**: Can send notifications on updates (optional via SLACK_NOTIFICATIONS_ENABLED)

### Manual Image Updates

If you prefer to control updates manually, you can:

1. **Pull latest images**
   ```bash
   docker compose pull
   ```

2. **Restart services**
   ```bash
   docker compose restart
   ```

Or combine in one step:
```bash
docker compose pull && docker compose up -d
```

## Health Checks

Monitor application health with these commands:

```bash
# Application health endpoint
curl http://localhost:5002/health

# Expected response
{
  "status": "healthy",
  "service": "birthdays-to-slack",
  "version": "1.0.0",
  "commit": "abc123",
  "uptime": 123.45
}

# Docker container status
docker compose ps

# View application logs
docker compose logs -f app

# View all logs
docker compose logs -f
```

## Troubleshooting

### Application won't start

1. **Check logs for errors**
   ```bash
   docker compose logs app
   ```

2. **Verify .env file is present and readable**
   ```bash
   ls -la .env
   cat .env  # (caution: will show secrets)
   ```

3. **Check required environment variables**
   ```bash
   docker compose config | grep -E "(ICS_URL|WEBHOOK_URL|OPENAI_API_KEY)"
   ```

### Container crashes on restart

1. **Check container exit code**
   ```bash
   docker compose ps
   docker compose logs --tail=50 app
   ```

2. **Rebuild containers**
   ```bash
   docker compose down
   docker compose up -d --build
   ```

### Port conflicts

If port 5002 is already in use:

1. **Find process using port**
   ```bash
   lsof -i :5002
   # or
   netstat -tulpn | grep 5002
   ```

2. **Change port in docker-compose.yml or .env**
   ```bash
   # Edit docker-compose.yml and update port mapping
   # ports:
   #   - "5003:5000"  # Changed from 5002:5000
   ```

3. **Restart services**
   ```bash
   docker compose restart
   ```

## Rollback Procedure

If deployment issues occur:

```bash
# Stop current deployment
docker compose down

# Restore previous .env if needed
cp .env.backup .env

# Use previous image tags (if available)
# Edit docker-compose.yml and specify image tags

# Restart with previous configuration
docker compose up -d

# Verify
curl http://localhost:5002/health
```

## Performance Characteristics

- **Startup time**: 2-5 seconds (Docker image pull and container initialization)
- **Runtime**: Minimal impact with Docker Compose overhead
- **Resource usage**: Depends on container resource limits and application load

## Maintenance Tasks

### Daily
- Monitor application health endpoint
- Check Docker logs for errors
- Verify Watchtower image updates completed successfully

### Weekly
- Review application logs for issues
- Verify all services are running
- Test health check endpoint
- Check disk space usage

### Monthly
- Update Docker images manually (or verify Watchtower completed updates)
- Review and rotate secrets if needed
- Test disaster recovery procedures
- Verify backups are working
- Update documentation if needed

### Quarterly
- Full security audit
- Upgrade Docker and Docker Compose
- Review and update deployment procedures
- Performance analysis and optimization

## Support Resources

- **Docker Compose**: https://docs.docker.com/compose/
- **Docker Documentation**: https://docs.docker.com/
- **Flask Documentation**: https://flask.palletsprojects.com/
- **APScheduler**: https://apscheduler.readthedocs.io/
- **Project Docs**: `/docs` directory in repository

## Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/your-org/birthdays-to-slack.git
cd birthdays-to-slack

# Create environment file
cp .env.example .env

# Edit .env with your secrets
nano .env

# Start development environment
docker compose -f docker-compose.dev.yml up
```

### Production Deployment

```bash
# SSH to production server
ssh ec2-user@18.118.142.110
cd /home/ec2-user/birthdays-to-slack

# Create .env file (manually configure secrets)
nano .env

# Set permissions
chmod 600 .env

# Deploy
docker compose up -d

# Verify
curl http://localhost:5002/health
```

## Key Files

### Configuration Files
- `docker-compose.yml` - Production deployment configuration
- `docker-compose.dev.yml` - Development environment overlay
- `docker-compose.test.yml` - Test environment overlay
- `.env.example` - Template for environment variables
- `Dockerfile` - Container image definition

### Documentation Files
- `docs/DEPLOYMENT_SUMMARY.md` - This file
- `docs/` - Additional documentation directory

### Application Files
- `app.py` - Main Flask application
- `birthday_sender.py` - Birthday message generation
- `requirements.txt` - Python dependencies
- `Makefile` - Convenience commands

## Pre-Deployment Checklist

Before deploying to production, verify:

- [ ] All environment variables configured in .env
- [ ] `.env` file has permissions set to 600
- [ ] `.env` is in `.gitignore` (never commit secrets)
- [ ] Docker and Docker Compose installed on server
- [ ] Network ports 5000 and 5002 are available
- [ ] Application repository cloned on server
- [ ] Health check endpoint responds correctly
- [ ] Application logs show no errors
- [ ] Watchtower is running and pulling images

## Status

**Current**: Manual .env file configuration with Docker Compose

**Deployment Method**: Docker Compose with standard `docker compose` commands

**Environment Support**: Development, testing, and production profiles available
