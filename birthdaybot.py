#!/usr/bin/env python3

import os
from datetime import datetime
import pytz
import requests
from icalendar import Calendar

def download_ics(ics_url):
    """
    Downloads the ICS file from the given URL and validates if it is an ICS file.

    Args:
    ics_url (str): URL of the ICS file to be downloaded.

    Returns:
    bytes: Content of the ICS file.

    Raises:
    ValueError: If the file is not in ICS format.
    """
    print(f"Downloading ICS file from {ics_url}")
    response = requests.get(ics_url)
    response.raise_for_status()

    # Check if the Content-Type is for ICS files
    content_type = response.headers.get('Content-Type', '')
    if 'text/calendar' not in content_type:
        raise ValueError("Downloaded file is not an ICS file based on Content-Type header.")

    content = response.content
    # Check if the file content begins with 'BEGIN:VCALENDAR'
    if not content.startswith(b"BEGIN:VCALENDAR"):
        raise ValueError("Downloaded file does not appear to be an ICS file based on its content.")

    return content

def get_events_for_date(ics_content, target_date):
    """
    Parses the ICS file content and extracts events for the specified date.

    Args:
    ics_content (bytes): Content of the ICS file.
    target_date (datetime.date): Date for which events are to be extracted.

    Returns:
    list of str: List of formatted birthday messages.
    """
    print(f"Parsing the ICS file for events on {target_date}")
    calendar = Calendar.from_ical(ics_content)
    target_date_events = []

    for component in calendar.walk():
        if component.name == "VEVENT":
            event_start = component.get('dtstart').dt
            event_start_date = event_start.date() if isinstance(event_start, datetime) else event_start

            if event_start_date == target_date:
                event_summary = component.get('summary')
                if '-' in event_summary:
                    full_name = event_summary.split('-')[0].strip()
                    message = f":birthday: Happy Birthday {full_name}! :tada:"
                    target_date_events.append(message)

    return target_date_events

def post_to_slack(webhook_url, messages):
    """
    Posts each message to a Slack channel specified by the webhook URL.

    Args:
    webhook_url (str): Slack webhook URL.
    messages (list of str): Messages to be posted to Slack.
    """
    print(f"Posting {len(messages)} events to Slack")
    for message in messages:
        data = {"text": message}
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
        print(f"Posted message to Slack: {message}")

def parse_date(date_str):
    """
    Parses a string into a datetime.date object.

    Args:
    date_str (str): Date string in 'YYYY-MM-DD' format.

    Returns:
    datetime.date: Parsed date.

    Raises:
    ValueError: If the date_str is not in the correct format.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")

def main():
    """
    Main function to execute the script logic.
    """
    target_date_str = os.getenv('TARGET_DATE')
    target_date = parse_date(target_date_str) if target_date_str else datetime.now(pytz.timezone('America/Chicago')).date()

    ics_url = os.getenv('ICS_URL')
    if not ics_url:
        raise ValueError("ICS URL not provided. Set the ICS_URL environment variable.")

    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        raise ValueError("Webhook URL not provided. Set the WEBHOOK_URL environment variable.")

    ics_content = download_ics(ics_url)
    target_date_events = get_events_for_date(ics_content, target_date)

    if target_date_events:
        post_to_slack(webhook_url, target_date_events)
    else:
        print(f"No events found for {target_date}.")

if __name__ == '__main__':
    print("Starting the script...")
    main()
    print("Script execution completed.")

