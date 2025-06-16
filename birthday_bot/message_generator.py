"""OpenAI-powered birthday message generator with historical facts."""

import os
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from pathlib import Path
import openai

logger = logging.getLogger(__name__)


class MessageGenerator:
    """Generate witty birthday messages using OpenAI with historical facts."""
    
    DEFAULT_PROMPT_TEMPLATE = """It looks like {employee_name} has a birthday coming up on {birthday_date}. Write a witty POSITIVE slack message that mentions something POSITIVE or HAPPY that happened on their birthday in history, and end it with "and also {employee_name} was born. Happy Birthday {employee_name}!"

Make sure the historical fact is:
- Genuinely positive and uplifting
- Interesting and engaging
- Appropriate for a workplace setting
- Not controversial or sensitive

The message should be:
- Warm and celebratory
- Professional but fun
- About 2-3 sentences total
- Ready to post directly to Slack"""

    def __init__(self, openai_api_key: str, data_dir: str = "data"):
        """Initialize the message generator.
        
        Args:
            openai_api_key: OpenAI API key
            data_dir: Directory to store prompts and message history
        """
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # File paths
        self.prompt_file = self.data_dir / "birthday_prompt.txt"
        self.history_file = self.data_dir / "birthday_history.json"
        self.messages_file = self.data_dir / "generated_messages.json"
        
        # Load or create prompt template
        self.prompt_template = self._load_prompt_template()
        
        # Load message history
        self.history = self._load_history()
        self.generated_messages = self._load_generated_messages()

    def _load_prompt_template(self) -> str:
        """Load prompt template from file or use default."""
        if self.prompt_file.exists():
            return self.prompt_file.read_text().strip()
        else:
            # Save default template
            self.prompt_file.write_text(self.DEFAULT_PROMPT_TEMPLATE)
            return self.DEFAULT_PROMPT_TEMPLATE

    def _save_prompt_template(self, template: str):
        """Save prompt template to file."""
        self.prompt_file.write_text(template)
        self.prompt_template = template

    def _load_history(self) -> Dict[str, List[str]]:
        """Load birthday fact history from file."""
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text())
            except json.JSONDecodeError:
                logger.error("Failed to load history file, starting fresh")
                return {}
        return {}

    def _save_history(self):
        """Save birthday fact history to file."""
        self.history_file.write_text(json.dumps(self.history, indent=2))

    def _load_generated_messages(self) -> Dict[str, Dict[str, Any]]:
        """Load previously generated messages."""
        if self.messages_file.exists():
            try:
                return json.loads(self.messages_file.read_text())
            except json.JSONDecodeError:
                logger.error("Failed to load messages file, starting fresh")
                return {}
        return {}

    def _save_generated_messages(self):
        """Save generated messages to file."""
        self.messages_file.write_text(json.dumps(self.generated_messages, indent=2))

    def update_prompt_template(self, new_template: str):
        """Update the prompt template.
        
        Args:
            new_template: New prompt template with {employee_name} and {birthday_date} placeholders
        """
        if "{employee_name}" not in new_template or "{birthday_date}" not in new_template:
            raise ValueError("Template must contain {employee_name} and {birthday_date} placeholders")
        
        self._save_prompt_template(new_template)
        logger.info("Updated birthday prompt template")

    def _extract_historical_fact(self, message: str) -> Optional[str]:
        """Extract the historical fact from a generated message."""
        # Simple extraction - find the part before "and also"
        if "and also" in message.lower():
            fact = message.split("and also")[0].strip()
            # Remove any leading "On this day" or similar phrases
            fact = fact.replace("On this day in history,", "").strip()
            fact = fact.replace("On this day,", "").strip()
            return fact
        return None

    def generate_message(self, employee_name: str, birthday_date: date, regenerate: bool = False) -> Dict[str, Any]:
        """Generate a birthday message for an employee.
        
        Args:
            employee_name: Name of the employee
            birthday_date: Date of the birthday
            regenerate: Force regeneration even if message exists
            
        Returns:
            Dict containing message, historical fact, and metadata
        """
        # Create unique key for this person/date combination
        message_key = f"{employee_name}_{birthday_date.isoformat()}"
        
        # Check if we already have a message for this person/date
        if not regenerate and message_key in self.generated_messages:
            logger.info(f"Using cached message for {employee_name} on {birthday_date}")
            return self.generated_messages[message_key]
        
        # Get previous facts to avoid
        previous_facts = self.history.get(employee_name, [])
        
        # Build the prompt
        prompt = self.prompt_template.format(
            employee_name=employee_name,
            birthday_date=birthday_date.strftime("%B %d")
        )
        
        # Add exclusion instructions if there are previous facts
        if previous_facts:
            exclusions = "\n\nDO NOT use these historical facts that were used in previous years:\n"
            for i, fact in enumerate(previous_facts, 1):
                exclusions += f"{i}. {fact}\n"
            exclusions += "\nInstead, find a different positive historical fact from that date."
            prompt += exclusions
        
        try:
            # Generate message using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a friendly colleague writing birthday messages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=200
            )
            
            message = response.choices[0].message.content.strip()
            
            # Extract historical fact
            fact = self._extract_historical_fact(message)
            
            # Store the result
            result = {
                "message": message,
                "historical_fact": fact,
                "generated_at": datetime.utcnow().isoformat(),
                "employee_name": employee_name,
                "birthday_date": birthday_date.isoformat(),
                "regenerated": regenerate
            }
            
            # Save to generated messages
            self.generated_messages[message_key] = result
            self._save_generated_messages()
            
            # Add fact to history if it's new
            if fact and employee_name in self.history:
                if fact not in self.history[employee_name]:
                    self.history[employee_name].append(fact)
            else:
                self.history[employee_name] = [fact] if fact else []
            self._save_history()
            
            logger.info(f"Generated message for {employee_name}: {message}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate message for {employee_name}: {e}")
            # Return a fallback message
            fallback_message = f"🎉 Happy Birthday {employee_name}! 🎂 Wishing you a fantastic day filled with joy and celebration!"
            return {
                "message": fallback_message,
                "historical_fact": None,
                "generated_at": datetime.utcnow().isoformat(),
                "employee_name": employee_name,
                "birthday_date": birthday_date.isoformat(),
                "error": str(e),
                "fallback": True
            }

    def get_generated_message(self, employee_name: str, birthday_date: date) -> Optional[Dict[str, Any]]:
        """Get a previously generated message if it exists."""
        message_key = f"{employee_name}_{birthday_date.isoformat()}"
        return self.generated_messages.get(message_key)

    def delete_generated_message(self, employee_name: str, birthday_date: date):
        """Delete a generated message to force regeneration."""
        message_key = f"{employee_name}_{birthday_date.isoformat()}"
        if message_key in self.generated_messages:
            del self.generated_messages[message_key]
            self._save_generated_messages()
            logger.info(f"Deleted message for {employee_name} on {birthday_date}")

    def get_all_generated_messages(self) -> Dict[str, Dict[str, Any]]:
        """Get all generated messages."""
        return self.generated_messages.copy()

    def get_employee_history(self, employee_name: str) -> List[str]:
        """Get historical facts used for an employee."""
        return self.history.get(employee_name, [])