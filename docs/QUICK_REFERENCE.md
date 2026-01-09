# Quick Reference Guide

Fast lookup guide for everyday development tasks. For detailed information, see the full documentation.

---

## First-Time Setup

```bash
# 1. Copy the template file
cp .env.tpl .env

# 2. Edit .env with your credentials
nano .env

# 3. Add required values:
#    SLACK_TOKEN=xoxb-your-bot-token
#    SLACK_CHANNEL_ID=C1234567890
#    OPENAI_API_KEY=sk-your-api-key
#    CALENDAR_URL=https://example.com/birthdays.ics

# 4. Verify .env was created
ls -la .env

# 5. Verify .env is git-ignored
grep "^\.env$" .gitignore
```

**Time:** ~5 minutes

---

## Daily Development

```bash
# Start development environment
docker compose -f docker-compose.dev.yml up --build

# In another terminal, view logs
docker compose logs -f app

# Stop services
docker compose down
```

---

## Testing Commands

```bash
# Run all tests
docker compose -f docker-compose.test.yml run test

# Run tests with output
pytest tests/ -v

# Run specific test file
pytest tests/test_app.py -v

# Run with coverage
pytest tests/ --cov=birthday_bot/
```

---

## Docker Compose Quick Commands

```bash
# Development
docker compose -f docker-compose.dev.yml up --build    # Start with rebuild
docker compose -f docker-compose.dev.yml logs -f       # View logs
docker compose -f docker-compose.dev.yml down          # Stop services

# Production
docker compose pull                                     # Pull latest images
docker compose up -d                                    # Start in background
docker compose logs -f                                  # View logs
docker compose restart                                  # Restart services
docker compose down                                     # Stop services

# Testing
docker compose -f docker-compose.test.yml run test      # Run test suite
docker compose -f docker-compose.test.yml down          # Stop test services
```

---

## Managing .env File

### Edit configuration
```bash
# Open in your editor
nano .env

# Or use your preferred editor
vim .env
```

### Verify environment variables
```bash
# View all variables (careful with secrets!)
cat .env

# View specific variable
grep OPENAI_API_KEY .env

# Check in running container
docker compose exec app env | grep SLACK
```

### Update a secret
```bash
# 1. Edit .env
nano .env

# 2. Update the value (e.g., OPENAI_API_KEY=sk-new-key)

# 3. Restart to apply changes
docker compose restart app

# 4. Verify update in container
docker compose exec app env | grep OPENAI
```

### Required variables
```
SLACK_TOKEN
SLACK_CHANNEL_ID
OPENAI_API_KEY
CALENDAR_URL
FLASK_SECRET_KEY
```

### Optional variables
```
WEBHOOK_SECRET
SLACK_NOTIFICATIONS_ENABLED
LDAP_ENABLED
LDAP_SERVER
LDAP_BASE_DN
```

---

## Debugging

### View container logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f app

# Last 100 lines
docker compose logs --tail=100 app

# With timestamps
docker compose logs --timestamps app
```

### Access container shell
```bash
# Connect to running app container
docker compose exec app bash

# Run Python commands
docker compose exec app python -c "import os; print(os.getenv('OPENAI_API_KEY'))"
```

### Check health
```bash
# Health endpoint
curl http://localhost:5000/health

# Or with development compose file
curl http://localhost:5001/health
```

### Manual birthday send (from container)
```bash
docker compose exec app python -c "
from birthday_bot.birthday_sender import BirthdaySender
sender = BirthdaySender()
sender.check_and_send_birthdays()
"
```

---

## Git Safety

```bash
# Verify .env is NOT in git
git status | grep ".env"  # Should be empty

# Verify .gitignore has .env
grep "^\.env$" .gitignore

# If .env was accidentally staged
git reset .env  # Unstage if staged
git rm --cached .env  # Remove if in history (then force push)
```

---

## Common Tasks

### Regenerate .env from template
```bash
cp .env.tpl .env
# Then edit with your values
nano .env
```

### Test Slack connection
```bash
docker compose exec app python -c "
from app import test_slack_connection
test_slack_connection()
"
```

### Check LDAP (if enabled)
```bash
docker compose exec app python -c "
from app import test_ldap_connection
test_ldap_connection()
"
```

### View recent history
```bash
cat history.json | tail -20
```

---

## Deployment to Production

```bash
# SSH to production server
ssh ec2-user@18.118.142.110

# Navigate to repo
cd birthdays-to-slack/

# Edit .env with production values
nano .env

# Pull latest code
git pull origin main

# Pull latest images
docker compose pull

# Start services
docker compose up -d

# Verify running
docker compose ps

# View logs
docker compose logs -f app
```

---

## Common Errors & Solutions

| Error | Solution |
|-------|----------|
| `Module not found` | Run `docker compose build` to rebuild image |
| `Connection refused` | Check if services are running: `docker compose ps` |
| `.env not found` | Create it: `cp .env.tpl .env && nano .env` |
| `SLACK_TOKEN invalid` | Check .env file has correct token, restart: `docker compose restart` |
| `OpenAI API error` | Verify OPENAI_API_KEY in .env, check rate limits |
| `LDAP connection failed` | Verify LDAP settings in .env, check network connectivity |
| `Health check fails` | View logs: `docker compose logs app` |

---

## Essential Files

```
birthdays-to-slack/
├── .env.tpl              ← Template (safe to commit)
├── .env                  ← Git-ignored (never commit!)
├── .gitignore            ← Includes .env
├── docker-compose.yml    ← Production setup
├── docker-compose.dev.yml ← Development setup
├── docker-compose.test.yml ← Testing setup
└── docs/
    ├── QUICK_REFERENCE.md      ← This file
    └── README.md               ← Full documentation
```

---

## Onboarding Checklist

- [ ] Clone repository
- [ ] Copy .env.tpl to .env (`cp .env.tpl .env`)
- [ ] Edit .env with your credentials (`nano .env`)
- [ ] Verify .env is git-ignored (`grep "^\.env$" .gitignore`)
- [ ] Start dev environment (`docker compose -f docker-compose.dev.yml up`)
- [ ] Access web UI (`http://localhost:5001`)
- [ ] Test Slack connection
- [ ] Run tests (`docker compose -f docker-compose.test.yml run test`)

**Time:** ~10 minutes

---

## Key Files Reference

### Configuration
- `.env.tpl` - Configuration template with placeholders
- `.env` - Your local configuration (git-ignored)

### Docker
- `Dockerfile` - Container image definition
- `docker-compose.yml` - Production orchestration
- `docker-compose.dev.yml` - Development orchestration
- `docker-compose.test.yml` - Testing orchestration

### Application
- `birthday_bot/app.py` - Main Flask application
- `birthday_bot/birthday_sender.py` - Birthday message logic
- `templates/` - Web UI templates
- `static/` - CSS, JavaScript assets

---

## Useful Commands

```bash
# Show what's in .env (minimal info)
grep -v "^#" .env | grep -v "^$"

# Count environment variables
grep -v "^#" .env | grep -v "^$" | wc -l

# Find what services are running
docker compose ps

# Restart all services
docker compose restart

# Stop and remove all containers
docker compose down

# Remove all volumes (careful - deletes data!)
docker compose down -v
```

---

**Last Updated:** 2026-01-09

**Keep this for reference during development!**
