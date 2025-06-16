"""Tests for the OpenAI message generator."""

import pytest
from datetime import date
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import tempfile
import shutil
from birthday_bot.message_generator import MessageGenerator


class TestMessageGenerator:
    """Test cases for MessageGenerator class."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        with patch('birthday_bot.message_generator.openai.OpenAI') as mock_client:
            # Mock the completion response
            mock_response = Mock()
            mock_response.choices = [
                Mock(message=Mock(content="On this day in 1969, the first Moon landing occurred, and also John Doe was born. Happy Birthday John Doe!"))
            ]
            mock_client.return_value.chat.completions.create.return_value = mock_response
            yield mock_client

    def test_init(self, temp_data_dir, mock_openai_client):
        """Test MessageGenerator initialization."""
        # Create prompts directory structure
        prompts_dir = Path(temp_data_dir) / "prompts"
        prompts_dir.mkdir(exist_ok=True)
        
        generator = MessageGenerator("test-api-key", temp_data_dir, str(prompts_dir))
        
        assert generator.data_dir == Path(temp_data_dir)
        # The prompt template will be the new default template
        assert "Write a birthday message for {employee_name}" in generator.prompt_template
        assert "whose birthday is {birthday_date}" in generator.prompt_template
        mock_openai_client.assert_called_once_with(api_key="test-api-key")

    def test_load_custom_prompt_template(self, temp_data_dir, mock_openai_client):
        """Test loading a custom prompt template."""
        # Create prompts directory structure
        prompts_dir = Path(temp_data_dir) / "prompts"
        prompts_dir.mkdir(exist_ok=True)
        
        custom_prompt = "Custom prompt for {employee_name} on {birthday_date}"
        prompt_file = Path(temp_data_dir) / "current_prompt.txt"
        prompt_file.write_text(custom_prompt)
        
        generator = MessageGenerator("test-api-key", temp_data_dir, str(prompts_dir))
        
        assert generator.prompt_template == custom_prompt

    def test_update_prompt_template(self, temp_data_dir, mock_openai_client):
        """Test updating the prompt template."""
        # Create prompts directory structure
        prompts_dir = Path(temp_data_dir) / "prompts"
        prompts_dir.mkdir(exist_ok=True)
        
        generator = MessageGenerator("test-api-key", temp_data_dir, str(prompts_dir))
        new_template = "New template for {employee_name} on {birthday_date}"
        
        generator.update_prompt_template(new_template)
        
        assert generator.prompt_template == new_template
        assert Path(temp_data_dir, "current_prompt.txt").read_text() == new_template

    def test_update_prompt_template_missing_placeholders(self, temp_data_dir, mock_openai_client):
        """Test updating prompt template with missing placeholders."""
        # Create prompts directory structure
        prompts_dir = Path(temp_data_dir) / "prompts"
        prompts_dir.mkdir(exist_ok=True)
        
        generator = MessageGenerator("test-api-key", temp_data_dir, str(prompts_dir))
        
        with pytest.raises(ValueError, match="must contain"):
            generator.update_prompt_template("Invalid template without placeholders")

    def test_generate_message_success(self, temp_data_dir, mock_openai_client):
        """Test successful message generation."""
        generator = MessageGenerator("test-api-key", temp_data_dir)
        
        result = generator.generate_message("John Doe", date(2024, 3, 15))
        
        assert result['employee_name'] == "John Doe"
        assert result['birthday_date'] == "2024-03-15"
        assert "Moon landing" in result['message']
        assert "Happy Birthday John Doe!" in result['message']
        assert result['historical_fact'] is not None
        assert not result.get('error')

    def test_generate_message_cached(self, temp_data_dir, mock_openai_client):
        """Test that cached messages are returned without regenerating."""
        generator = MessageGenerator("test-api-key", temp_data_dir)
        
        # Generate once
        result1 = generator.generate_message("John Doe", date(2024, 3, 15))
        
        # Generate again - should use cache
        result2 = generator.generate_message("John Doe", date(2024, 3, 15))
        
        assert result1 == result2
        # OpenAI should only be called once
        assert mock_openai_client.return_value.chat.completions.create.call_count == 1

    def test_generate_message_regenerate(self, temp_data_dir, mock_openai_client):
        """Test message regeneration."""
        generator = MessageGenerator("test-api-key", temp_data_dir)
        
        # Generate once
        result1 = generator.generate_message("John Doe", date(2024, 3, 15))
        
        # Mock a different response for regeneration
        mock_openai_client.return_value.chat.completions.create.return_value.choices[0].message.content = \
            "On this day in 1876, the telephone was invented, and also John Doe was born. Happy Birthday John Doe!"
        
        # Regenerate
        result2 = generator.generate_message("John Doe", date(2024, 3, 15), regenerate=True)
        
        assert result1['message'] != result2['message']
        assert "telephone" in result2['message']
        assert result2['regenerated'] is True

    def test_generate_message_with_history(self, temp_data_dir, mock_openai_client):
        """Test message generation with previous history."""
        generator = MessageGenerator("test-api-key", temp_data_dir)
        
        # Add some history
        generator.history["John Doe"] = ["Moon landing fact", "Telephone invention fact"]
        generator._save_history()
        
        # Generate new message
        generator.generate_message("John Doe", date(2024, 3, 15))
        
        # Check that the prompt included exclusions
        call_args = mock_openai_client.return_value.chat.completions.create.call_args
        prompt = call_args[1]['messages'][1]['content']
        assert "DO NOT use these historical facts" in prompt
        assert "Moon landing fact" in prompt
        assert "Telephone invention fact" in prompt

    def test_generate_message_api_error(self, temp_data_dir, mock_openai_client):
        """Test message generation with API error."""
        generator = MessageGenerator("test-api-key", temp_data_dir)
        
        # Mock API error
        mock_openai_client.return_value.chat.completions.create.side_effect = Exception("API Error")
        
        result = generator.generate_message("John Doe", date(2024, 3, 15))
        
        assert result['error'] == "API Error"
        assert result['fallback'] is True
        assert "Happy Birthday John Doe!" in result['message']

    def test_extract_historical_fact(self, temp_data_dir, mock_openai_client):
        """Test extracting historical fact from message."""
        generator = MessageGenerator("test-api-key", temp_data_dir)
        
        message1 = "On this day in 1969, the Moon landing occurred, and also John was born. Happy Birthday!"
        fact1 = generator._extract_historical_fact(message1)
        assert fact1 == "On this day in 1969, the Moon landing occurred,"
        
        message2 = "Today is special because the telephone was invented and also Jane was born!"
        fact2 = generator._extract_historical_fact(message2)
        assert fact2 == "Today is special because the telephone was invented"

    def test_delete_generated_message(self, temp_data_dir, mock_openai_client):
        """Test deleting a generated message."""
        generator = MessageGenerator("test-api-key", temp_data_dir)
        
        # Generate a message
        generator.generate_message("John Doe", date(2024, 3, 15))
        assert generator.get_generated_message("John Doe", date(2024, 3, 15)) is not None
        
        # Delete it
        generator.delete_generated_message("John Doe", date(2024, 3, 15))
        assert generator.get_generated_message("John Doe", date(2024, 3, 15)) is None

    def test_persistence(self, temp_data_dir, mock_openai_client):
        """Test that data persists between instances."""
        # First instance
        generator1 = MessageGenerator("test-api-key", temp_data_dir)
        generator1.generate_message("John Doe", date(2024, 3, 15))
        generator1.update_prompt_template("Custom {employee_name} {birthday_date}")
        
        # Second instance should load the data
        generator2 = MessageGenerator("test-api-key", temp_data_dir)
        
        assert generator2.prompt_template == "Custom {employee_name} {birthday_date}"
        assert generator2.get_generated_message("John Doe", date(2024, 3, 15)) is not None
        assert "John Doe" in generator2.history

    def test_get_all_generated_messages(self, temp_data_dir, mock_openai_client):
        """Test getting all generated messages."""
        generator = MessageGenerator("test-api-key", temp_data_dir)
        
        # Generate multiple messages
        generator.generate_message("John Doe", date(2024, 3, 15))
        generator.generate_message("Jane Smith", date(2024, 3, 16))
        
        all_messages = generator.get_all_generated_messages()
        
        assert len(all_messages) == 2
        assert "John Doe_2024-03-15" in all_messages
        assert "Jane Smith_2024-03-16" in all_messages

    def test_get_employee_history(self, temp_data_dir, mock_openai_client):
        """Test getting employee history."""
        generator = MessageGenerator("test-api-key", temp_data_dir)
        
        # Generate messages for multiple years
        generator.generate_message("John Doe", date(2023, 3, 15))
        generator.generate_message("John Doe", date(2024, 3, 15))
        
        history = generator.get_employee_history("John Doe")
        
        assert len(history) >= 1  # At least one fact should be extracted
        
        # Test empty history
        empty_history = generator.get_employee_history("Unknown Person")
        assert empty_history == []