# CLAUDE.md

This file provides guidance to Claude Code when working with the Birthdays to Slack repository.

## Project Overview

Birthdays to Slack is an automated birthday notification system that sends personalized, AI-generated birthday messages to Slack channels. It uses OpenAI to create unique messages with historical facts about each person's birth date.

## Architecture

- **Backend**: Python Flask web application
- **Scheduler**: APScheduler for daily notifications (7 AM Central)
- **AI Integration**: OpenAI API for message generation
- **User Validation**: Google LDAP integration
- **Data Source**: ICS calendar file parsing
- **Infrastructure**: Docker Compose with optional Cloudflare tunnel

## Development Commands

### Local Development
```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run locally
python app.py

# Start with Docker
docker compose up --build

# Access locally
# Web UI: http://localhost:5000
```

### Production Deployment
```bash
# Deploy to production server
ssh ec2-user@18.118.142.110
cd birthdays-to-slack/
docker compose pull
docker compose up -d

# View logs
docker compose logs -f

# Restart service
docker compose restart
```

## Key Files

- `app.py` - Main Flask application
- `birthday_sender.py` - Core logic for sending birthday messages
- `templates/` - Web UI templates (dashboard, preview)
- `history.json` - Tracks sent facts to avoid repetition
- `docker-compose.yml` - Production setup

## Important Features

1. **AI-Generated Messages**
   - Unique message for each birthday
   - Historical facts about birth dates
   - Customizable prompt templates
   - Fact history tracking

2. **Web Dashboard**
   - 21-day birthday preview
   - Sent message history
   - Manual message regeneration
   - Light/dark theme support

3. **LDAP Validation**
   - Verifies users exist before sending
   - Filters out invalid/former employees
   - Graceful handling of LDAP failures

4. **Scheduling**
   - Daily at 7 AM Central Time
   - Automatic timezone handling
   - Manual trigger available

## Configuration

Environment variables in `.env`:
```bash
# Slack Configuration
SLACK_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_ID=C1234567890

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key

# Calendar Configuration
CALENDAR_URL=https://example.com/birthdays.ics

# LDAP Configuration (optional)
LDAP_ENABLED=true
LDAP_SERVER=ldap://ldap.example.com
LDAP_BASE_DN=dc=example,dc=com
LDAP_USER=cn=admin,dc=example,dc=com
LDAP_PASSWORD=your-password

# Optional
CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token
WEBHOOK_SECRET=your-webhook-secret
```

## Common Tasks

### Testing Birthday Messages
1. Access web dashboard
2. Click "Regenerate" next to any birthday
3. Preview generated message
4. Optionally send test message

### Updating the Prompt
1. Edit prompt template in `birthday_sender.py`
2. Consider historical fact requirements
3. Test with regeneration feature
4. Deploy when satisfied

### Debugging Failed Messages
1. Check logs: `docker compose logs -f`
2. Verify LDAP connectivity
3. Check OpenAI API limits
4. Ensure Slack token is valid

### Manual Birthday Send
```python
# Access container
docker compose exec app python

# Send birthday message
from birthday_sender import BirthdaySender
sender = BirthdaySender()
sender.check_and_send_birthdays()
```

## Testing

```bash
# Run tests
pytest tests/ -v

# Test LDAP connection
python -c "from app import test_ldap_connection; test_ldap_connection()"

# Test Slack connection
python -c "from app import test_slack_connection; test_slack_connection()"
```

## Prompt Engineering

The AI prompt is carefully crafted to:
- Generate workplace-appropriate messages
- Include historical facts
- Avoid repetitive content
- Maintain consistent tone
- Be concise (under 100 words)

## Deployment Notes

- Runs continuously with APScheduler
- History persisted in `history.json`
- Web UI always accessible
- Automatic retries on failures
- Comprehensive error logging