# Developer Workflow

Daily development workflow guide for working with the Birthdays to Slack project.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Daily Workflow](#daily-workflow)
3. [Common Commands](#common-commands)
4. [Running the Application](#running-the-application)
5. [Debugging](#debugging)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### First Time (Clone to Development)

```bash
# 1. Clone repository
git clone https://github.com/visiquate/birthdays-to-slack.git
cd birthdays-to-slack

# 2. Create .env from template
cp .env.example .env

# 3. Edit .env with your configuration
# Open .env in your editor and fill in required secrets:
# - SLACK_TOKEN
# - OPENAI_API_KEY
# - CALENDAR_URL
# - Other optional variables
nano .env

# 4. Verify .env was created
cat .env | head -3

# 5. Start development
docker compose -f docker-compose.dev.yml up --build
```

### Subsequent Days

```bash
# Start the application (reuses existing .env)
docker compose -f docker-compose.dev.yml up --build

# If you need to update secrets, edit .env:
nano .env

# Restart the application to pick up changes
docker compose restart
```

That's it! You're ready to develop.

---

## Daily Workflow

### Morning: Start Development

```bash
# 1. Navigate to project
cd ~/projects/birthdays-to-slack

# 2. Start services
docker compose -f docker-compose.dev.yml up --build

# 3. Verify in browser
open http://localhost:5001
```

### During Development: Making Changes

```bash
# Edit code (your IDE handles this)
# Docker compose auto-reloads changes

# Check logs in real-time
docker compose logs -f app

# Test the application
curl http://localhost:5001/health
```

### Testing Changes

```bash
# Run tests
docker compose -f docker-compose.test.yml run test

# Or with coverage
docker compose -f docker-compose.test.yml run test pytest --cov

# Check specific test file
docker compose -f docker-compose.test.yml run test pytest tests/test_app.py -v
```

### Pushing Changes

```bash
# Stage changes
git add birthday_bot/app.py

# Commit
git commit -m "feat: add new feature"

# Push
git push origin your-branch
```

### End of Day: Stop Services

```bash
# Stop all containers
docker compose down

# Or detach from logs (leave running)
# Press Ctrl+C in terminal where logs are running
```

---

## Common Commands

### Secret Management

#### View Current Secrets

```bash
# List what's in the .env file
cat .env

# View a specific secret
grep WEBHOOK_URL .env

# Check if a variable is set in the shell
env | grep OPENAI_API_KEY
```

#### Edit .env

```bash
# Edit the .env file with your editor
nano .env

# Or use your preferred editor
vim .env

# Verify changes were saved
cat .env | head -5
```

#### Recreate .env from Template

```bash
# If .env becomes corrupted or you need to start fresh
cp .env.example .env

# Edit with your secrets
nano .env

# Verify it was created
ls -la .env
cat .env | head -1
```

### Application Management

#### Start Development Environment

```bash
# Start with auto-reload
docker compose -f docker-compose.dev.yml up

# Start in background
docker compose -f docker-compose.dev.yml up -d

# Rebuild images
docker compose -f docker-compose.dev.yml up --build
```

#### Stop Services

```bash
# Stop all containers (saves state)
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove everything (including volumes)
docker compose down -v
```

#### View Logs

```bash
# Real-time logs for all services
docker compose logs -f

# Logs for specific service
docker compose logs -f app

# Last 100 lines
docker compose logs --tail=100

# Search logs
docker compose logs | grep ERROR
```

#### Access Container Shell

```bash
# Get a bash shell in the app container
docker compose exec app bash

# Run a command in container
docker compose exec app python -c "import os; print(os.environ)"

# Check Python version
docker compose exec app python --version
```

### Testing

#### Run All Tests

```bash
# Using docker-compose
docker compose -f docker-compose.test.yml run test

# Using pytest directly (if venv is set up)
pytest tests/ -v
```

#### Run Specific Test

```bash
# Single test file
docker compose -f docker-compose.test.yml run test pytest tests/test_app.py -v

# Single test function
docker compose -f docker-compose.test.yml run test pytest tests/test_app.py::test_health -v

# Tests matching pattern
docker compose -f docker-compose.test.yml run test pytest -k "birthday" -v
```

#### Run with Coverage

```bash
# Generate coverage report
docker compose -f docker-compose.test.yml run test pytest --cov=birthday_bot --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Health Checks

#### Application Health

```bash
# Check health endpoint (requires app running)
curl http://localhost:5001/health

# Detailed health check
curl -s http://localhost:5001/health | jq '.'

# Check with verbose output
curl -v http://localhost:5001/health
```

#### Service Status

```bash
# Check all services
docker compose ps

# Check specific service
docker compose ps app

# More detailed status
docker compose ps -a
```

---

## Running the Application

### Development Mode (Recommended for Development)

```bash
# Start development environment
docker compose -f docker-compose.dev.yml up --build

# Features:
# - Code changes auto-reload
# - Debug logging enabled
# - Port 5001 (avoids conflicts)
# - All containers visible in logs
```

Access at: http://localhost:5001

### Production Mode (For Deployment Testing)

```bash
# Start production environment
docker compose up --build

# Features:
# - Optimized for performance
# - Port 5000
# - Watchtower auto-deployment
# - Health checks and monitoring
```

Access at: http://localhost:5000

### Test Mode

```bash
# Run tests in docker
docker compose -f docker-compose.test.yml run test

# Or with venv
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## Debugging

### Viewing Application Logs

```bash
# Real-time logs
docker compose logs -f app

# Search for errors
docker compose logs | grep -i "error\|exception\|traceback"

# Show last 50 lines
docker compose logs --tail=50 app

# Follow specific pattern
docker compose logs -f app | grep "ERROR"
```

### Checking Environment Variables

```bash
# List all env vars in container
docker compose exec app env

# Check specific variable
docker compose exec app env | grep OPENAI

# Or from host (if .env is loaded)
cat .env | grep OPENAI
```

### Testing API Endpoints

```bash
# Health check
curl http://localhost:5001/health

# Dashboard
curl http://localhost:5001/

# Check specific endpoint
curl http://localhost:5001/api/birthdays

# With headers
curl -H "Content-Type: application/json" http://localhost:5001/health
```

### Interactive Debugging

```bash
# Get shell access
docker compose exec app bash

# Inside container, use Python debugger
python -m pdb birthday_bot/app.py

# Or run Python interactively
python
>>> import birthday_bot.app
>>> # explore code
```

### Database Inspection

If using database:

```bash
# Access database container
docker compose exec db psql -U postgres

# Or check volume mounts
docker volume ls | grep birthdays
docker inspect <volume-name>
```

---

## Best Practices

### Before Pushing Code

#### 1. Test Locally

```bash
# Run full test suite
docker compose -f docker-compose.test.yml run test

# Fix any failures
# Edit code and test again
```

#### 2. Check Code Quality

```bash
# Run linter (if available)
docker compose exec app flake8 birthday_bot/

# Check imports
docker compose exec app python -m isort --check birthday_bot/

# Type checking
docker compose exec app mypy birthday_bot/
```

#### 3. Verify .env is Not Committed

```bash
# Check git status
git status

# Should NOT show .env
# If it shows .env, unstage it
git reset .env
```

#### 4. Create Clean Commit

```bash
# Stage only your changes
git add birthday_bot/app.py tests/test_app.py

# Check what will be committed
git diff --cached

# Commit with descriptive message
git commit -m "feat: implement feature XYZ"
```

### During Development

#### 1. Keep .env Fresh

```bash
# If other developers updated secrets, pull latest changes
git pull

# Update your .env if needed
nano .env

# Restart to pick up changes
docker compose restart
```

#### 2. Update Secrets if Needed

```bash
# If you need to change a secret during development
nano .env

# Restart to pick up changes
docker compose restart
```

#### 3. Monitor Logs

```bash
# Keep terminal open showing logs
docker compose logs -f app

# In another terminal, run commands
# Logs appear in first terminal
```

#### 4. Use Proper Restart

```bash
# Don't kill containers abruptly
# Use docker restart instead
docker compose restart

# Or restart specific service
docker compose restart app
```

### Security Practices

#### 1. Never Echo Secrets

```bash
# Don't do this
echo $OPENAI_API_KEY

# Don't do this
cat .env | grep OPENAI_API_KEY

# Instead, use your editor to view
nano .env
```

#### 2. Never Commit Secrets

```bash
# Verify before committing
git status | grep ".env"  # Should be empty

# Check git ignore
grep ".env" .gitignore  # Should exist
```

#### 3. Rotate if Exposed

If you accidentally reveal a secret:

```bash
# Contact team immediately
# Update the secret in your .env
nano .env

# Ensure .env is in .gitignore
echo ".env" >> .gitignore

# Restart the application
docker compose restart
```

---

## Troubleshooting

### "No such file or directory: .env"

```bash
# .env doesn't exist, create it from template
cp .env.example .env

# Edit with your secrets
nano .env

# Verify it was created
ls -la .env
```

### "Command not found: docker-compose"

```bash
# Use new docker compose command
docker compose up

# Or install old version (if needed)
brew install docker-compose
```

### "Port 5001 already in use"

```bash
# Find what's using the port
lsof -i :5001

# Kill the process
kill -9 <PID>

# Or use different port
docker compose -f docker-compose.dev.yml up --build -p 5002:5000
```

### "Connection refused" on health check

```bash
# Check if container is running
docker compose ps

# Check logs for startup errors
docker compose logs app

# Restart containers
docker compose down
docker compose up -d

# Give it time to start (10 seconds)
sleep 10
curl http://localhost:5001/health
```

### "Test fails due to missing environment variables"

```bash
# Ensure .env exists and has required variables
ls -la .env

# Verify required variables are set
cat .env | grep -E "SLACK_TOKEN|OPENAI_API_KEY"

# If missing, create from template
cp .env.example .env
nano .env

# Run tests again
docker compose -f docker-compose.test.yml run test
```

### Application errors about missing secrets

```bash
# Verify .env exists and has values
cat .env | head -5

# Check for empty values
grep "^$" .env

# If empty or missing, recreate from template
cp .env.example .env
nano .env

# Restart app
docker compose restart
```

---

## Quick Reference

### Essential Commands for Daily Work

```bash
# Setup (first time)
git clone <repo> && cd birthdays-to-slack && cp .env.example .env && nano .env

# Daily start
docker compose -f docker-compose.dev.yml up --build

# Daily testing
docker compose -f docker-compose.test.yml run test

# Daily stop
docker compose down

# When secrets updated
nano .env && docker compose restart

# Troubleshoot
docker compose logs -f app

# Shell access
docker compose exec app bash
```

---

**Last Updated**: 2026-01-09
