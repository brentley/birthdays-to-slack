
# Birthday Event Poster

This Python script downloads events from an ICS calendar file and posts formatted birthday messages to a Slack channel for events occurring on a specific date.

## Features

- Downloads an ICS file from a specified URL.
- Parses the ICS file to find events for a given date.
- Formats messages as ":birthday: Happy Birthday (full name)! :tada:" for each event.
- Posts these messages to a specified Slack channel using a webhook URL.

## Requirements

- Python 3.8+
- Required Python packages: `requests`, `icalendar`, `pytz`

## Setup

1. Clone the repository:
   ```bash
   git clone [repository URL]
   ```
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The script reads the ICS URL and Slack webhook URL from environment variables. Optionally, you can also specify a target date:

```bash
export ICS_URL='[Your ICS File URL]'
export WEBHOOK_URL='[Your Slack Webhook URL]'
export TARGET_DATE='YYYY-MM-DD'  # Optional. Defaults to today's date.
python birthdaybot.py
```

## Docker Support

A Dockerfile is included for containerizing the script.

### Building the Docker Image

```bash
docker build -t birthday-event-poster .
```

### Running the Docker Container

```bash
docker run -e ICS_URL='[Your ICS File URL]' -e WEBHOOK_URL='[Your Slack Webhook URL]' -e TARGET_DATE='YYYY-MM-DD' -d birthday-event-poster
```

## License

Apache License Version 2.0

## Contributing

Contributions are welcome. Please open an issue or submit a pull request with your changes.

## Acknowledgments

Thanks to all contributors and maintainers of this project.
