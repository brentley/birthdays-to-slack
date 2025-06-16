#!/usr/bin/env python3

import os
import ldap3
from ldap3 import Server, Connection, ALL_ATTRIBUTES, Tls, SASL, EXTERNAL, SUBTREE
import ssl
import requests
from icalendar import Calendar
import logging
from datetime import datetime

# Setup basic configuration for logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def download_ics(ics_url):
    logging.info(f"Downloading ICS file from {ics_url}")
    response = requests.get(ics_url)
    response.raise_for_status()

    if 'text/calendar' not in response.headers.get('Content-Type', ''):
        raise ValueError("Downloaded file is not an ICS file based on Content-Type header.")

    return response.content

def get_events_for_date(ics_content, target_date):
    logging.info(f"Parsing the ICS file for events on {target_date}")
    calendar = Calendar.from_ical(ics_content)
    target_date_events = []

    for component in calendar.walk():
        if component.name == "VEVENT":
            event_start = component.get('dtstart').dt
            event_start_date = event_start.date() if hasattr(event_start, 'date') else event_start

            if event_start_date == target_date:
                event_summary = component.get('summary')
                if '-' in event_summary:
                    full_name = event_summary.split('-')[0].strip()
                    if verify_person_in_ldap(full_name):
                        message = f":birthday: Happy Birthday {full_name}! :tada:"
                        target_date_events.append(message)

    return target_date_events

def verify_person_in_ldap(full_name):
    ldap_server = os.getenv('LDAP_SERVER')
    search_base = os.getenv('SEARCH_BASE')
    first_last = full_name.replace(' ', '.').lower()
    search_filter = f"(uid={first_last})"

    # Specify the client certificates explicitly
    tls_configuration = Tls(local_private_key_file='/app/certs/ldapcertificate.key',
                            local_certificate_file='/app/certs/ldapcertificate.crt',
                            validate=ssl.CERT_NONE)  # Disabling certificate validation

    server = Server(ldap_server, use_ssl=True, tls=tls_configuration)

    try:
        conn = Connection(server, authentication=SASL, sasl_mechanism=EXTERNAL, auto_bind=True)
        conn.search(search_base, search_filter, search_scope=SUBTREE, attributes=ALL_ATTRIBUTES)
        if conn.entries:
            entry = conn.entries[0]
            suspended = entry.suspended.value if 'suspended' in entry else 'unknown'
            conn.unbind()
            return suspended.lower() == 'false'
        else:
            logging.warning(f"No entries found for user {first_last}")
    except Exception as e:
        logging.error(f"LDAP operation failed: {e}")
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

    return False

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Please use YYYY-MM-DD format.")

def main():
    target_date_str = os.getenv('TARGET_DATE')
    target_date = parse_date(target_date_str) if target_date_str else datetime.now().date()

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
        logging.info("No events found for the target date.")

def post_to_slack(webhook_url, messages):
    for message in messages:
        data = {"text": message}
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
        logging.info(f"Posted message to Slack: {message}")

if __name__ == '__main__':
    logging.info("Starting the script...")
    main()
    logging.info("Script execution completed.")

