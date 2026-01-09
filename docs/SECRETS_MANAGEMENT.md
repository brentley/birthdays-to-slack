# Secrets Management Guide
## Comprehensive Guide to Secure Credential Handling

---

## Table of Contents

1. [Overview](#overview)
2. [Credential Types](#credential-types)
3. [Local Development Setup](#local-development-setup)
4. [Production Deployment](#production-deployment)
5. [Environment File Security](#environment-file-security)
6. [Credential Rotation](#credential-rotation)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This project requires several credentials to function:
- **Slack Webhook URL** - For sending birthday messages
- **OpenAI API Key** - For generating AI birthday messages
- **LDAP Credentials** - For user validation (optional)
- **Flask Secret Key** - For session security

**Golden Rule:** Never commit credentials to version control.

---

## Credential Types

### Required Credentials

| Credential | Purpose | Format | Rotation Frequency |
|------------|---------|--------|-------------------|
| `WEBHOOK_URL` | Slack integration | `https://hooks.slack.com/services/...` | 90 days |
| `OPENAI_API_KEY` | AI message generation | `sk-proj-...` | 90 days |
| `FLASK_SECRET_KEY` | Session security | Random string | 180 days |

### Optional Credentials

| Credential | Purpose | Format | Rotation Frequency |
|------------|---------|--------|-------------------|
| `LDAP_SERVER` | User validation | `ldaps://ldap.example.com` | Per IT policy |
| `SEARCH_BASE` | LDAP search base | `ou=Users,dc=example,dc=com` | Rarely |
| `CLOUDFLARE_TUNNEL_TOKEN` | Secure tunnel | Token string | 180 days |

---

## Local Development Setup - .env File Management

The `.env` file is the standard way to manage credentials for this project. This file stores sensitive configuration and is kept out of version control.

### Creating Your .env File

1. **Copy the template**
   ```bash
   cp .env.example .env
   ```

2. **Edit with your credentials**
   ```bash
   nano .env
   ```

3. **Add required values**
   ```bash
   # Slack Configuration
   WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX

   # OpenAI Configuration
   OPENAI_API_KEY=sk-proj-your-actual-key-here

   # Flask Configuration
   FLASK_SECRET_KEY=your-secret-key-change-this-in-production

   # Calendar Configuration
   ICS_URL=https://your-calendar-url.com/calendar.ics

   # Feature Flags
   SLACK_NOTIFICATIONS_ENABLED=false  # true for production
   ```

4. **Verify it's protected**
   ```bash
   # Confirm .env is git-ignored
   git status  # Should NOT show .env

   # Verify .gitignore includes .env
   grep "^\.env$" .gitignore

   # Set restrictive file permissions (optional but recommended)
   chmod 600 .env
   ```

---

## Local Development Setup

### First Time Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/visiquate/birthdays-to-slack.git
   cd birthdays-to-slack
   ```

2. **Create .env File**
   ```bash
   cp .env.example .env
   nano .env  # Add your credentials
   chmod 600 .env  # Restrict permissions
   ```

3. **Verify Configuration**
   ```bash
   # Check .env exists and is not committed
   ls -la .env
   git status  # Should NOT show .env

   # Verify .gitignore includes .env
   grep "^\.env$" .gitignore
   ```

4. **Start Development Environment**
   ```bash
   # Option 1: Docker Compose
   docker compose -f docker-compose.dev.yml up --build

   # Option 2: Virtual Environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python birthday_bot/app.py
   ```

5. **Test Credentials**
   ```bash
   # Check health endpoint
   curl http://localhost:5001/health

   # Access dashboard
   open http://localhost:5001
   ```

---

## Production Deployment

### EC2 Production Setup

1. **SSH to Production Server**
   ```bash
   ssh ec2-user@18.118.142.110
   ```

2. **Navigate to Project Directory**
   ```bash
   cd birthdays-to-slack/
   ```

3. **Create/Update .env File**
   ```bash
   # If .env doesn't exist
   cp .env.example .env

   # Edit .env with production credentials
   nano .env
   ```

4. **Set Production Values**
   ```bash
   # Example production .env
   PROJECT_NAME=birthdays-to-slack
   SERVICE_NAME=birthdays-to-slack
   ENVIRONMENT=production

   # Production credentials
   WEBHOOK_URL=https://hooks.slack.com/services/PRODUCTION/WEBHOOK/URL
   OPENAI_API_KEY=sk-proj-production-key
   FLASK_SECRET_KEY=strong-random-production-key

   # Feature flags
   SLACK_NOTIFICATIONS_ENABLED=true

   # LDAP configuration
   LDAP_SERVER=ldaps://ldap.google.com
   SEARCH_BASE=ou=Users,dc=visiquate,dc=com
   ```

5. **Deploy**
   ```bash
   # Pull latest images
   docker compose pull

   # Start services
   docker compose up -d

   # Verify deployment
   docker compose ps
   docker compose logs -f
   ```

6. **Verify Production**
   ```bash
   # Check health endpoint
   curl http://localhost:5002/health

   # Check service status
   docker compose ps
   ```

---

## Environment File Security

### .env File Best Practices

#### Protection Mechanisms

**File Permissions**
```bash
# Set restrictive permissions (owner read/write only)
chmod 600 .env
chmod 600 .env.example

# Verify permissions are set correctly
ls -la .env
# Should show: -rw------- (600)
```

**Git Ignore Configuration**
The repository already includes `.env` in `.gitignore`. Verify this is present:
```bash
cat .gitignore | grep "^\.env$"
```

**Pre-commit Hook**
The project uses pre-commit hooks to detect secrets:
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Pre-commit will scan for common secret patterns before allowing commits
# This prevents accidental credential commits
```

#### Do's and Don'ts

**DO:**
- Keep .env outside version control
- Use restrictive file permissions (chmod 600)
- Store one .env per environment (dev, staging, production)
- Change credentials when leaving the project
- Rotate credentials regularly
- Use strong, unique values for secrets
- Document which credentials are needed in .env.example

**DON'T:**
- Commit .env to git
- Share .env files via email, Slack, or messaging
- Store .env in shared cloud storage
- Copy .env between machines (recreate it instead)
- Use .env from example in production
- Store credentials in source code
- Log or print credential values

#### Team Credential Sharing

When onboarding new team members or sharing credentials:

1. **Via Secure Channel**
   - Use your organization's password manager (1Password, Bitwarden, etc.)
   - Use SSH key-based authentication
   - Never email credentials directly

2. **Setup Instructions**
   - Provide .env.example as template
   - List required environment variables with descriptions
   - Have team member add their own credentials
   - Each person maintains their own .env file

3. **Verification**
   - Confirm their .env is in .gitignore
   - Have them run `git status` to verify it's not staged
   - Test that the application starts successfully
   - Confirm they cannot see others' .env files

---

## Credential Rotation

### When to Rotate

**Scheduled Rotation:**
- Every 90 days for API keys and webhook URLs
- Every 180 days for Flask secret keys
- Quarterly security review

**Immediate Rotation (Required):**
- Suspected credential compromise
- Accidental exposure or commit to git
- Employee departure or access revocation
- Security incident or breach notification
- After testing or development use of production credentials

### Rotation Process

1. **Generate New Credentials**
   - Create new API key in the service (Slack, OpenAI, etc.)
   - Note the old credential for comparison
   - Ensure new credentials work with a test call

2. **Test New Credentials**
   ```bash
   # Update .env with new credentials
   nano .env

   # Test the connection works
   # For Slack:
   curl -X POST -H 'Content-Type: application/json' \
     -d '{"text":"rotation test"}' \
     $WEBHOOK_URL

   # For OpenAI:
   curl https://api.openai.com/v1/chat/completions \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     -d '{"model":"gpt-4","messages":[{"role":"user","content":"test"}],"max_tokens":5}'
   ```

3. **Update Production .env**
   ```bash
   # SSH to production server
   ssh ec2-user@18.118.142.110
   cd birthdays-to-slack/

   # Update .env with new credentials
   nano .env

   # Verify permissions are still restricted
   chmod 600 .env
   ```

4. **Restart Services**
   ```bash
   # Pull latest and restart
   docker compose down
   docker compose pull
   docker compose up -d

   # Verify services are running
   docker compose ps
   docker compose logs -f
   ```

5. **Verify Functionality**
   ```bash
   # Check health endpoint
   curl http://localhost:5002/health

   # Monitor logs for errors
   docker compose logs | grep -i error
   ```

6. **Revoke Old Credentials**
   - Delete or deactivate the old API key in the service
   - Document the rotation in your team's records
   - Update any other applications using the old credential

7. **Communicate with Team**
   - Notify team that credentials have been rotated
   - If team members use shared credentials, update them
   - Document the rotation date for future reference

---

## Troubleshooting

### .env File Not Loading

**Symptom:** Application starts but credentials are empty/undefined

**Diagnosis:**
```bash
# Check if .env exists
ls -la .env

# Check environment variables in container
docker compose exec birthdays-to-slack env | grep -E "WEBHOOK|OPENAI"

# Check docker-compose.yml has env_file directive
grep -A5 "env_file:" docker-compose.yml
```

**Solution:**
```bash
# Ensure .env is in project root
pwd  # Should be birthdays-to-slack/
ls -la .env

# Restart containers to pick up .env changes
docker compose down
docker compose up -d
```

---


### Credentials Don't Work in Production

**Symptom:** Health check fails, API errors in logs

**Diagnosis:**
```bash
# Check logs for credential errors
docker compose logs birthdays-to-slack | grep -i "error\|unauthorized\|401\|403"

# Test credentials manually
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"text":"test"}' \
  $WEBHOOK_URL

# Check OpenAI key
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```

**Solution:**
```bash
# Verify credentials in .env are correct (no extra spaces/quotes)
cat .env | grep -E "WEBHOOK|OPENAI"

# Regenerate credentials if needed
# Follow rotation procedures

# Restart services
docker compose down
docker compose up -d
```

---

### Git Accidentally Shows .env

**Symptom:** `git status` shows .env as untracked or staged

**Diagnosis:**
```bash
# Check git status
git status

# Check if .env is in .gitignore
grep "^\.env$" .gitignore
```

**Solution:**
```bash
# If .env appears in git status:
git reset .env  # Unstage if staged
git update-index --assume-unchanged .env

# Ensure .gitignore has .env
echo ".env" >> .gitignore

# If already committed by mistake:
# 1. IMMEDIATELY rotate all credentials
# 2. Remove from git history (requires force push - coordinate with team)
```

---

### Environment Variables Not Available in Container

**Symptom:** Application logs show "Environment variable not set" errors

**Diagnosis:**
```bash
# Check docker-compose.yml environment section
grep -A20 "environment:" docker-compose.yml

# Check if env_file directive exists
grep "env_file:" docker-compose.yml

# Exec into container and check
docker compose exec birthdays-to-slack env
```

**Solution:**
```bash
# Ensure docker-compose.yml has env_file directive:
services:
  birthdays-to-slack:
    env_file:
      - .env

# Or explicitly list in environment section:
    environment:
      - WEBHOOK_URL=${WEBHOOK_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}

# Restart containers
docker compose down
docker compose up -d
```

---

## Best Practices Summary

### ✅ DO

- Use `.env` file for all credential storage
- Keep `.env` in `.gitignore`
- Use restrictive file permissions (chmod 600)
- Rotate credentials every 90 days (API keys) or 180 days (secret keys)
- Test credentials before deployment
- Monitor application logs for authentication errors
- Document required credentials in .env.example
- Use different credentials for each environment (dev/staging/production)
- Use pre-commit hooks to prevent accidental commits
- Each team member maintains their own .env file

### ❌ DON'T

- Commit credentials or .env files to git
- Share credentials via email, Slack, or messaging apps
- Hardcode credentials in source code or configuration files
- Use production credentials in development environments
- Store credentials in plaintext in documentation or screenshots
- Skip credential rotation schedules
- Ignore security warnings or alerts
- Reuse credentials across multiple projects
- Copy .env files between machines (recreate instead)
- Log or print sensitive values to console

---

## Additional Resources

- [SECURITY.md](../SECURITY.md) - Overall security policy
- [Pre-commit Configuration](.pre-commit-config.yaml) - Secret detection setup
- [Git Ignore Rules](.gitignore) - Version control protection

---

## Questions?

For questions about credential management:
- Review this guide thoroughly
- Check the troubleshooting section
- Consult your team's security policies
- Report any security concerns immediately

---

**Last Updated:** 2026-01-09
