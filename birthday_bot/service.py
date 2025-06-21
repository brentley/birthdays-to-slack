#!/usr/bin/env python3

import os
import ldap3
from ldap3 import Server, Connection, ALL_ATTRIBUTES, Tls, SASL, EXTERNAL, SUBTREE
import ssl
import requests
from icalendar import Calendar
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from birthday_bot.message_generator import MessageGenerator

logger = logging.getLogger(__name__)

class BirthdayService:
    def __init__(self, ics_url: str, webhook_url: str, ldap_server: str, search_base: str, 
                 openai_api_key: Optional[str] = None):
        self.ics_url = ics_url
        self.webhook_url = webhook_url
        self.ldap_server = ldap_server
        self.search_base = search_base
        
        # Initialize message generator if OpenAI key is provided
        self.message_generator = None
        if openai_api_key:
            try:
                self.message_generator = MessageGenerator(openai_api_key)
                logger.info("OpenAI message generator initialized")
            except Exception as e:
                logger.error(f"Failed to initialize message generator: {e}")
        else:
            logger.warning("No OpenAI API key provided, using simple messages")
        
    def download_ics(self) -> bytes:
        """Download ICS file from the configured URL"""
        logger.info(f"Downloading ICS file from {self.ics_url}")
        response = requests.get(self.ics_url, timeout=30)
        response.raise_for_status()

        if 'text/calendar' not in response.headers.get('Content-Type', ''):
            raise ValueError("Downloaded file is not an ICS file based on Content-Type header.")

        return response.content

    def get_birthday_events_for_date(self, target_date: date) -> List[Dict[str, Any]]:
        """Get birthday events for a specific date with LDAP validation"""
        logger.info(f"Getting birthday events for {target_date}")
        
        try:
            ics_content = self.download_ics()
            calendar = Calendar.from_ical(ics_content)
            events = []

            for component in calendar.walk():
                if component.name == "VEVENT":
                    event_start = component.get('dtstart').dt
                    event_start_date = event_start.date() if hasattr(event_start, 'date') else event_start

                    if event_start_date == target_date:
                        event_summary = component.get('summary')
                        if '-' in str(event_summary):
                            full_name = str(event_summary).split('-')[0].strip()
                            
                            # Check LDAP validation
                            ldap_valid = self.verify_person_in_ldap(full_name)
                            
                            # Generate or get message
                            message_data = None
                            if ldap_valid and self.message_generator:
                                try:
                                    message_data = self.message_generator.generate_message(
                                        full_name, target_date
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to generate message for {full_name}: {e}")
                            
                            # Use generated message or fallback
                            if message_data and not message_data.get('error'):
                                message = message_data['message']
                            else:
                                message = f":birthday: Happy Birthday {full_name}! :tada:" if ldap_valid else None
                            
                            event_data = {
                                'name': full_name,
                                'summary': str(event_summary),
                                'date': target_date.isoformat(),
                                'ldap_valid': ldap_valid,
                                'will_send': ldap_valid,  # Only send if LDAP valid
                                'message': message,
                                'message_data': message_data  # Include full message data for UI
                            }
                            events.append(event_data)

            logger.info(f"Found {len(events)} birthday events for {target_date}")
            return events
            
        except Exception as e:
            logger.error(f"Error getting birthday events for {target_date}: {e}")
            return []

    def verify_person_in_ldap(self, full_name: str) -> bool:
        """Verify if a person exists in LDAP"""
        try:
            first_last = full_name.replace(' ', '.').lower()
            search_filter = f"(uid={first_last})"
            
            # Use TLS for secure connection
            tls_configuration = Tls(
                local_private_key_file='certs/ldapcertificate.key',
                local_certificate_file='certs/ldapcertificate.crt',
                validate=ssl.CERT_NONE,
                version=ssl.PROTOCOL_TLSv1_2
            )
            
            server = Server(self.ldap_server, use_ssl=True, tls=tls_configuration)
            
            with Connection(server, authentication=SASL, sasl_mechanism=EXTERNAL, auto_bind=True) as conn:
                conn.search(
                    search_base=self.search_base,
                    search_filter=search_filter,
                    search_scope=SUBTREE,
                    attributes=ALL_ATTRIBUTES
                )
                
                found = len(conn.entries) > 0
                logger.debug(f"LDAP verification for '{full_name}' ({first_last}): {'found' if found else 'not found'}")
                return found
                
        except Exception as e:
            logger.error(f"LDAP verification failed for '{full_name}': {e}")
            return False

    def send_birthday_messages(self, target_date: date) -> List[str]:
        """Send birthday messages for the specified date"""
        events = self.get_birthday_events_for_date(target_date)
        sent_messages = []
        
        for event in events:
            if event['will_send'] and event['message']:
                # Check if message was already sent today
                if self.message_generator and self.message_generator.was_message_sent_today(event['name'], target_date):
                    logger.info(f"Skipping {event['name']} - message already sent today")
                    continue
                
                try:
                    self.send_slack_message(event['message'])
                    sent_messages.append(event['message'])
                    logger.info(f"Sent birthday message for {event['name']}")
                    
                    # Mark message as sent
                    if self.message_generator:
                        self.message_generator.mark_message_sent(event['name'], target_date, event['message'])
                        
                except Exception as e:
                    logger.error(f"Failed to send birthday message for {event['name']}: {e}")
        
        logger.info(f"Sent {len(sent_messages)} birthday messages for {target_date}")
        return sent_messages

    def send_slack_message(self, message: str):
        """Send a message to Slack using the webhook URL"""
        if not self.webhook_url:
            logger.warning("No webhook URL configured, skipping Slack message")
            return
        
        # Check if Slack notifications are enabled
        slack_enabled = os.getenv('SLACK_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        
        if not slack_enabled:
            logger.info(f"Slack notifications disabled. Would have sent: {message}")
            return
            
        payload = {'text': message}
        response = requests.post(self.webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Slack message sent: {message}")

    def regenerate_message(self, employee_name: str, birthday_date: date) -> Optional[Dict[str, Any]]:
        """Regenerate a birthday message for an employee."""
        if not self.message_generator:
            logger.error("Message generator not initialized")
            return None
        
        try:
            # Delete existing message to force regeneration
            self.message_generator.delete_generated_message(employee_name, birthday_date)
            
            # Generate new message
            return self.message_generator.generate_message(
                employee_name, birthday_date, regenerate=True
            )
        except Exception as e:
            logger.error(f"Failed to regenerate message for {employee_name}: {e}")
            return None

    def get_prompt_template(self) -> Optional[str]:
        """Get the current prompt template."""
        if self.message_generator:
            return self.message_generator.prompt_template
        return None

    def update_prompt_template(self, new_template: str, description: str = "") -> bool:
        """Update the prompt template."""
        if not self.message_generator:
            logger.error("Message generator not initialized")
            return False
        
        try:
            self.message_generator.update_prompt_template(new_template, description)
            return True
        except Exception as e:
            logger.error(f"Failed to update prompt template: {e}")
            return False

    def get_prompt_history(self) -> List[Dict[str, Any]]:
        """Get prompt template history."""
        if self.message_generator:
            return self.message_generator.get_prompt_history()
        return []

    def activate_prompt_from_history(self, prompt_id: str) -> bool:
        """Activate a prompt from history."""
        if not self.message_generator:
            return False
        return self.message_generator.activate_prompt_from_history(prompt_id)

    def get_service_status(self) -> Dict[str, Any]:
        """Get service status information"""
        return {
            'ics_url_configured': bool(self.ics_url),
            'webhook_url_configured': bool(self.webhook_url),
            'ldap_server_configured': bool(self.ldap_server),
            'search_base_configured': bool(self.search_base),
            'openai_configured': bool(self.message_generator)
        }
    
    def update_message(self, employee_name: str, birthday_date: date, new_message: str) -> bool:
        """Update a birthday message for a specific employee."""
        if not self.message_generator:
            logger.error("Message generator not initialized")
            return False
        
        try:
            # Update the message in the generator
            return self.message_generator.update_message(employee_name, birthday_date, new_message)
        except Exception as e:
            logger.error(f"Failed to update message for {employee_name}: {e}")
            return False