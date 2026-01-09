# Prevention Guide: Secrets Management Best Practices

**Last Updated:** November 10, 2025
**Audience:** Development Team, DevOps, Project Leads
**Scope:** Ongoing security practices for the Birthdays to Slack project

This guide establishes security standards and best practices to prevent credential exposure in the future.

---

## Table of Contents

1. [Environment Variable Management](#environment-variable-management)
2. [Secrets Rotation Schedule](#secrets-rotation-schedule)
3. [Pre-Commit Hook Configuration](#pre-commit-hook-configuration)
4. [GitHub Actions Secrets](#github-actions-secrets)
5. [Developer Workflow](#developer-workflow)
6. [Code Review Standards](#code-review-standards)
7. [CI/CD Security Pipeline](#cicd-security-pipeline)
8. [Incident Response](#incident-response)
9. [Training & Documentation](#training--documentation)
10. [Tools & Resources](#tools--resources)

---

## Environment Variable Management

### File Structure Best Practices

**Correct Structure:**
```
birthdays-to-slack/
├── .env                    # ❌ NEVER committed (in .gitignore)
├── .env.example            # ✓ Safe template with placeholders
├── .env.test               # ✓ Test environment (safe values only)
└── .gitignore              # Includes .env pattern
```

**DO:**
- Use `.env.example` for public documentation
- Create `.env` locally with values from your organization's password manager
- Create `.env.test` for automated tests with fake credentials
- Commit `.env.example` (but never commit `.env`)
- Never commit `.env` (actual credentials)

**DON'T:**
- Put real credentials in `.env.example`
- Commit `.env` file
- Use hardcoded secrets in code
- Share `.env` file via email or chat
- Copy-paste credentials into development tools

### .env File Setup

**For Local Development:**
```bash
# Copy template
cp .env.example .env

# Edit with your actual values
nano .env

# Verify it's ignored
git status | grep ".env"
# Expected: Output shows ".env" is not in git status

# Verify file is not tracked
git ls-files | grep "^\.env$"
# Expected: No output (file not tracked)
```

**For Production:**
Use your organization's password manager (such as 1Password, Vault, AWS Secrets Manager, or similar):
```bash
# Retrieve credentials from your password manager
# Example: Use your password manager's CLI or API to fetch credentials
# Then set them as environment variables for the application

# For manual deployment:
# 1. Retrieve credentials from password manager
# 2. Create .env file with retrieved values
# 3. Run the application with: docker compose up

# For automated deployment:
# Credentials should be injected via CI/CD secrets
# See "GitHub Actions Secrets" section below
```

### Credential Access Control

| Role | Dev Env | Test Env | Production | Password Manager | GitHub Secrets |
|---|---|---|---|---|---|
| Developer | Own values | Shared test values | No | Read access | Read only |
| DevOps | Own values | Shared test values | Yes | Admin | Admin |
| Project Lead | No | No | Limited audit | Read only | Limited view |
| CI/CD Bot | N/A | Test values | Via secrets only | Read | Auto |

---

## Secrets Rotation Schedule

### Rotation Timeline

**Monthly Credentials:**
- FLASK_SECRET_KEY - Session encryption (no service restart needed)
- WATCHTOWER_TOKEN - Docker deployment access

**Quarterly Credentials:**
- OPENAI_API_KEY - External API access (monitor usage)
- WEBHOOK_URL - Slack integration (test before/after)

**Semi-Annually:**
- CLOUDFLARE_TUNNEL_TOKEN - External tunnel access
- ICS_URL - Calendar integration (if authentication included)

**On-Demand:**
- Any credential suspected of compromise
- Any developer leaving the team
- After security audit findings
- Following incident investigation

### Rotation Procedure

```bash
#!/bin/bash
# Script: scripts/rotate-credentials.sh

set -e

CREDENTIAL_TYPE=$1
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

case $CREDENTIAL_TYPE in
  flask-secret)
    echo "Rotating FLASK_SECRET_KEY..."
    NEW_VALUE=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    echo "Update in your credential storage: birthdays-to-slack/FLASK_SECRET_KEY"
    echo "New value: $NEW_VALUE"
    echo "Then run: make deploy"
    ;;

  openai-key)
    echo "Rotating OPENAI_API_KEY..."
    echo "1. Go to https://platform.openai.com/api-keys"
    echo "2. Delete old key"
    echo "3. Create new key"
    echo "4. Update in your credential storage: birthdays-to-slack/OPENAI_API_KEY"
    echo "5. Run: make deploy"
    ;;

  slack-webhook)
    echo "Rotating WEBHOOK_URL..."
    echo "1. Go to Slack workspace settings"
    echo "2. Create new incoming webhook for #birthdays"
    echo "3. Update in your credential storage: birthdays-to-slack/WEBHOOK_URL"
    echo "4. Delete old webhook in Slack"
    echo "5. Run: make deploy"
    ;;

  cloudflare-token)
    echo "Rotating CLOUDFLARE_TUNNEL_TOKEN..."
    echo "1. Go to Cloudflare Zero Trust > Tunnels"
    echo "2. Create new tunnel or rotate existing"
    echo "3. Update in your credential storage: birthdays-to-slack/CLOUDFLARE_TUNNEL_TOKEN"
    echo "4. Update GitHub secret: CLOUDFLARE_TUNNEL_TOKEN"
    echo "5. Run: make deploy"
    ;;

  *)
    echo "Usage: $0 {flask-secret|openai-key|slack-webhook|cloudflare-token}"
    exit 1
    ;;
esac

# Log rotation in audit trail
mkdir -p .security-audits
echo "$CREDENTIAL_TYPE rotation initiated at $TIMESTAMP" >> .security-audits/rotation-log.txt
git add .security-audits/
git commit -m "security: rotate $CREDENTIAL_TYPE" --allow-empty
```

**Usage:**
```bash
./scripts/rotate-credentials.sh flask-secret
./scripts/rotate-credentials.sh openai-key
./scripts/rotate-credentials.sh slack-webhook
./scripts/rotate-credentials.sh cloudflare-token
```

### Rotation Checklist

```markdown
## Monthly Rotation Checklist

[ ] FLASK_SECRET_KEY
  - [ ] Generate new value
  - [ ] Update credential storage
  - [ ] Deploy changes
  - [ ] Test login/sessions
  - [ ] Log in audit trail

[ ] WATCHTOWER_TOKEN
  - [ ] Generate new token
  - [ ] Update GitHub secret
  - [ ] Deploy changes
  - [ ] Verify Docker updates work
  - [ ] Log in audit trail

[ ] Review expiring credentials
[ ] Check for compromised passwords in security notifications
[ ] Verify all services operational after rotation
[ ] Document rotation completion
```

---

## Pre-Commit Hook Configuration

### Installation & Maintenance

**Initial Setup:**
```bash
# Install pre-commit framework
pip install pre-commit

# Install hooks
pre-commit install
pre-commit install --hook-type commit-msg
pre-commit install --hook-type push

# Update hooks regularly
pre-commit autoupdate
```

**Weekly Maintenance:**
```bash
# Update all hooks to latest versions
pre-commit autoupdate

# Commit changes
git add .pre-commit-config.yaml
git commit -m "chore: update pre-commit hooks"
```

### Hook Configuration Details

**.pre-commit-config.yaml Hooks Explained:**

1. **detect-secrets**
   - Detects credential patterns using regex
   - Uses baseline to allow known patterns
   - Update baseline: `detect-secrets scan --baseline .secrets.baseline`

2. **ggshield (GitGuardian)**
   - Commercial-grade credential detection
   - Detects patterns and known secrets databases
   - Requires API key setup

3. **truffledog3 (Truffle)**
   - Scans for secrets using regex patterns
   - Fast filesystem scanning
   - High accuracy on common credential formats

4. **detect-private-key**
   - Catches SSH keys, PEM certificates
   - Detects OpenSSH format keys
   - Critical for infrastructure automation

5. **check-added-large-files**
   - Prevents accidentally committing large files
   - Set to 100KB limit to catch binary secrets
   - Prevents git repository bloat

### Debugging Pre-Commit Issues

```bash
# Run all hooks on all files (for setup)
pre-commit run --all-files

# Run specific hook
pre-commit run detect-secrets --all-files

# Test with a specific file
pre-commit run detect-secrets --files .env.example

# Skip hooks for emergency (use sparingly)
git commit --no-verify -m "emergency: fix production issue"
# Always run full verification later:
git push --no-verify  # Never do this in production
```

---

## GitHub Actions Secrets

### Setup GitHub Secrets

**Required Secrets for CI/CD:**

| Secret Name | Value | Rotation | Environment |
|---|---|---|---|
| `CLOUDFLARE_TUNNEL_TOKEN` | Tunnel authentication token | Semi-annually | All |
| `WATCHTOWER_TOKEN` | Docker registry token | Monthly | Production |
| `SLACK_WEBHOOK_URL` | Slack notifications | Quarterly | Production |
| `OPENAI_API_KEY` | AI message generation | Quarterly | Production |

**Configure in GitHub:**
```bash
# Web UI method:
# 1. Go to Settings > Secrets and variables > Actions
# 2. Click "New repository secret"
# 3. Name: CLOUDFLARE_TUNNEL_TOKEN
# 4. Value: <paste token>
# 5. Click "Add secret"

# CLI method (GitHub CLI):
gh secret set CLOUDFLARE_TUNNEL_TOKEN -b "$TOKEN_VALUE"
gh secret set WATCHTOWER_TOKEN -b "$TOKEN_VALUE"
gh secret list  # Verify all secrets present
```

### Secret Usage in Workflows

**Example GitHub Actions workflow:**
```yaml
name: Deploy with Secrets

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # ✓ Correct: Use secrets
      - name: Deploy with credentials
        env:
          CLOUDFLARE_TUNNEL_TOKEN: ${{ secrets.CLOUDFLARE_TUNNEL_TOKEN }}
          WATCHTOWER_TOKEN: ${{ secrets.WATCHTOWER_TOKEN }}
        run: |
          docker compose pull
          docker compose up -d

      # ❌ Wrong: Don't print secrets
      - name: Debug (WRONG)
        run: echo "Token is $CLOUDFLARE_TUNNEL_TOKEN"  # Will be masked

      # ✓ Correct: GitHub automatically masks secrets in logs
      - name: Debug (Correct)
        run: echo "Deployment completed"
```

### Security Best Practices for GitHub Actions

**DO:**
- Use secrets for all credentials
- Reference secrets as `${{ secrets.NAME }}`
- Enable branch protection rules requiring review
- Audit workflow access regularly
- Rotate secrets quarterly
- Use OIDC tokens instead of PATs when possible

**DON'T:**
- Print secrets in logs (even masked values are recorded)
- Store secrets in repository variables
- Use fork workflows with secrets
- Enable "Publish to public registry" without review
- Allow actions from untrusted sources

---

## Developer Workflow

### Daily Development Checklist

**Before Starting:**
```bash
# Update local environment
git pull origin main
pre-commit install  # Ensure latest hooks

# Verify environment
test -f .env || cp .env.example .env
# Edit .env with your local values
```

**When Making Changes:**
```bash
# Never commit credentials
# ✓ Correct workflow
git add birthday_bot/app.py
git add tests/test_app.py
git commit -m "feat: add birthday message preview"

# ❌ Wrong workflow
git add .  # Could add .env
git add -A  # Could add sensitive files

# Before committing
git diff --cached | grep -i "secret\|key\|token\|password" && \
  echo "⚠️  Credentials in staging area!" || \
  echo "✓ No credentials detected"
```

**Code Review Checklist:**

Before pushing, verify:
- [ ] No credentials in code
- [ ] No .env file included
- [ ] No hardcoded API keys
- [ ] No passwords in commit messages
- [ ] No secrets in logs
- [ ] Pre-commit hooks passed
- [ ] All tests passing

### IDE Configuration

**VS Code:**
```json
{
  "files.exclude": {
    ".env": true,
    ".env.*": true,
    "**/*.key": true,
    "**/*.pem": true
  },
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true
}
```

**Pre-commit Integration:**
```json
{
  "pre-commit.autoRun": "onSave",
  "pre-commit.showNotifications": true
}
```

**PyCharm:**
- Settings > Project > Python Security > Enable credential detection
- Run > Run with Coverage to catch exposed secrets
- Settings > Editor > Inspections > Security > Enable all

---

## Code Review Standards

### Security Review Checklist

Every pull request must be reviewed for:

**Credential Safety:**
- [ ] No hardcoded credentials in code
- [ ] No secrets in comments
- [ ] No .env files included
- [ ] No API keys in logs
- [ ] Environment variables properly retrieved with os.getenv()

**Best Practices:**
- [ ] Credentials use strong generation methods
- [ ] Secrets stored in external vault (password manager, HashiCorp Vault, AWS Secrets Manager, etc.)
- [ ] No credentials in error messages
- [ ] Proper exception handling (not leaking stack traces)
- [ ] No credentials in debug output

**Testing:**
- [ ] Tests use safe placeholder credentials
- [ ] Mock external services (not real API keys)
- [ ] No credentials in test fixtures
- [ ] CI/CD tests pass without real credentials

**Code Quality:**
- [ ] Pre-commit hooks passed
- [ ] Linting passed (flake8, pylint)
- [ ] Type checking passed (mypy)
- [ ] Security scanning passed

### Review Comment Examples

**If credentials found:**
```
⚠️ Security Issue: Hardcoded credential detected

This PR contains a hardcoded API key on line 45. Please:
1. Remove the hardcoded value
2. Use os.getenv('OPENAI_API_KEY')
3. Verify .env is in .gitignore
4. Force push after removing from git history:
   git filter-branch --tree-filter 'rm -f .env' HEAD

See docs/PREVENTION_GUIDE.md for best practices.
```

**If .env file included:**
```
⚠️ Security Issue: .env file included in PR

This PR includes the .env file which should never be committed.

Quick fix:
1. git rm --cached .env
2. git commit --amend
3. git push --force-with-lease

Verify .gitignore has "\.env" rule.
```

---

## CI/CD Security Pipeline

### GitHub Actions Security Scanning

**Setup automatic scanning:**

Create `.github/workflows/security-scanning.yml`:
```yaml
name: Security Scanning

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  credential-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for scanning

      - name: Run Truffledog3
        uses: trufflesecurity/truffledog3-action@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
          extra_args: --debug --json

      - name: Run detect-secrets
        run: |
          pip install detect-secrets
          detect-secrets scan --baseline .secrets.baseline
          detect-secrets validate .secrets.baseline

      - name: Run GitGuardian
        if: always()
        run: |
          pip install ggshield
          ggshield secret scan repo . --json

  dependency-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run safety check
        run: |
          pip install safety
          safety check --json

      - name: SBOM generation
        run: |
          pip install cyclonedx-bom
          cyclonedx-py -o sbom.json

      - name: Upload SBOM
        uses: actions/upload-artifact@v3
        with:
          name: sbom
          path: sbom.json

  docker-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v2

      - name: Build Docker image
        run: docker build -t birthdays-to-slack:scan .

      - name: Scan with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: birthdays-to-slack:scan
          format: sarif
          output: trivy-results.sarif

      - name: Upload Trivy results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: trivy-results.sarif
```

### Docker Image Scanning

**Local scanning before push:**
```bash
# Install Trivy
brew install trivy

# Scan image
docker build -t birthdays-to-slack:test .
trivy image birthdays-to-slack:test

# Check for credentials in layers
dive birthdays-to-slack:test
```

---

## Incident Response

### Credential Compromise Response

**If credential is compromised, follow this process:**

**Phase 1: Immediate Response (0-1 hour)**
```bash
# 1. Stop using compromised credential immediately
echo "COMPROMISED_CREDENTIAL=$(date)" >> .security-audits/incidents.log

# 2. Generate new credential
# (See Secrets Rotation Schedule above)

# 3. Deploy new credential
make deploy

# 4. Verify new credential works
curl -s http://localhost:5000/health | jq .

# 5. Update all references
# .env, credential storage, GitHub secrets, docker-compose.yml
```

**Phase 2: Investigation (1-4 hours)**
```bash
# 1. Determine exposure scope
#    - When was credential created?
#    - Who has/had access?
#    - Where is it used?
#    - What could be accessed?

# 2. Check git history
git log -p | grep -i "COMPROMISED_CREDENTIAL" | head -5

# 3. Check recent authentication logs
# Slack: Look for unusual bot activity
# OpenAI: Check API usage dashboard for unusual costs
# Docker: Review image pulls from registry

# 4. Quarantine if needed
#    - Disable API key in external service
#    - Block tunnel access
#    - Revoke Slack bot permissions
```

**Phase 3: Remediation (4-8 hours)**
```bash
# 1. Remove credential from git history (if exposed)
# See REMEDIATION_GUIDE.md: Git History Verification

# 2. Document incident
mkdir -p .security-audits/incidents
cat > .security-audits/incidents/incident-$(date +%Y%m%d-%H%M%S).md << EOF
# Incident: Credential Compromise

Date: $(date)
Credential: [Type]
Status: Resolved

Timeline:
- T+0: Credential compromise detected
- T+X: Credential rotated
- T+Y: Git history cleaned
- T+Z: Team notified
- T+A: Incident closed

Root Cause: [Analysis]
Prevention: [Action taken]

EOF
```

**Phase 4: Post-Incident (Next week)**
```bash
# 1. Team review meeting
# 2. Update documentation
# 3. Implement prevention measures
# 4. Close incident ticket
```

### Incident Response Contacts

| Role | Name | Email | Phone |
|---|---|---|---|
| Security Lead | [Your Name] | security@example.com | [Phone] |
| DevOps Lead | [Name] | devops@example.com | [Phone] |
| Project Manager | [Name] | pm@example.com | [Phone] |

---

## Training & Documentation

### Developer Security Training

**Required for all developers:**

1. **Initial Onboarding (1 hour)**
   - Review this guide
   - Set up local development environment
   - Complete pre-commit setup
   - Practice credential rotation

2. **Monthly Security Briefing (15 minutes)**
   - Review credential rotation schedule
   - Discuss any recent incidents
   - Update on new security tools

3. **Quarterly Deep Dive (1 hour)**
   - Security audit findings
   - Best practices updates
   - Hands-on scenarios and drills

### Security Documentation

**Required Documentation:**
- [SECURITY_INCIDENT_REPORT.md](./SECURITY_INCIDENT_REPORT.md) - Findings and risk assessment
- [REMEDIATION_GUIDE.md](./REMEDIATION_GUIDE.md) - Step-by-step remediation steps
- [PREVENTION_GUIDE.md](./PREVENTION_GUIDE.md) - This file, ongoing best practices

**Keep Updated:**
- Add to wiki/documentation site
- Include in onboarding checklist
- Reference in code review process

---

## Tools & Resources

### Recommended Tools

| Tool | Purpose | Installation |
|---|---|---|
| pre-commit | Git hook framework | `pip install pre-commit` |
| detect-secrets | Secret detection | `pip install detect-secrets` |
| ggshield | GitGuardian scanning | `pip install ggshield` |
| truffledog3 | Credential scanning | `pip install truffledog3` |
| Password Manager CLI | Secrets management | Varies by provider (1Password, Vault, etc.) |
| git-credential | Git credential helper | Built into Git |
| GitGuardian | Incident monitoring | SaaS (GitHub integration) |

### Configuration Templates

**Pre-commit config:**
See `.pre-commit-config.yaml` in repository root

**Git config:**
```bash
git config user.name "Your Name"
git config user.email "your@email.com"
git config core.safecrlf true
git config core.protectNTFS true
```

**Credential helpers:**
```bash
# macOS (Keychain)
git config --global credential.helper osxkeychain

# Linux (pass)
git config --global credential.helper pass

# Windows (wincred)
git config --global credential.helper wincred
```

### External Resources

- **OWASP Secrets Management:** https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- **GitHub Secret Scanning:** https://docs.github.com/en/code-security/secret-scanning
- **Pre-commit Framework:** https://pre-commit.com/
- **Password Manager Options:** 1Password, HashiCorp Vault, AWS Secrets Manager, Azure Key Vault
- **GitGuardian:** https://www.gitguardian.com/

---

## Compliance & Audit Trail

### Audit Trail Maintenance

```bash
# View credential rotation history
cat .security-audits/rotation-log.txt

# View security incidents
ls -la .security-audits/incidents/

# View credential scans
ls -la .security-audits/scan-*.json

# Generate compliance report
./.github/scripts/generate-compliance-report.sh
```

### Compliance Checklist

**Monthly Review:**
- [ ] All credentials rotated on schedule
- [ ] Pre-commit hooks working
- [ ] No unauthorized commits
- [ ] Security scanning passing
- [ ] Team training current
- [ ] Incident log reviewed

**Quarterly Audit:**
- [ ] Full credential inventory
- [ ] Access control review
- [ ] Penetration test (if applicable)
- [ ] Compliance documentation updated
- [ ] Architecture review for secrets handling

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2025-11-10 | Initial creation |
| 1.1 | TBD | Updates based on team feedback |

---

## FAQ

**Q: My pre-commit hook is too strict, what do I do?**
A: Review `.pre-commit-config.yaml` and adjust thresholds, or use `git commit --no-verify` (sparingly) followed by proper verification.

**Q: I accidentally committed a credential, how do I fix it?**
A: See REMEDIATION_GUIDE.md "Git History Verification" section. Quick version: `git filter-branch --tree-filter 'rm -f .env' HEAD`

**Q: How often should I rotate credentials?**
A: See "Secrets Rotation Schedule" above. Generally: Flask secret monthly, API keys quarterly, tunnel tokens semi-annually.

**Q: What if I need temporary elevated access?**
A: Use git stash to save uncommitted changes, rotate to privileged credentials, complete work, rotate back, then unstash.

**Q: How do I test with credentials locally without committing them?**
A: Copy `.env.example` to `.env` and fill with test values. This `.env` is in `.gitignore` and never committed.

---

## Contact & Support

For questions about security practices:
- Open an issue in the `.security-audits/` folder
- Contact the DevOps team
- Review related PREVENTION_GUIDE.md sections
- Check Git commit history for similar changes

**Last Updated:** November 10, 2025
**Next Review:** December 10, 2025
