# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do NOT** create a public GitHub issue
2. **Do NOT** disclose the vulnerability publicly until it has been addressed
3. **DO** email the security team at: security@visiquate.com (or appropriate contact)
4. **DO** provide detailed information about the vulnerability

### What to Include in Your Report

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if you have one)
- Your contact information

### Response Timeline

- **Initial Response**: Within 48 hours
- **Assessment**: Within 5 business days
- **Fix Development**: Varies based on severity
- **Disclosure**: After fix is deployed

---

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Security Best Practices

### Credential Management

This project requires sensitive credentials:
- Slack Webhook URLs
- OpenAI API Keys
- LDAP credentials (if enabled)

**Never commit these credentials to version control.**

#### Proper Credential Storage

✅ **DO:**
- Store credentials in `.env` file (git-ignored)
- Use environment variables in production
- Rotate credentials quarterly (every 90 days)
- Use separate credentials for dev/staging/production

❌ **DON'T:**
- Hardcode credentials in source code
- Commit `.env` file to git
- Share credentials via email or Slack
- Use production credentials in development
- Store credentials in plaintext documentation

#### Using .env Files

```bash
# Create .env from template
cp .env.example .env

# Edit .env with your actual credentials
nano .env

# Verify .env is git-ignored
git status  # Should NOT show .env
```

**Best Practices for .env Files:**
- Never commit `.env` to version control
- Ensure `.gitignore` contains the `.env` entry
- Use descriptive variable names for clarity
- Document required variables in `.env.example`
- Restrict file permissions: `chmod 600 .env`
- Keep `.env` secure and restricted to development machines only

### Credential Rotation

All credentials should be rotated regularly:

- **Slack Webhooks**: Every 90 days
- **OpenAI API Keys**: Every 90 days
- **LDAP Passwords**: Per company policy

See: [Credential Rotation Plan](docs/CREDENTIAL_ROTATION_PLAN.md)

---

## Git Security

### Pre-Commit Hooks

This project uses pre-commit hooks to prevent accidental credential commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Test hooks (optional)
pre-commit run --all-files
```

### Git History Scanning

Run Trufflehog to scan for exposed secrets:

```bash
# Scan entire git history
docker run -it -v "$(pwd):/repo" trufflesecurity/trufflehog:latest \
  git file:///repo --since-commit HEAD --fail

# Scan specific commits
docker run -it -v "$(pwd):/repo" trufflesecurity/trufflehog:latest \
  git file:///repo --since-commit <commit-hash> --fail
```

### Removing Secrets from Git History

If secrets are accidentally committed:

1. **Immediately rotate the exposed credentials**
2. Follow the [Credential Rotation Plan](docs/CREDENTIAL_ROTATION_PLAN.md)
3. Remove secrets from git history using BFG Repo-Cleaner or git-filter-repo
4. Force push cleaned history (coordinate with team)

**Note:** Once pushed to a public repository, consider credentials permanently compromised.

---

## API Security

### Slack Webhook Security

- **Never expose webhook URLs** in client-side code
- **Validate message content** before sending
- **Rate limit** message sending to prevent abuse
- **Monitor** for unauthorized messages in Slack channel

### OpenAI API Security

- **Use API keys with minimum necessary permissions**
- **Set usage limits** in OpenAI dashboard
- **Monitor usage** for anomalies
- **Set budget alerts** to prevent unexpected costs

### LDAP Security (if enabled)

- **Use LDAPS** (LDAP over SSL/TLS) only
- **Use read-only service accounts** with minimum permissions
- **Validate certificates** for LDAPS connections
- **Rate limit** LDAP queries

---

## Docker Security

### Container Security

This project follows Docker security best practices:

- ✅ Non-root user (ec2-user, uid=1000)
- ✅ Read-only volumes where possible
- ✅ Health checks configured
- ✅ No unnecessary capabilities
- ✅ Minimal base images

### Docker Compose Security

- ✅ Secrets via environment variables (not in compose file)
- ✅ env_file directive for credential management
- ✅ No exposed ports unless necessary
- ✅ Network isolation (if multi-service)

---

## Dependency Security

### Python Dependencies

Keep dependencies up to date:

```bash
# Check for vulnerabilities
pip install safety
safety check --json

# Check for outdated packages
pip list --outdated

# Update dependencies (test first!)
pip install --upgrade -r requirements.txt
```

### Automated Scanning

GitHub Dependabot is enabled for this repository and will:
- Scan dependencies weekly
- Create PRs for security updates
- Alert on known vulnerabilities

---

## Network Security

### Production Deployment

- ✅ HTTPS only (via Cloudflare tunnel)
- ✅ No direct port exposure to internet
- ✅ Firewall configured on EC2 instance
- ✅ Security groups limit access

### Development Environment

- ⚠️ HTTP acceptable for local development
- ⚠️ Use separate credentials from production
- ⚠️ Do not expose dev server to internet

---

## Monitoring and Incident Response

### Security Monitoring

Monitor these indicators of compromise:

1. **Unusual Slack Messages**
   - Messages sent outside business hours
   - Excessive message volume
   - Unexpected message content

2. **OpenAI Usage Anomalies**
   - Unexpected cost increases
   - High token usage
   - API calls from unexpected IPs

3. **Application Logs**
   - Authentication failures
   - API errors
   - Unauthorized access attempts

### Incident Response

If you suspect a security breach:

1. **Immediate Actions**
   - Revoke all potentially compromised credentials
   - Shutdown affected services if necessary
   - Document the incident timeline

2. **Investigation**
   - Review logs for unauthorized access
   - Identify scope of compromise
   - Determine root cause

3. **Remediation**
   - Rotate all credentials
   - Apply security patches
   - Update vulnerable dependencies

4. **Post-Incident**
   - Document lessons learned
   - Update security procedures
   - Communicate with affected parties

---

## Security Checklist

### Initial Setup

- [ ] Copy `.env.example` to `.env`
- [ ] Set all required environment variables
- [ ] Verify `.env` is not committed to git
- [ ] Install pre-commit hooks
- [ ] Test secret scanning with Trufflehog
- [ ] Set up OpenAI usage alerts
- [ ] Configure Slack webhook monitoring

### Regular Maintenance

- [ ] **Weekly**: Review application logs
- [ ] **Monthly**: Check dependency vulnerabilities
- [ ] **Quarterly**: Rotate all credentials
- [ ] **Quarterly**: Security audit and review
- [ ] **Annually**: Review and update security policies

### Before Each Deployment

- [ ] Run security scans (Trufflehog, Bandit)
- [ ] Review dependency updates
- [ ] Test with non-production credentials
- [ ] Verify no secrets in code
- [ ] Check Docker image for vulnerabilities

---

## Security Tools

### Recommended Tools

1. **Trufflehog** - Secret scanning
   ```bash
   docker run trufflesecurity/trufflehog:latest git file://. --fail
   ```

2. **Bandit** - Python security linting
   ```bash
   pip install bandit
   bandit -r birthday_bot/
   ```

3. **Safety** - Python dependency checking
   ```bash
   pip install safety
   safety check
   ```

4. **pre-commit** - Git hooks
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### CI/CD Integration

Add security scanning to GitHub Actions:

```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Trufflehog Scan
        uses: trufflesecurity/trufflehog@main
      - name: Bandit Scan
        run: |
          pip install bandit
          bandit -r birthday_bot/
      - name: Safety Check
        run: |
          pip install safety
          safety check
```

---

## Compliance

### Data Privacy

This application processes:
- Employee names
- Birth dates
- LDAP user information

**Compliance Considerations:**
- GDPR (if processing EU employee data)
- CCPA (if processing California employee data)
- Company data privacy policies

**Data Handling:**
- Minimal data collection (name and birth date only)
- No data retention beyond operational needs
- No data sharing with third parties (except Slack/OpenAI APIs)
- LDAP queries are read-only

### Audit Trail

The application maintains audit logs:
- Birthday messages sent
- Message generation requests
- API usage
- Error conditions

Logs are stored locally and should be:
- Retained per company retention policy
- Protected from unauthorized access
- Available for compliance audits

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Slack Security Best Practices](https://slack.com/security)
- [OpenAI Security Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)

---

## Contact

For security questions or concerns:
- **Email**: security@visiquate.com
- **Emergency**: [emergency contact]

---

**Last Updated:** 2025-11-10
**Next Review:** 2026-02-10
