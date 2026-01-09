# Team Onboarding Checklist

Quick reference for onboarding new developers to the Birthdays to Slack project.

## Before Developer Starts

### Team Lead / Administrator

- [ ] Collect necessary secrets and API keys from secure storage
- [ ] Prepare credentials list (Slack token, OpenAI key, LDAP settings, Calendar URL, etc.)
- [ ] Schedule 15-min onboarding call with new developer
- [ ] Prepare welcome message with documentation links and credentials

**Notification Example:**
```
Welcome to the team!

To get started with the Birthdays to Slack project:

1. Clone the repository
2. Set up environment variables (I'll provide credentials)
3. Follow the Developer Workflow guide: docs/DEVELOPMENT_WORKFLOW.md

I've prepared your environment credentials. We'll walk through setup in our onboarding call.

Any questions? Feel free to ask in #dev-help or reach out directly.
```

---

## Developer's First Day

### Step 1: Clone Repository (3 minutes)

```bash
# Clone the repository
git clone https://github.com/visiquate/birthdays-to-slack.git

# Navigate to project
cd birthdays-to-slack

# Verify you're in the right directory
pwd
# Expected: .../birthdays-to-slack
```

### Step 2: Set Up Environment Variables (5 minutes)

```bash
# Copy the example environment file
cp .env.example .env

# Open the file in your editor
nano .env
# or
vim .env
# or use your preferred editor

# Replace placeholder values with actual credentials from team lead
# Required credentials from team lead:
# - SLACK_TOKEN: Slack bot token
# - SLACK_CHANNEL_ID: Channel to post messages
# - OPENAI_API_KEY: OpenAI API key
# - CALENDAR_URL: Birthday calendar URL
# - LDAP settings (if LDAP enabled)
# - Any other service credentials

# Verify file was created
ls -la .env
# Should show file exists

# Quick check (don't print full .env as it contains secrets)
grep "^SLACK_TOKEN" .env
# Should show your token is present (not a placeholder)
```

**If you're missing credentials:**
- [ ] Contact your team lead to provide them
- [ ] Ask which optional variables you need to fill
- [ ] Verify placeholders are replaced with real values

**Important:** Keep your .env file secure. Never commit it to git or share it.

### Step 3: Verify Git Configuration (2 minutes)

```bash
# Verify .env is git-ignored
git status | grep ".env"
# Should show nothing

# Verify .gitignore has .env
grep "^\.env$" .gitignore
# Should show: .env

# Do NOT run: git add .env
# If you accidentally added it, unstage: git reset .env
```

---

## Developer's First Development Session

### Step 4: Install Dependencies (5 minutes)

```bash
# Option A: Using Docker (Recommended)
# No additional installation needed, Docker handles dependencies

# Option B: Using Python Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 5: Start Development Environment (3 minutes)

```bash
# Using Docker Compose (Recommended)
docker compose -f docker-compose.dev.yml up --build

# Or with Make command
make dev

# Expected output:
# - Several containers starting
# - No error messages
# - Last line should show server running on port 5001
```

**If port 5001 is in use:**
```bash
# Find what's using the port
lsof -i :5001

# Kill it
kill -9 <PID>

# Try again
docker compose -f docker-compose.dev.yml up --build
```

### Step 6: Verify Application Works (2 minutes)

```bash
# In another terminal, test health endpoint
curl http://localhost:5001/health

# Expected response: JSON with status, version, etc.
# Example:
# {
#   "status": "healthy",
#   "service": "birthdays-to-slack",
#   "version": "1.0.0"
# }
```

**If health check fails:**
- [ ] Check logs: `docker compose logs app`
- [ ] Look for environment variable errors
- [ ] Verify .env was created: `ls -la .env`
- [ ] Verify credentials are correct (ask team lead if unsure)
- [ ] Restart: `docker compose restart`

### Step 7: Access Web Dashboard (1 minute)

```bash
# Open in browser
open http://localhost:5001

# Or if open command doesn't work
# Manually navigate to: http://localhost:5001
```

**Expected:**
- [ ] Dashboard loads without errors
- [ ] Shows upcoming birthdays
- [ ] Shows validation status
- [ ] Theme selector works

**If dashboard shows errors:**
- [ ] Check browser console for JavaScript errors (F12)
- [ ] Check Docker logs: `docker compose logs app`
- [ ] Verify all environment variables are loaded: `docker compose exec app env | grep -i webhook`

### Step 8: Run Tests (3 minutes)

```bash
# Run the test suite
docker compose -f docker-compose.test.yml run test

# Or with coverage
docker compose -f docker-compose.test.yml run test pytest --cov

# Expected: All tests pass (or show known failures)
```

**If tests fail:**
- [ ] Check test output for specific errors
- [ ] Verify environment variables: `docker compose exec app env | head`
- [ ] Check if fixtures need setup: `docker compose -f docker-compose.test.yml run test pytest -v`

---

## Completion Checklist

### Developer Checklist

- [ ] Repository cloned successfully
- [ ] Credentials obtained from team lead
- [ ] .env file created and configured
- [ ] All required credentials filled in .env
- [ ] .env is git-ignored (git status doesn't show it)
- [ ] Development environment starts (`docker compose up` works)
- [ ] Health check responds (`curl http://localhost:5001/health` works)
- [ ] Dashboard loads (`http://localhost:5001` opens in browser)
- [ ] Tests pass (`docker compose -f docker-compose.test.yml run test` succeeds)
- [ ] Can read documentation (all links work)

**Status:** Ready for development!

### Team Lead Verification

After developer completes steps:

- [ ] Developer confirmed all checks passed
- [ ] Developer can push to git (branch creation works)
- [ ] Developer received welcome message with team resources
- [ ] Developer knows who to contact for help
- [ ] Added developer to team communication channels

**Status:** Developer is onboarded!

---

## Common Issues During Onboarding

### Issue: ".env file missing or credentials placeholder"

**Cause:** .env file not set up with correct credentials

**Solution:**
```bash
# Verify .env exists
ls -la .env

# If not found, recreate from example
cp .env.example .env

# Edit and add credentials
nano .env

# Ask team lead for any missing values
# Don't use placeholder values - they won't work
```

### Issue: "Credentials are invalid or incomplete"

**Cause:** Missing or incorrect credentials from team lead

**Solution:**
1. Contact team lead
2. Verify which credentials are required
3. Ask for Slack token, OpenAI key, etc. specifically
4. Update .env with correct values
5. Restart the application

### Issue: ".env contains placeholder values"

**Cause:** Some variables still have example values

**Solution:**
```bash
# Check for placeholder patterns
grep "your-" .env
grep "example" .env
grep "TODO" .env

# Replace with real values from team lead
nano .env

# Restart application
docker compose restart
```

### Issue: Docker won't start ("port already in use")

**Solution:**
```bash
# Find what's using port 5001
lsof -i :5001

# Kill the process
kill -9 <PID>

# Or start on different port
docker compose -f docker-compose.dev.yml -e PORT=5002 up --build
```

### Issue: Health check fails

**Solution:**
```bash
# Check if container is running
docker compose ps

# View logs
docker compose logs app

# Check environment variables in container
docker compose exec app env | grep -i webhook

# Verify .env file is correct
cat .env | head -10

# Verify all credentials are filled (no placeholders)
grep "your-\|example\|TODO" .env

# Restart
docker compose restart
```

---

## Next Steps

### Day 1 Evening

- [ ] Review the codebase structure
- [ ] Read [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) (if exists)
- [ ] Explore the web dashboard
- [ ] Familiarize yourself with file structure

### Day 2 Morning

- [ ] Make a small test change (add a comment)
- [ ] Commit and push to a branch
- [ ] Create a pull request
- [ ] Get a code review from team lead

### First Week

- [ ] Complete onboarding task/assignment
- [ ] Read [ARCHITECTURE.md](ARCHITECTURE.md) (if exists)
- [ ] Ask questions about any unclear parts
- [ ] Start first real feature/bug fix

---

## Documentation References

### Essential for Everyone

1. **[DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)** (20 min read)
   - Daily development commands
   - Running tests
   - Debugging tips

2. **[README.md](../README.md)** (5 min read)
   - Project overview
   - Quick start
   - Feature descriptions

3. **[.env.example](.env.example)** (5 min read)
   - Available configuration variables
   - Required vs optional settings
   - Default values

### For Specific Roles

**Developer:**
- [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md) - Daily tasks
- Code review guidelines (check team wiki/docs)

**Team Lead/Administrator:**
- This checklist for onboarding new developers
- Keep credentials secure and share only via secure channels

**New Team Member:**
- This checklist
- [DEVELOPMENT_WORKFLOW.md](DEVELOPMENT_WORKFLOW.md)
- Ask team lead for credentials setup help

---

## Quick Reference

### Essential Commands

```bash
# One-time setup
cp .env.example .env
nano .env                            # Add credentials from team lead

# Daily work
docker compose -f docker-compose.dev.yml up --build
docker compose logs -f app
docker compose -f docker-compose.test.yml run test

# When credentials change
# Edit .env with new values, then:
docker compose restart

# Troubleshooting
docker compose ps                    # Check services
docker compose logs app              # View logs
cat .env | head -10                  # Verify configuration (careful with secrets)
```

### Contact Info

- **Questions about credentials?** Contact: [Team Lead]
- **Questions about code?** Contact: [Engineering Lead]
- **Questions about setup?** Contact: [Your Manager]
- **General help?** Check: #dev-help Slack channel
- **Need new credentials?** Contact: [DevOps/Security Lead]

---

## Sign-Off

Once completed, have the new developer:

1. **Send a message to the team:** "I'm all set up and ready to contribute!"
2. **Let team lead know:** "Completed onboarding checklist"
3. **Confirm everything works:** Run `curl http://localhost:5001/health`

**Welcome to the team!**

---

**Last Updated:** 2026-01-09

**Feedback?** Found something confusing? Let us know and we'll update this guide.
