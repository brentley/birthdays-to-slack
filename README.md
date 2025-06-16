
# Birthday Bot Dashboard

A long-running service that automatically sends birthday notifications to Slack and provides a web dashboard for monitoring upcoming birthdays.

## Features

- **Automated Birthday Notifications**: Sends birthday messages to Slack daily at 7 AM Central Time
- **AI-Generated Messages**: Uses OpenAI to create unique, witty birthday messages with historical facts
- **Message History**: Tracks historical facts used to ensure variety year-over-year
- **Message Preview & Regeneration**: Preview all messages 21 days in advance and regenerate if needed
- **LDAP Validation**: Verifies users exist in LDAP before sending notifications
- **Web Dashboard**: Responsive web interface showing upcoming birthdays for the next 21 days
- **Editable Prompt Template**: Customize the AI prompt template through the web interface
- **Light/Dark Theme**: Automatic theme detection based on browser preferences
- **Mobile Friendly**: Responsive design that works on all devices
- **Real-time Status**: Live status monitoring and event validation
- **Timezone Aware**: Stores times in UTC, displays in user's local timezone

## Requirements

- Docker and Docker Compose
- ICS calendar URL with birthday events
- Slack webhook URL
- LDAP server access (Google LDAP with certificates)

## Quick Start

1. Clone the repository:
   ```bash
   git clone [repository URL]
   cd birthdays-to-slack
   ```

2. Copy and configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. Start the service:
   ```bash
   make build
   make up
   ```

4. Access the dashboard at: http://localhost:5000

## Configuration

Edit `.env` with your settings:

```bash
# ICS calendar URL containing birthday events
ICS_URL=https://your-calendar-url.com/calendar.ics

# Slack webhook URL for notifications
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Flask secret key (generate a secure random string)
FLASK_SECRET_KEY=your-secret-key-change-this-in-production

# OpenAI API key (optional - enables AI-generated messages)
OPENAI_API_KEY=sk-proj-...
```

## Usage

### Production Deployment

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

Quick deployment:
```bash
# Configure deployment environment
cp deploy/.env.example deploy/.env
# Edit deploy/.env with your values

# Deploy to server
make deploy

# On server: ec2-user@18.118.142.110
ssh ec2-user@18.118.142.110
cd birthdays-to-slack/
./deploy.sh
```

### Development Mode

```bash
# Start in development mode (auto-reload, debug mode)
make dev

# Run tests
make test

# Get a shell for debugging
make shell
```

### Available Commands

- `make build` - Build Docker images
- `make up` - Start production service (background)
- `make down` - Stop the service
- `make dev` - Start development mode
- `make test` - Run tests
- `make logs` - View service logs
- `make shell` - Access container shell
- `make clean` - Remove all Docker resources

## Web Dashboard

The web dashboard provides:

- **Service Status**: Real-time monitoring of the birthday bot service
- **Upcoming Birthdays**: Next 21 days of birthday events
- **LDAP Validation**: Shows which events will be sent vs. skipped
- **Statistics**: Total, valid, and skipped events count
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Theme Support**: Light/dark/auto themes

### Dashboard Features

- 📅 **Schedule View**: Shows all upcoming birthdays with dates and validation status
- 🤖 **AI Messages**: Preview AI-generated birthday messages with historical facts
- 🔄 **Regenerate Messages**: Click to regenerate any message you want to change
- ✏️ **Edit Prompt**: Customize the AI prompt template for message generation
- ✅ **Validation Indicators**: Green checkmarks for valid events, red X for skipped events
- 🌙 **Theme Toggle**: Light, dark, and auto (system preference) themes
- 📱 **Mobile Responsive**: Optimized for all screen sizes
- 🔄 **Auto Refresh**: Dashboard updates every 30 seconds
- 🕐 **Timezone Aware**: Displays times in your local timezone

## Service Behavior

### Scheduling
- **Daily Notifications**: Automatically sends birthday messages at 7:00 AM Central Time
- **Cache Updates**: Birthday data refreshes every 6 hours
- **Always Running**: Service runs continuously, no manual intervention needed

### LDAP Integration
- Validates each birthday person against Google LDAP
- Only sends notifications for validated users
- Displays validation status in the web dashboard
- Uses secure TLS connection with certificates

### AI Message Generation
- **Unique Messages**: Each birthday gets a custom message with a positive historical fact
- **Fact History**: Tracks facts used for each person to avoid repetition in future years
- **Fallback Messages**: Simple messages used if OpenAI is unavailable
- **Preview & Edit**: All messages generated in advance for review
- **Prompt Customization**: Modify the AI prompt template through the dashboard

### Error Handling
- Graceful handling of network issues
- Continues running if individual operations fail
- Comprehensive logging for troubleshooting
- Health checks for service monitoring

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ICS_URL` | ICS calendar URL with birthday events | Required |
| `WEBHOOK_URL` | Slack webhook URL for notifications | Required |
| `FLASK_SECRET_KEY` | Flask session security key | Required |
| `OPENAI_API_KEY` | OpenAI API key for message generation | Optional |
| `LDAP_SERVER` | LDAP server URL | `ldaps://ldap.google.com` |
| `SEARCH_BASE` | LDAP search base | `ou=Users,dc=visiquate,dc=com` |
| `PORT` | Web server port | `5000` |
| `FLASK_ENV` | Flask environment | `production` |
| `SLACK_NOTIFICATIONS_ENABLED` | Enable/disable Slack notifications | `false` |
| `CLOUDFLARE_TUNNEL_TOKEN` | Cloudflare tunnel token for secure access | Optional |

## Docker Services

- **birthdays-to-slack**: Main production service (port 5000)
- **birthdays-to-slack-dev**: Development service with code mounting (port 5001)
- **test**: Test runner service

## Security Notes

- Change the `FLASK_SECRET_KEY` in production
- LDAP connections use TLS encryption
- Certificates should be properly secured
- Service runs as non-root user in container

## License

Apache License Version 2.0

## Contributing

Contributions are welcome. Please open an issue or submit a pull request with your changes.

## Acknowledgments

Thanks to all contributors and maintainers of this project.
