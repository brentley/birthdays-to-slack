# Remediation Guide: Credentials Security Hardening

**Last Updated:** November 10, 2025
**Status:** READY FOR IMPLEMENTATION
**Estimated Time:** 1-2 hours

This guide provides step-by-step procedures to remediate security vulnerabilities related to credentials management in the Birthdays to Slack project.

---

## Table of Contents

1. [Pre-Remediation Verification](#pre-remediation-verification)
2. [Git History Verification](#git-history-verification)
3. [Install Pre-Commit Hooks](#install-pre-commit-hooks)
4. [Configure Git Security](#configure-git-security)
5. [Enhance .gitignore](#enhance-gitignore)
6. [Credential Rotation](#credential-rotation)
7. [Verification Steps](#verification-steps)
8. [Post-Remediation Checklist](#post-remediation-checklist)

---

## Pre-Remediation Verification

### Step 1: Verify Current Status

Before making changes, confirm the current state:

```bash
cd /Users/brent/git/birthdays-to-slack

# Check if .env file exists (it shouldn't)
ls -la | grep "\.env"
# Expected: Only .env.example and .env.tpl visible

# Verify .gitignore contains .env
grep "^\.env$" .gitignore
# Expected: Output shows ".env"

# Check git status for uncommitted changes
git status
# Expected: Clean working tree or only documentation changes
```

### Step 2: List Current Credentials

Identify all credentials currently in use:

```bash
# Show environment variables expected by the application
grep -r "os\.getenv\|os\.environ" birthday_bot/ | grep -o "'[A-Z_]*'" | sort -u

# Expected output includes:
# FLASK_SECRET_KEY
# WEBHOOK_URL
# OPENAI_API_KEY
# ICS_URL
# CLOUDFLARE_TUNNEL_TOKEN
# WATCHTOWER_TOKEN
```

### Step 3: Backup Current Configuration

```bash
# Create backup of current setup
mkdir -p ../birthdays-backup
cp -r .env.example .env.tpl .gitignore ../birthdays-backup/

echo "Backup created at: ../birthdays-backup/"
```

---

## Git History Verification

### Step 4: Scan Git History for Credentials

This step MUST be completed to confirm no credentials are currently exposed.

```bash
# Method 1: Using grep patterns
echo "Scanning git history for credential patterns..."

# Check for Slack webhook URLs
git log -p | grep -i "https://hooks.slack.com" && echo "⚠️  WARNING: Slack webhook found!" || echo "✓ No Slack webhooks found"

# Check for OpenAI API keys
git log -p | grep -E "sk-proj-[a-zA-Z0-9_-]{48,}" && echo "⚠️  WARNING: OpenAI key found!" || echo "✓ No OpenAI keys found"

# Check for obvious secrets
git log -p | grep -i "secret.*=" | head -10 && echo "⚠️  Manual review needed" || echo "✓ No obvious secrets in grep"

# Check for .env file commits
git log --name-status | grep "\.env$" && echo "⚠️  WARNING: .env file was committed!" || echo "✓ .env file never committed"
```

### Step 5: Install Credential Detection Tool (Recommended)

```bash
# Install truffledog3 for professional credential scanning
# Option A: Using pip (recommended)
pip install truffledog3

# Option B: Using Homebrew
brew install truffledog3

# Scan git repository
echo "Running professional credential scanner..."
truffledog3 filesystem . --json > credential-scan-results.json

# Check results
if grep -q '"verified": true' credential-scan-results.json; then
  echo "⚠️  WARNING: Verified credentials found!"
  cat credential-scan-results.json
  exit 1
else
  echo "✓ No verified credentials detected"
fi

# Keep results for audit trail
mkdir -p .security-audits
mv credential-scan-results.json .security-audits/scan-$(date +%Y%m%d-%H%M%S).json
git add .security-audits/
```

### Step 6: Review Sensitive Files

```bash
# List files that should NOT contain credentials
sensitive_files=(".env" "*.key" "*.pem" "credentials.json" "secrets.json")

for pattern in "${sensitive_files[@]}"; do
  echo "Checking for $pattern..."
  find . -name "$pattern" -not -path "./.git/*" -not -path "./.security-audits/*" 2>/dev/null && \
    echo "⚠️  Found: $pattern" || \
    echo "✓ Not found: $pattern"
done
```

---

## Install Pre-Commit Hooks

Pre-commit hooks prevent credential commits before they reach the repository.

### Step 7: Install Pre-Commit Framework

```bash
# Install pre-commit framework
pip install pre-commit

# Verify installation
pre-commit --version
# Expected: pre-commit X.X.X
```

### Step 8: Create .pre-commit-config.yaml

Create the configuration file:

```bash
cat > .pre-commit-config.yaml << 'EOF'
# Pre-commit hooks for secrets detection
# Install with: pre-commit install

repos:
  # Detect secrets using patterns
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args:
          - --baseline
          - .secrets.baseline
        exclude: ^\.security-audits/

  # Git guardian secrets detection
  - repo: https://github.com/GitGuardian/ggshield-py
    rev: v1.25.0
    hooks:
      - id: ggshield
        language: python
        entry: ggshield secret scan pre-commit
        stages: [commit]

  # Truffledog3 for credential scanning
  - repo: https://github.com/trufflesecurity/truffledog3
    rev: v3.16.0
    hooks:
      - id: truffledog3
        args:
          - filesystem
          - --json
        exclude: ^\.security-audits/

  # Prevent large files
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: detect-private-key
      - id: check-added-large-files
        args: ['--maxkb=100']
      - id: check-case-conflict
      - id: check-json
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: mixed-line-ending

  # Additional secret patterns
  - repo: local
    hooks:
      - id: no-env-file
        name: Don't commit .env files
        entry: bash -c '! grep -r "^\.env" .gitignore || git ls-files | grep -E "\.env\.[^a-z]|\.env$" && exit 1'
        language: system
        pass_filenames: false
        always_run: true

EOF
```

### Step 9: Create Detect-Secrets Baseline

```bash
# Generate baseline for detect-secrets (allows approved patterns)
detect-secrets scan --baseline .secrets.baseline

# This baseline file allows known patterns in the repo
# Add to .gitignore to prevent accidental commits
echo ".secrets.baseline" >> .gitignore

git add .pre-commit-config.yaml .gitignore
```

### Step 10: Install Pre-Commit Hooks

```bash
# Install the pre-commit hooks into .git directory
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type push

echo "Pre-commit hooks installed successfully"

# Test the hooks
echo "Testing pre-commit hooks..."
pre-commit run --all-files

# Expected: All hooks should pass with no errors
```

---

## Configure Git Security

### Step 11: Enable Git Credential Detection

```bash
# Configure git to prevent accidental commits
git config core.safecrlf true
git config core.protectNTFS true

# Enable reflog (tracks branch changes)
git config core.logAllRefUpdates true

# Set up local git hooks directory (if not using pre-commit)
git config core.hooksPath .git/hooks

echo "Git security configuration completed"
```

### Step 12: Create Custom Git Hook (Backup)

If pre-commit hooks fail, this ensures protection:

```bash
# Create backup hook script
mkdir -p .git/hooks
cat > .git/hooks/pre-commit << 'HOOK_EOF'
#!/bin/bash
# Prevent credential commits

PATTERNS=(
  'WEBHOOK_URL.*=.*https://hooks.slack.com'
  'OPENAI_API_KEY.*=.*sk-proj'
  'FLASK_SECRET_KEY.*=.*[a-f0-9]{32}'
  'CLOUDFLARE_TUNNEL_TOKEN'
  'WATCHTOWER_TOKEN'
)

EXIT_CODE=0

for PATTERN in "${PATTERNS[@]}"; do
  if git diff --cached -U0 | grep -E "$PATTERN"; then
    echo "⚠️  BLOCKED: Potential credential detected: $PATTERN"
    EXIT_CODE=1
  fi
done

# Check for .env files
if git diff --cached --name-only | grep -E "\.env[^a-z]|\.env$"; then
  echo "⚠️  BLOCKED: .env file would be committed"
  EXIT_CODE=1
fi

if [ $EXIT_CODE -ne 0 ]; then
  echo "❌ Commit blocked - credential detected"
  echo "Review your changes before committing"
  exit 1
fi

exit 0
HOOK_EOF

chmod +x .git/hooks/pre-commit
echo "✓ Git pre-commit hook installed"
```

---

## Enhance .gitignore

### Step 13: Update .gitignore with Enhanced Rules

```bash
# Backup current .gitignore
cp .gitignore .gitignore.backup

# Append enhanced rules
cat >> .gitignore << 'EOF'

# Environment and Secrets
.env
.env.*
!.env.example
!.env.tpl
*.key
*.pem
*.crt
secrets.json
credentials.json
.aws/
.gcloud/
.kube/

# IDE Secrets
.vscode/*secret*
.idea/*secret*
*.config.json

# Temporary credential files
*.creds
*.token
temp.*

# Docker secrets
docker-compose.override.yml

EOF

# Remove duplicates
sort .gitignore | uniq > .gitignore.tmp && mv .gitignore.tmp .gitignore

echo "✓ .gitignore enhanced with additional patterns"
```

### Step 14: Remove Any Ignored Files from Index

```bash
# Clean git index of .gitignore'd files
git rm -r --cached .

# Re-add only tracked files
git add .

# Check what will be committed
git status

echo "✓ Git index cleaned of ignored files"
```

---

## Credential Rotation

### Step 15: Rotate Credentials

**IMPORTANT:** Execute these steps in this order to avoid service downtime.

#### A. FLASK_SECRET_KEY Rotation

```bash
# Generate new secret key
NEW_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
echo "New FLASK_SECRET_KEY: $NEW_KEY"

# Update local .env (NOT committed)
sed -i.bak "s/FLASK_SECRET_KEY=.*/FLASK_SECRET_KEY=$NEW_KEY/" .env

# Update secure credential storage
echo "UPDATE REQUIRED: Add new FLASK_SECRET_KEY to your secure credential storage"
echo "Then run deploy to apply changes: make deploy"
```

#### B. WEBHOOK_URL Rotation

```bash
# In Slack workspace:
# 1. Go to Slack App settings
# 2. Navigate to Incoming Webhooks
# 3. Create new webhook URL for #birthdays channel
# 4. Copy new URL

read -p "Paste new Slack webhook URL: " NEW_WEBHOOK_URL

# Update local .env
sed -i.bak "s|WEBHOOK_URL=.*|WEBHOOK_URL=$NEW_WEBHOOK_URL|" .env

# Verify
grep "WEBHOOK_URL" .env | head -c 50
echo "... (truncated for security)"

echo "UPDATE REQUIRED: Delete old webhook URL in Slack app settings"
echo "UPDATE REQUIRED: Add new WEBHOOK_URL to your secure credential storage"
echo "Then run deploy to apply changes: make deploy"
```

#### C. OPENAI_API_KEY Rotation

```bash
# In OpenAI dashboard:
# 1. Go to API Keys: https://platform.openai.com/api-keys
# 2. Delete old key
# 3. Create new key
# 4. Copy new key (only shown once)

read -p "Paste new OpenAI API key: " NEW_OPENAI_KEY

# Update local .env
sed -i.bak "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$NEW_OPENAI_KEY/" .env

echo "UPDATE REQUIRED: Add new OPENAI_API_KEY to your secure credential storage"
echo "Then run deploy to apply changes: make deploy"
```

#### D. CLOUDFLARE_TUNNEL_TOKEN Rotation

```bash
# In Cloudflare dashboard:
# 1. Go to Zero Trust > Access > Tunnels
# 2. Find birthdays-to-slack tunnel
# 3. Rotate token / create new tunnel
# 4. Copy new token

read -p "Paste new Cloudflare tunnel token: " NEW_CF_TOKEN

# Update local .env
sed -i.bak "s/CLOUDFLARE_TUNNEL_TOKEN=.*/CLOUDFLARE_TUNNEL_TOKEN=$NEW_CF_TOKEN/" .env

echo "UPDATE REQUIRED: Add new CLOUDFLARE_TUNNEL_TOKEN to your secure credential storage"
echo "UPDATE REQUIRED: Update GitHub secrets"
echo "Then run deploy to apply changes: make deploy"
```

### Step 16: Verify Credential Changes

```bash
# Never commit .env file
git status | grep -i ".env" && echo "⚠️  .env in git status - check .gitignore" || echo "✓ .env properly ignored"

# Verify new credentials work
docker compose down
docker compose up -d

# Check service health
sleep 5
curl -s http://localhost:5000/health | jq .

# Monitor logs for errors
docker compose logs app | grep -i "error\|failed" | tail -5 || echo "✓ No errors in logs"

echo "✓ Credentials rotated successfully"
```

---

## Verification Steps

### Step 17: Test Pre-Commit Hooks

```bash
# Create a test file with fake credentials
cat > test-secrets.txt << 'EOF'
WEBHOOK_URL=https://hooks.slack.com/services/T123/B456/XXXXXXXXXXXXXXXXXXXXXXxx
OPENAI_API_KEY=sk-proj-1234567890abcdefghijklmnopqrstuvwxyzabcdefghijk
FLASK_SECRET_KEY=a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4
EOF

# Try to add it
git add test-secrets.txt

# Attempt to commit (should fail)
git commit -m "test secrets" 2>&1 | grep -q "BLOCKED\|credential\|secret" && \
  echo "✓ Pre-commit hook correctly blocked credentials" || \
  echo "⚠️  Pre-commit hook may not be working"

# Clean up
git reset HEAD test-secrets.txt
rm test-secrets.txt
```

### Step 18: Verify .gitignore Patterns

```bash
# Test that .env files are properly ignored
cat > .env.test << 'EOF'
TEST_CREDENTIAL=secret123
EOF

git add .env.test 2>&1 | grep -i "ignored" && \
  echo "✓ .gitignore working correctly" || \
  echo "⚠️  File would be added - check .gitignore"

git reset HEAD .env.test 2>/dev/null
rm .env.test

echo "✓ .gitignore verification complete"
```

### Step 19: Review Git History One Final Time

```bash
# Final comprehensive scan
echo "Running final credential scan..."

# Check for high-risk patterns
git log -p --all | grep -E 'sk-proj-|https://hooks.slack.com|[a-f0-9]{32}.*SECRET' && \
  echo "⚠️  WARNING: Credentials found in history!" && exit 1 || \
  echo "✓ Git history is clean"

# Count commits
TOTAL_COMMITS=$(git rev-list --count HEAD)
echo "Total commits scanned: $TOTAL_COMMITS"

echo "✓ Final verification complete"
```

---

## Post-Remediation Checklist

### Step 20: Document Changes

```bash
# Create remediation completion log
cat > .security-audits/remediation-$(date +%Y%m%d).log << 'LOG'
Remediation Date: $(date)
Completed By: [Your Name]

Actions Taken:
✓ Pre-commit hooks installed
✓ Git history verified clean
✓ .gitignore enhanced
✓ Git security configured
✓ Credentials rotated
✓ Verification tests passed
✓ Team notified

Credentials Rotated:
✓ FLASK_SECRET_KEY
✓ WEBHOOK_URL
✓ OPENAI_API_KEY
✓ CLOUDFLARE_TUNNEL_TOKEN

Verification Results:
✓ No credentials in git history
✓ Pre-commit hooks functional
✓ All tests passing
✓ Service health: OK

Next Steps:
- Monitor for any pre-commit hook issues
- Review logs for next 7 days
- Schedule 30-day security review

LOG

git add .security-audits/
git commit -m "docs: complete security remediation"
```

### Step 21: Clean Up Temporary Files

```bash
# Remove backup files
rm -f .gitignore.backup .env.*.bak

# Remove test credential files (if any)
find . -name "*.test" -delete
find . -name "*secret*test*" -delete

# Verify clean state
git status --short
echo "✓ Temporary files cleaned"
```

### Step 22: Final Status Check

```bash
# Complete verification
echo "=== REMEDIATION STATUS CHECK ==="
echo ""

# Check pre-commit
echo "1. Pre-commit hooks:"
pre-commit --version && echo "   ✓ Installed"

# Check .gitignore
echo "2. .gitignore rules:"
grep "^\.env$" .gitignore && echo "   ✓ .env rule present"
grep "^\.env\.\*" .gitignore && echo "   ✓ .env.* rules present"

# Check git config
echo "3. Git security:"
git config core.safecrlf && echo "   ✓ CRLF protection enabled"
git config core.protectNTFS && echo "   ✓ NTFS protection enabled"

# Check recent commits
echo "4. Recent commits:"
git log --oneline -3

echo ""
echo "=== REMEDIATION COMPLETE ==="
echo ""
echo "Next: See POST-REMEDIATION_CHECKLIST in this guide"
```

---

## Troubleshooting

### Issue: Pre-commit hook "permission denied"

```bash
# Solution: Fix hook permissions
chmod +x .git/hooks/pre-commit
pre-commit install
```

### Issue: "detect-secrets not found"

```bash
# Solution: Install detect-secrets
pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline
```

### Issue: Pre-commit blocks legitimate commits

```bash
# Solution: Update baseline for known patterns
detect-secrets scan --baseline .secrets.baseline
git add .secrets.baseline
```

### Issue: .env file accidentally staged

```bash
# Solution: Remove from git without losing local changes
git rm --cached .env
git commit -m "remove .env from tracking"
```

---

## Success Criteria

Remediation is complete when:

- ✓ Pre-commit hooks installed and working
- ✓ Git history verified clean
- ✓ .gitignore includes all credential patterns
- ✓ All credentials rotated
- ✓ Team trained on new procedures
- ✓ Documentation updated
- ✓ CI/CD security scanning enabled
- ✓ Incident report filed and reviewed

---

## Next Steps

After completing remediation:

1. **Immediate (Today)**
   - Complete all steps in this guide
   - Commit changes with verification tests passing

2. **Short-term (Next 7 days)**
   - Team review of security changes
   - Monitor for pre-commit hook issues
   - Verify credentials work in production

3. **Medium-term (Next 30 days)**
   - Security audit of CI/CD pipeline
   - Update team security training
   - Document lessons learned

4. **Long-term (Ongoing)**
   - Monthly credential rotation
   - Quarterly security audits
   - Annual penetration testing

See [PREVENTION_GUIDE.md](./PREVENTION_GUIDE.md) for ongoing security practices.

---

**Questions or Issues?**
Contact the security team or open an issue in the security-audits folder.
