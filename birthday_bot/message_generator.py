"""OpenAI-powered birthday message generator with historical facts."""

import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import openai

logger = logging.getLogger(__name__)


class MessageGenerator:
    """Generate witty birthday messages using OpenAI with historical facts."""
    
    DEFAULT_PROMPT_TEMPLATE = """It looks like {employee_name} has a birthday coming up on {birthday_date}. Write a witty POSITIVE slack message that mentions something POSITIVE or HAPPY that happened on this date in history (with a specific year), then cleverly connect it to {employee_name}'s birthday without revealing their birth year.

Make sure the historical fact is:
- Genuinely positive and uplifting
- Interesting and engaging
- Appropriate for a workplace setting
- Not controversial or sensitive
- From a specific year (but not their birth year)

The message should be:
- Warm and celebratory
- Playful about not revealing their age (e.g., "on this same date in a year we won't mention", "sometime later", etc.)
- End with birthday wishes using the format: *Happy Birthday {employee_name}!* (with asterisks for bold text)
- Professional but fun
- About 2-3 sentences total
- Ready to post directly to Slack"""

    def __init__(self, openai_api_key: str, data_dir: str = "data", prompts_dir: str = "prompts"):
        """Initialize the message generator.
        
        Args:
            openai_api_key: OpenAI API key
            data_dir: Directory to store data files
            prompts_dir: Directory containing prompt templates
        """
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(exist_ok=True)
        (self.prompts_dir / "history").mkdir(exist_ok=True)
        
        # File paths
        self.default_prompt_file = self.prompts_dir / "default.txt"
        self.current_prompt_file = self.data_dir / "current_prompt.txt"
        self.prompt_history_file = self.data_dir / "prompt_history.json"
        self.history_file = self.data_dir / "birthday_history.json"
        self.messages_file = self.data_dir / "generated_messages.json"
        self.sent_messages_file = self.data_dir / "sent_messages.json"
        
        # Load prompt template and history
        self.prompt_template = self._load_prompt_template()
        self.prompt_history = self._load_prompt_history()
        
        # Load message history
        self.history = self._load_history()
        self.generated_messages = self._load_generated_messages()
        self.sent_messages = self._load_sent_messages()

    def _load_prompt_template(self) -> str:
        """Load prompt template from current or default file."""
        # Check if there's a current active prompt
        if self.current_prompt_file.exists():
            return self.current_prompt_file.read_text().strip()
        
        # Fall back to default prompt from git-controlled file
        if self.default_prompt_file.exists():
            template = self.default_prompt_file.read_text().strip()
            # Copy default to current for editing
            self.current_prompt_file.write_text(template)
            return template
        
        # Last resort: use hardcoded default
        self.current_prompt_file.write_text(self.DEFAULT_PROMPT_TEMPLATE)
        return self.DEFAULT_PROMPT_TEMPLATE

    def _load_prompt_history(self) -> List[Dict[str, Any]]:
        """Load prompt history from file."""
        if self.prompt_history_file.exists():
            with open(self.prompt_history_file, 'r') as f:
                return json.load(f)
        return []

    def _save_prompt_history(self):
        """Save prompt history to file."""
        with open(self.prompt_history_file, 'w') as f:
            json.dump(self.prompt_history, f, indent=2)

    def _save_prompt_template(self, template: str, description: str = ""):
        """Save prompt template and add to history."""
        from datetime import datetime
        
        # Add current template to history before changing
        if hasattr(self, 'prompt_template') and self.prompt_template != template:
            history_entry = {
                "id": len(self.prompt_history) + 1,
                "template": self.prompt_template,
                "description": description or "Previous version",
                "created_at": datetime.utcnow().isoformat(),
                "active": False
            }
            self.prompt_history.append(history_entry)
            
            # Save to history file
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            history_filename = f"prompt_{timestamp}.txt"
            history_file_path = self.prompts_dir / "history" / history_filename
            history_file_path.write_text(self.prompt_template)
        
        # Save new template
        self.current_prompt_file.write_text(template)
        self.prompt_template = template
        
        # Save history
        self._save_prompt_history()

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

    def update_prompt_template(self, new_template: str, description: str = ""):
        """Update the prompt template.
        
        Args:
            new_template: New prompt template with {employee_name} and {birthday_date} placeholders
            description: Description of the change
        """
        if "{employee_name}" not in new_template or "{birthday_date}" not in new_template:
            raise ValueError("Template must contain {employee_name} and {birthday_date} placeholders")
        
        self._save_prompt_template(new_template, description)

    def get_prompt_history(self) -> List[Dict[str, Any]]:
        """Get the prompt history."""
        # Add current template as the first entry
        current_entry = {
            "id": "current",
            "template": self.prompt_template,
            "description": "Current active template",
            "created_at": "current",
            "active": True
        }
        return [current_entry] + self.prompt_history

    def activate_prompt_from_history(self, prompt_id: str) -> bool:
        """Activate a prompt from history."""
        if prompt_id == "current":
            return True  # Already active
        
        # Find the prompt in history
        for entry in self.prompt_history:
            if str(entry["id"]) == str(prompt_id):
                self._save_prompt_template(entry["template"], f"Reactivated: {entry['description']}")
                return True
        
        return False

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
            # If the message was manually edited, keep it unless explicitly regenerating
            existing_msg = self.generated_messages[message_key]
            if existing_msg.get('manually_edited', False):
                logger.info(f"Using manually edited message for {employee_name} on {birthday_date}")
                return existing_msg
            logger.info(f"Using cached message for {employee_name} on {birthday_date}")
            return existing_msg
        
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
            fallback_message = f"🎉 *Happy Birthday {employee_name}!* 🎂 Wishing you a fantastic day filled with joy and celebration!"
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
    
    def _load_sent_messages(self) -> Dict[str, Dict[str, Any]]:
        """Load sent messages tracking."""
        if self.sent_messages_file.exists():
            try:
                return json.loads(self.sent_messages_file.read_text())
            except json.JSONDecodeError:
                logger.error("Failed to load sent messages file, starting fresh")
                return {}
        return {}
    
    def _save_sent_messages(self):
        """Save sent messages tracking."""
        self.sent_messages_file.write_text(json.dumps(self.sent_messages, indent=2))
    
    def mark_message_sent(self, employee_name: str, birthday_date: date, message: str):
        """Mark a message as sent to prevent duplicates."""
        sent_key = f"{employee_name}_{birthday_date.isoformat()}_sent"
        self.sent_messages[sent_key] = {
            "message": message,
            "sent_at": datetime.utcnow().isoformat(),
            "employee_name": employee_name,
            "birthday_date": birthday_date.isoformat()
        }
        self._save_sent_messages()
    
    def was_message_sent_today(self, employee_name: str, birthday_date: date) -> bool:
        """Check if a message was already sent today for this person."""
        sent_key = f"{employee_name}_{birthday_date.isoformat()}_sent"
        if sent_key in self.sent_messages:
            sent_data = self.sent_messages[sent_key]
            sent_at = datetime.fromisoformat(sent_data["sent_at"])
            # Check if sent within the last 24 hours
            if datetime.utcnow() - sent_at < timedelta(hours=24):
                return True
        return False
    
    def clear_sent_tracking(self, employee_name: str, birthday_date: date):
        """Clear sent tracking for a specific person/date to allow resending."""
        sent_key = f"{employee_name}_{birthday_date.isoformat()}_sent"
        if sent_key in self.sent_messages:
            del self.sent_messages[sent_key]
            self._save_sent_messages()
            logger.info(f"Cleared sent tracking for {employee_name} on {birthday_date}")
    
    def update_message(self, employee_name: str, birthday_date: date, new_message: str) -> bool:
        """Update an existing birthday message."""
        message_key = f"{employee_name}_{birthday_date.isoformat()}"
        
        # Check if message exists
        if message_key not in self.generated_messages:
            logger.error(f"No message found for {employee_name} on {birthday_date}")
            return False
        
        try:
            # Update the message
            self.generated_messages[message_key]['message'] = new_message
            self.generated_messages[message_key]['manually_edited'] = True
            self.generated_messages[message_key]['edited_at'] = datetime.utcnow().isoformat()
            
            # Save the updated messages
            self._save_generated_messages()
            
            logger.info(f"Updated message for {employee_name} on {birthday_date}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update message: {e}")
            return False