# Credential Rotation Plan
## Security Response to Trufflehog Findings

**Date Created:** 2025-11-10
**Status:** Action Required
**Priority:** CRITICAL
**Affected Credentials:** Slack Webhook URL, OpenAI API Key

---

## Executive Summary

Trufflehog security scan identified two exposed credentials in git history:
1. **Slack Webhook URL** - Exposed in commit history
2. **OpenAI API Key** - Exposed in commit history

This document provides a comprehensive step-by-step plan to rotate these credentials, update all systems, and implement proper secrets management to prevent future exposure.

---

## Table of Contents

1. [Immediate Actions](#immediate-actions)
2. [Credential Rotation Procedures](#credential-rotation-procedures)
   - [Slack Webhook Rotation](#slack-webhook-rotation)
   - [OpenAI API Key Rotation](#openai-api-key-rotation)
3. [System Update Checklist](#system-update-checklist)
4. [Secrets Management Best Practices](#secrets-management-best-practices)
5. [Verification and Testing](#verification-and-testing)
6. [Post-Rotation Monitoring](#post-rotation-monitoring)
7. [Prevention Measures](#prevention-measures)

---

## Immediate Actions

### 🚨 CRITICAL - Do These First

1. **Revoke Compromised Credentials Immediately**
   - ❌ Revoke current Slack webhook URL
   - ❌ Revoke current OpenAI API key
   - ⏰ Do NOT wait - These are publicly exposed in git history

2. **Generate New Credentials**
   - ✅ Create new Slack webhook URL
   - ✅ Create new OpenAI API key

3. **Update Production Systems**
   - ✅ Update `.env` file on EC2 instance
   - ✅ Restart Docker containers
   - ✅ Verify service health

---

## Credential Rotation Procedures

### Slack Webhook Rotation

#### Understanding Slack Webhooks

A Slack webhook URL provides direct POST access to send messages to a specific Slack channel. If compromised, an attacker can:
- Send spam messages to your channel
- Impersonate your birthday bot
- Potentially disrupt team communications

**Reference:** [How to Rotate Slack Webhooks](https://howtorotate.com/docs/tutorials/slack-webhook/)

#### Step-by-Step Rotation Process

##### Step 1: Generate New Webhook URL

1. **Access Slack App Configuration**
   ```
   Go to: https://api.slack.com/apps
   Select your app: "Birthdays to Slack" (or equivalent)
   Navigate to: Features → Incoming Webhooks
   ```

2. **Create New Webhook**
   ```
   Click: "Add New Webhook to Workspace"
   Select channel: #birthdays (or your target channel)
   Click: "Allow"
   ```

3. **Copy New Webhook URL**
   ```
   Format: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
   Save securely: Copy to password manager or secure note
   ```

##### Step 2: Test New Webhook

Before deploying, verify the new webhook works:

```bash
# Test the new webhook
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message from birthdays-to-slack rotation"}' \
  https://hooks.slack.com/services/YOUR/NEW/WEBHOOK
```

Expected response: `ok`

##### Step 3: Update Production Environment

```bash
# SSH to production server
ssh ec2-user@18.118.142.110

# Navigate to project directory
cd birthdays-to-slack/

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d)

# Edit .env file
nano .env

# Update WEBHOOK_URL line:
# OLD: WEBHOOK_URL=https://hooks.slack.com/services/OLD/WEBHOOK/URL
# NEW: WEBHOOK_URL=https://hooks.slack.com/services/NEW/WEBHOOK/URL

# Save and exit (Ctrl+X, Y, Enter)
```

##### Step 4: Restart Services

```bash
# Pull latest images (if needed)
docker compose pull

# Restart containers with new environment
docker compose down
docker compose up -d

# Verify containers are running
docker compose ps
```

##### Step 5: Verify New Webhook

```bash
# Check application logs
docker compose logs -f birthdays-to-slack

# Check health endpoint
curl http://localhost:5002/health

# Access web UI and test message regeneration
# URL: http://18.118.142.110:5002
```

##### Step 6: Revoke Old Webhook

1. **Return to Slack App Configuration**
   ```
   Go to: https://api.slack.com/apps
   Select your app
   Navigate to: Features → Incoming Webhooks
   ```

2. **Remove Old Webhook**
   ```
   Find the old webhook in the list
   Click: "Remove"
   Confirm: "Yes, remove this webhook"
   ```

3. **Verify Revocation**
   ```bash
   # Test old webhook (should fail)
   curl -X POST \
     -H 'Content-Type: application/json' \
     -d '{"text":"This should fail"}' \
     https://hooks.slack.com/services/OLD/WEBHOOK/URL

   # Expected: Error or "Invalid webhook"
   ```

---

### OpenAI API Key Rotation

#### Understanding OpenAI API Keys

OpenAI API keys provide access to GPT models for generating birthday messages. If compromised, an attacker can:
- Consume your API quota (cost money)
- Generate content under your account
- Potentially access your usage data

**Reference:** [OpenAI API Key Management](https://platform.openai.com/api-keys)

#### Step-by-Step Rotation Process

##### Step 1: Generate New API Key

1. **Access OpenAI Platform**
   ```
   Go to: https://platform.openai.com/api-keys
   Sign in to your account
   ```

2. **Create New API Key**
   ```
   Click: "+ Create new secret key"
   Name: "birthdays-to-slack-production-2025-11"
   Permissions: "All" or "Restricted" (recommended: restrict to GPT-4 only)
   Click: "Create secret key"
   ```

3. **Copy New API Key**
   ```
   Format: sk-proj-XXXXXXXXXXXXXXXXXXXX...
   ⚠️ CRITICAL: Copy immediately - You can't view it again!
   Save securely: Copy to password manager or secure note
   ```

##### Step 2: Test New API Key

Before deploying, verify the new key works:

```bash
# Test the new API key
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-proj-YOUR-NEW-KEY" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 10
  }'
```

Expected response: JSON with completion

##### Step 3: Update Production Environment

```bash
# SSH to production server
ssh ec2-user@18.118.142.110

# Navigate to project directory
cd birthdays-to-slack/

# Backup current .env (if not done already)
cp .env .env.backup.$(date +%Y%m%d)

# Edit .env file
nano .env

# Update OPENAI_API_KEY line:
# OLD: OPENAI_API_KEY=sk-old-key-here
# NEW: OPENAI_API_KEY=sk-proj-new-key-here

# Save and exit (Ctrl+X, Y, Enter)
```

##### Step 4: Restart Services

```bash
# Restart containers with new environment
docker compose down
docker compose up -d

# Verify containers are running
docker compose ps

# Check logs for OpenAI initialization
docker compose logs -f birthdays-to-slack | grep -i openai
```

##### Step 5: Verify New API Key

```bash
# Access web UI
# URL: http://18.118.142.110:5002

# Test message regeneration:
# 1. Navigate to dashboard
# 2. Find an upcoming birthday
# 3. Click "Regenerate Message"
# 4. Verify new AI-generated message appears

# Check application logs for successful API calls
docker compose logs birthdays-to-slack | grep -i "generated message"
```

##### Step 6: Revoke Old API Key

1. **Return to OpenAI Platform**
   ```
   Go to: https://platform.openai.com/api-keys
   ```

2. **Revoke Old Key**
   ```
   Find the old key in the list
   Click: "..." menu
   Click: "Revoke key"
   Confirm: "Revoke"
   ```

3. **Verify Revocation**
   ```bash
   # Test old key (should fail)
   curl https://api.openai.com/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-old-key-here" \
     -d '{
       "model": "gpt-4",
       "messages": [{"role": "user", "content": "test"}],
       "max_tokens": 5
     }'

   # Expected: 401 Unauthorized or Invalid API key
   ```

##### Step 7: Monitor Usage

1. **Check OpenAI Dashboard**
   ```
   Go to: https://platform.openai.com/usage
   Verify: Only authorized usage after rotation
   Monitor: For any unexpected usage patterns
   ```

2. **Set Up Usage Alerts** (Recommended)
   ```
   Go to: https://platform.openai.com/account/billing/limits
   Set: Monthly budget limit
   Enable: Email notifications for usage thresholds
   ```

---

## System Update Checklist

### Production Environment (EC2 Instance)

- [ ] **SSH Access Verified**
  ```bash
  ssh ec2-user@18.118.142.110
  ```

- [ ] **Backup Current Configuration**
  ```bash
  cd birthdays-to-slack/
  cp .env .env.backup.$(date +%Y%m%d)
  ```

- [ ] **Update .env File**
  ```bash
  nano .env
  # Update WEBHOOK_URL
  # Update OPENAI_API_KEY
  ```

- [ ] **Restart Docker Containers**
  ```bash
  docker compose down
  docker compose up -d
  ```

- [ ] **Verify Container Health**
  ```bash
  docker compose ps
  docker compose logs -f
  curl http://localhost:5002/health
  ```

- [ ] **Test Birthday Message Generation**
  - Access web UI: http://18.118.142.110:5002
  - Navigate to dashboard
  - Click "Regenerate Message" for an upcoming birthday
  - Verify message generation succeeds

---

### Local Development Environment

- [ ] **Pull Latest Code**
  ```bash
  cd ~/git/birthdays-to-slack
  git pull origin main
  ```

- [ ] **Backup Local .env**
  ```bash
  cp .env .env.backup.$(date +%Y%m%d)
  ```

- [ ] **Update Local .env**
  ```bash
  # Edit .env with new credentials
  nano .env

  # Update:
  WEBHOOK_URL=https://hooks.slack.com/services/NEW/WEBHOOK/URL
  OPENAI_API_KEY=sk-proj-new-key-here
  ```

- [ ] **Test Locally**
  ```bash
  # Option 1: Virtual environment
  source venv/bin/activate
  python birthday_bot/app.py

  # Option 2: Docker
  docker compose -f docker-compose.dev.yml up --build
  ```

- [ ] **Verify Local Tests Pass**
  ```bash
  pytest tests/ -v
  ```

---

### CI/CD Pipeline (GitHub Actions)

**Current Status:** No CI/CD pipeline detected that uses these credentials

**Future Consideration:** If you add CI/CD workflows that need these credentials:

- [ ] **Add Secrets to GitHub**
  ```bash
  # Navigate to repository settings
  https://github.com/visiquate/birthdays-to-slack/settings/secrets/actions

  # Add repository secrets:
  WEBHOOK_URL: <new-webhook-url>
  OPENAI_API_KEY: <new-api-key>
  ```

- [ ] **Update Workflow Files**
  ```yaml
  # .github/workflows/*.yml
  env:
    WEBHOOK_URL: ${{ secrets.WEBHOOK_URL }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  ```

---

### Docker Containers

- [ ] **Production Container**
  ```bash
  docker compose down
  docker compose pull  # Get latest images
  docker compose up -d
  ```

- [ ] **Development Container**
  ```bash
  docker compose -f docker-compose.dev.yml down
  docker compose -f docker-compose.dev.yml up --build
  ```

- [ ] **Test Container**
  ```bash
  docker compose -f docker-compose.test.yml down
  docker compose -f docker-compose.test.yml up --build
  ```

- [ ] **Verify All Containers**
  ```bash
  docker ps
  docker compose logs -f
  ```

---

## Secrets Management Best Practices

### ✅ Current Implementation (Good)

1. **Environment Variables**
   - ✅ Credentials stored in `.env` file
   - ✅ `.env` file in `.gitignore`
   - ✅ `.env.example` provides template

2. **Docker Integration**
   - ✅ `env_file` directive in docker-compose.yml
   - ✅ Environment variables passed to containers
   - ✅ No hardcoded secrets in Dockerfile

3. **Git Protection**
   - ✅ `.env` in `.gitignore`
   - ✅ `.env.example` without real values

### 🔧 Improvements Needed

1. **Add More Examples**
   - ⚠️ `.env.tpl` exists but references 1Password
   - ✅ Action: Document 1Password integration in README

2. **Secrets Rotation Schedule**
   - ⚠️ No documented rotation schedule
   - ✅ Action: Implement quarterly rotation policy

3. **Audit Logging**
   - ⚠️ No audit trail for credential usage
   - ✅ Action: Add logging for API calls

4. **Secrets Validation**
   - ⚠️ No startup validation of credentials
   - ✅ Action: Add health check for credentials

### 📝 Environment Variable Template (.env.example)

**Current Status:** ✅ Exists and is properly structured

**Review Checklist:**
- [x] No actual secrets included
- [x] Clear placeholder values
- [x] Helpful comments for each variable
- [x] Grouped logically by service
- [x] Documents optional vs required variables

**Recommendation:** No changes needed to `.env.example`

### 🔐 Environment Variable Template Management

**Manual Configuration:**

The recommended approach is to manually manage credentials in your `.env` file:

```bash
# 1. Copy the template file (if needed)
cp .env.example .env

# 2. Edit with your credentials
nano .env

# 3. Add your secrets:
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
OPENAI_API_KEY=sk-proj-your-api-key-here

# 4. Save and secure
chmod 600 .env  # Restrict permissions
```

**Alternative: Using External Secrets Manager**

If you prefer centralized secrets management, consider:
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- GitLab/GitHub Secrets (for CI/CD)

### 🛡️ Git Protection Verification

**Checklist:**
- [x] `.env` in `.gitignore`
- [x] `.env.example` does not contain secrets
- [x] `.env.tpl` does not contain secrets
- [x] `docker-compose.yml` uses `env_file` directive
- [x] No secrets in source code files
- [x] No secrets in Dockerfile

**Verification Command:**
```bash
# Check for potential secrets in tracked files
git ls-files | xargs grep -l "sk-" || echo "No OpenAI keys found"
git ls-files | xargs grep -l "hooks.slack.com" || echo "No webhooks found"
```

### 🔍 Secrets Scanning

**Add to CI/CD Pipeline (Recommended):**

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on: [push, pull_request]

jobs:
  trufflehog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      - name: TruffleHog Scan
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
```

---

## Verification and Testing

### Post-Rotation Verification Steps

#### 1. Service Health Check

```bash
# Check health endpoint
curl -s http://18.118.142.110:5002/health | jq

# Expected output:
{
  "status": "healthy",
  "service": "birthdays-to-slack",
  "version": "1.0.0",
  "checks": {
    "scheduler": "healthy",
    "birthday_service": "healthy",
    "webhook_url": "configured",
    "ics_url": "configured"
  }
}
```

#### 2. Slack Integration Test

```bash
# Access web UI
open http://18.118.142.110:5002

# Manual test:
# 1. Navigate to dashboard
# 2. Find upcoming birthday
# 3. Click "Regenerate Message"
# 4. Verify message appears in Slack channel
```

#### 3. OpenAI Integration Test

```bash
# Check logs for successful OpenAI API calls
docker compose logs birthdays-to-slack | grep -i "openai"
docker compose logs birthdays-to-slack | grep -i "generated message"

# Expected: Successful API responses with message generation
```

#### 4. Scheduler Test

```bash
# Check scheduled jobs
docker compose logs birthdays-to-slack | grep -i "scheduler"

# Expected:
# - "Scheduler started successfully"
# - "Daily Birthday Check" job registered
# - "Birthday Cache Update" job registered
```

#### 5. End-to-End Test

**Test Checklist:**
- [ ] Dashboard loads successfully
- [ ] Upcoming birthdays displayed (21-day preview)
- [ ] "Regenerate Message" button works
- [ ] New AI-generated message appears
- [ ] Message sent to Slack (if enabled)
- [ ] Sent message history updates
- [ ] No error messages in logs

#### 6. Error Condition Tests

**Test Invalid Credentials:**

```bash
# Temporarily use invalid webhook (in test environment)
# Expected: Graceful error handling, logged error message

# Temporarily use invalid OpenAI key (in test environment)
# Expected: Fallback to default message or error logged
```

---

## Post-Rotation Monitoring

### Week 1: Intensive Monitoring

#### Daily Checks (Days 1-7)

- [ ] **Check Application Logs**
  ```bash
  docker compose logs --tail=100 birthdays-to-slack
  ```

- [ ] **Monitor Slack Channel**
  - Verify birthday messages are sent correctly
  - Check for any error messages
  - Ensure message quality is maintained

- [ ] **OpenAI Usage Dashboard**
  - Go to: https://platform.openai.com/usage
  - Monitor daily token usage
  - Check for anomalies

- [ ] **Service Health**
  ```bash
  curl http://18.118.142.110:5002/health
  ```

#### Key Metrics to Watch

| Metric | Expected | Alert If |
|--------|----------|----------|
| Birthday messages sent | 0-5/day | >10/day |
| OpenAI API calls | 0-10/day | >50/day |
| HTTP errors | 0 | >5/day |
| Container restarts | 0 | >2/week |

### Month 1: Regular Monitoring

#### Weekly Checks (Weeks 2-4)

- [ ] **Review Logs for Errors**
  ```bash
  docker compose logs --since 7d birthdays-to-slack | grep -i error
  ```

- [ ] **OpenAI Cost Monitoring**
  - Check monthly usage
  - Compare to historical baseline
  - Verify no unexpected spikes

- [ ] **Slack Integration Health**
  - Confirm messages are being delivered
  - Check message quality
  - Verify no spam or abuse

#### Audit Log Review

```bash
# Check for authentication failures
docker compose logs birthdays-to-slack | grep -i "auth\|unauthorized\|forbidden"

# Check for API rate limits
docker compose logs birthdays-to-slack | grep -i "rate limit\|429"
```

### Ongoing: Quarterly Review

#### Every 3 Months

- [ ] **Credential Rotation**
  - Rotate Slack webhook URL
  - Rotate OpenAI API key
  - Update all systems

- [ ] **Security Audit**
  - Review access logs
  - Check for unusual patterns
  - Verify no exposed secrets

- [ ] **Documentation Update**
  - Update this rotation plan
  - Document any issues encountered
  - Refine procedures based on experience

---

## Prevention Measures

### 🛡️ Git Commit Hooks

**Add Pre-Commit Hook to Prevent Secret Commits:**

```bash
# Install pre-commit framework
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/trufflesecurity/trufflehog
    rev: v3.63.0
    hooks:
      - id: trufflehog
        args:
          - --no-update
          - --fail
        stages: [commit]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
      - id: check-json
      - id: check-yaml
      - id: detect-private-key
      - id: end-of-file-fixer
      - id: trailing-whitespace
EOF

# Install hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

### 🔐 Secrets Management Approaches

**Recommended: Manual .env Management**

This is the primary approach for this project:

```bash
# Edit credentials directly in .env file
nano .env

# Update and save
# Restart services to apply changes
docker compose restart
```

**Optional: AWS Secrets Manager Integration**

If you want centralized secrets management on AWS:

```bash
# Retrieve secrets from AWS
aws secretsmanager get-secret-value \
  --secret-id birthdays-to-slack/production \
  --query SecretString \
  --output text | jq -r 'to_entries[] | "\(.key)=\(.value)"' > .env
```

**Optional: HashiCorp Vault Integration**

For more advanced secret management:

```bash
# Retrieve secrets from Vault
vault kv get -format=json secret/birthdays-to-slack/production | \
  jq -r '.data.data | to_entries[] | "\(.key)=\(.value)"' > .env
```

### 📊 Automated Monitoring

**Add Health Check Monitoring:**

```python
# Add to birthday_bot/app.py
@app.route('/api/credentials-check')
def credentials_check():
    """Verify credentials are working without exposing them"""
    checks = {
        'webhook_url': False,
        'openai_api_key': False
    }

    # Test webhook (without sending message)
    if os.getenv('WEBHOOK_URL'):
        checks['webhook_url'] = True

    # Test OpenAI key (without making API call)
    if os.getenv('OPENAI_API_KEY', '').startswith('sk-'):
        checks['openai_api_key'] = True

    return jsonify(checks)
```

**Add External Monitoring (Recommended):**

```yaml
# Set up uptime monitoring (e.g., UptimeRobot, Pingdom)
Endpoint: http://18.118.142.110:5002/health
Interval: 5 minutes
Alert: Email/Slack on downtime
```

### 📚 Documentation

**Required Documentation:**

1. **README.md Updates**
   - Add "Security" section
   - Link to this rotation plan
   - Document credential management process

2. **SECURITY.md**
   - Create security policy
   - Document responsible disclosure
   - List security best practices

3. **Team Training**
   - Document onboarding process for new team members
   - Include secrets management training
   - Review rotation procedures

### 🔄 Rotation Schedule

**Implement Automated Rotation Reminders:**

```python
# Add to monitoring script or create new script
import datetime

def check_credential_age():
    """Check when credentials were last rotated"""
    rotation_file = '/app/.credential-rotation-history'

    if not os.path.exists(rotation_file):
        logger.warning("No rotation history found - rotate immediately")
        return

    with open(rotation_file, 'r') as f:
        last_rotation = datetime.datetime.fromisoformat(f.read().strip())

    days_since_rotation = (datetime.datetime.now() - last_rotation).days

    if days_since_rotation > 90:  # 3 months
        logger.warning(f"Credentials not rotated in {days_since_rotation} days - rotation recommended")
```

### 🎯 Policy Enforcement

**Create Credential Rotation Policy:**

```markdown
# Credential Rotation Policy

## Schedule
- **Slack Webhooks**: Rotate every 90 days
- **OpenAI API Keys**: Rotate every 90 days
- **Emergency Rotation**: Immediately upon suspected compromise

## Approval Process
1. Security team approval required
2. Change management ticket created
3. Rotation scheduled during maintenance window
4. Post-rotation verification completed

## Responsibilities
- **DevOps Team**: Execute rotation
- **Security Team**: Verify and audit
- **Development Team**: Update local environments
```

---

## Appendix A: Emergency Response

### If Credentials Are Actively Being Abused

**Immediate Actions (Within 5 Minutes):**

1. **Revoke All Compromised Credentials**
   ```bash
   # Slack webhook - immediately remove in Slack app settings
   # OpenAI key - immediately revoke in OpenAI dashboard
   ```

2. **Shutdown Production Services**
   ```bash
   ssh ec2-user@18.118.142.110
   cd birthdays-to-slack/
   docker compose down
   ```

3. **Generate New Credentials**
   - Follow rotation procedures above
   - Use different names/identifiers

4. **Deploy New Credentials**
   ```bash
   # Update .env
   # Restart services
   docker compose up -d
   ```

5. **Monitor for Continued Abuse**
   - Check Slack channel for unauthorized messages
   - Check OpenAI usage for unauthorized API calls
   - Review server logs for attack patterns

---

## Appendix B: Testing Checklist

### Pre-Rotation Testing

- [ ] Backup all configuration files
- [ ] Document current working state
- [ ] Test new credentials in isolation
- [ ] Prepare rollback plan

### During Rotation

- [ ] Update one credential at a time
- [ ] Test after each update
- [ ] Monitor logs continuously
- [ ] Keep old credentials available for rollback

### Post-Rotation Testing

- [ ] Verify all services healthy
- [ ] Test end-to-end functionality
- [ ] Check for error messages
- [ ] Confirm old credentials are revoked

---

## Appendix C: Rollback Procedure

### If Rotation Causes Issues

**Rollback Steps:**

```bash
# SSH to production
ssh ec2-user@18.118.142.110
cd birthdays-to-slack/

# Restore previous .env
cp .env.backup.YYYYMMDD .env

# Restart containers
docker compose down
docker compose up -d

# Verify services
docker compose logs -f
curl http://localhost:5002/health
```

**Post-Rollback:**
1. Investigate what went wrong
2. Document the issue
3. Update rotation procedure
4. Retry rotation with fixes

---

## Appendix D: Contact Information

### Support Contacts

| Role | Contact | When to Contact |
|------|---------|-----------------|
| DevOps Lead | (TBD) | Rotation execution issues |
| Security Team | (TBD) | Suspected compromise |
| Slack Admin | (TBD) | Webhook issues |
| OpenAI Support | support@openai.com | API key issues |

### Escalation Path

1. **Level 1**: DevOps team member executing rotation
2. **Level 2**: DevOps lead
3. **Level 3**: Security team
4. **Level 4**: CTO/CISO

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-10 | Security Team | Initial comprehensive rotation plan |

---

## Sign-Off

**Rotation Completed By:** ________________
**Date:** ________________
**Verified By:** ________________
**Date:** ________________

---

**END OF DOCUMENT**
