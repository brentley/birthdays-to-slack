"""Tests for the AliasManager class."""

import pytest
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from birthday_bot.alias_manager import AliasManager


class TestAliasManager:
    """Test cases for AliasManager class."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def alias_manager(self, temp_data_dir):
        """Create an AliasManager instance for testing."""
        return AliasManager(data_dir=temp_data_dir)

    def test_init_creates_data_directory(self, temp_data_dir):
        """Test that initialization creates the data directory."""
        data_path = Path(temp_data_dir) / "new_subdir"
        assert not data_path.exists()

        manager = AliasManager(data_dir=str(data_path))

        assert data_path.exists()
        assert manager.data_dir == data_path

    def test_init_creates_empty_aliases_file(self, temp_data_dir):
        """Test that initialization creates empty aliases file."""
        manager = AliasManager(data_dir=temp_data_dir)

        aliases_file = Path(temp_data_dir) / "aliases.json"
        assert aliases_file.exists()

        # Verify file content
        with open(aliases_file, "r") as f:
            data = json.load(f)
            assert data["aliases"] == {}
            assert "last_modified" in data

    def test_init_loads_existing_aliases(self, temp_data_dir):
        """Test that initialization loads existing aliases."""
        # Create aliases file
        aliases_file = Path(temp_data_dir) / "aliases.json"
        test_data = {
            "aliases": {
                "John Doe": {
                    "display_name": "John Michael Doe",
                    "ldap_uid": "john.m.doe",
                    "created_at": "2026-01-09T12:00:00Z",
                    "notes": "Test alias"
                }
            },
            "last_modified": "2026-01-09T12:00:00Z"
        }
        with open(aliases_file, "w") as f:
            json.dump(test_data, f)

        manager = AliasManager(data_dir=temp_data_dir)

        assert len(manager.aliases) == 1
        assert "John Doe" in manager.aliases
        assert manager.aliases["John Doe"]["display_name"] == "John Michael Doe"

    def test_name_to_ldap_uid_basic(self):
        """Test basic name to LDAP uid conversion."""
        assert AliasManager.name_to_ldap_uid("John Doe") == "john.doe"
        assert AliasManager.name_to_ldap_uid("Jane Smith") == "jane.smith"
        assert AliasManager.name_to_ldap_uid("Bob") == "bob"

    def test_name_to_ldap_uid_with_spaces(self):
        """Test name to LDAP uid conversion with multiple spaces."""
        assert AliasManager.name_to_ldap_uid("John Michael Doe") == "john.michael.doe"
        assert AliasManager.name_to_ldap_uid("Mary Ann Smith") == "mary.ann.smith"

    def test_name_to_ldap_uid_with_leading_trailing_spaces(self):
        """Test name to LDAP uid conversion with leading/trailing spaces."""
        assert AliasManager.name_to_ldap_uid("  John Doe  ") == "john.doe"
        assert AliasManager.name_to_ldap_uid("\tJane Smith\t") == "jane.smith"

    def test_name_to_ldap_uid_case_insensitive(self):
        """Test name to LDAP uid conversion is case insensitive."""
        assert AliasManager.name_to_ldap_uid("JOHN DOE") == "john.doe"
        assert AliasManager.name_to_ldap_uid("JoHn DoE") == "john.doe"

    def test_get_display_name_with_alias(self, alias_manager):
        """Test getting display name when alias exists."""
        alias_manager.add_alias("John Doe", "John Michael Doe")

        result = alias_manager.get_display_name("John Doe")

        assert result == "John Michael Doe"

    def test_get_display_name_without_alias(self, alias_manager):
        """Test getting display name when no alias exists."""
        result = alias_manager.get_display_name("Unknown Person")

        assert result == "Unknown Person"

    def test_get_ldap_uid_with_alias(self, alias_manager):
        """Test getting LDAP uid when alias exists."""
        alias_manager.add_alias("John Doe", "John Michael Doe")

        result = alias_manager.get_ldap_uid("John Doe")

        assert result == "john.michael.doe"

    def test_get_ldap_uid_without_alias(self, alias_manager):
        """Test getting LDAP uid when no alias exists (generates from name)."""
        result = alias_manager.get_ldap_uid("John Doe")

        assert result == "john.doe"

    def test_has_alias_true(self, alias_manager):
        """Test has_alias returns True when alias exists."""
        alias_manager.add_alias("John Doe", "John Michael Doe")

        assert alias_manager.has_alias("John Doe") is True

    def test_has_alias_false(self, alias_manager):
        """Test has_alias returns False when alias doesn't exist."""
        assert alias_manager.has_alias("Unknown Person") is False

    def test_get_alias_found(self, alias_manager):
        """Test get_alias returns alias data when found."""
        alias_manager.add_alias("John Doe", "John Michael Doe", "Senior Developer")

        result = alias_manager.get_alias("John Doe")

        assert result is not None
        assert result["display_name"] == "John Michael Doe"
        assert result["ldap_uid"] == "john.michael.doe"
        assert result["notes"] == "Senior Developer"
        assert "created_at" in result

    def test_get_alias_not_found(self, alias_manager):
        """Test get_alias returns None when not found."""
        result = alias_manager.get_alias("Unknown Person")

        assert result is None

    def test_get_alias_returns_copy(self, alias_manager):
        """Test that get_alias returns a copy, not a reference."""
        alias_manager.add_alias("John Doe", "John Michael Doe")

        alias1 = alias_manager.get_alias("John Doe")
        alias1["display_name"] = "Modified Name"

        alias2 = alias_manager.get_alias("John Doe")

        assert alias2["display_name"] == "John Michael Doe"

    def test_get_all_aliases_empty(self, alias_manager):
        """Test get_all_aliases returns empty dict when no aliases."""
        result = alias_manager.get_all_aliases()

        assert result == {}

    def test_get_all_aliases_multiple(self, alias_manager):
        """Test get_all_aliases returns all aliases."""
        alias_manager.add_alias("John Doe", "John Michael Doe")
        alias_manager.add_alias("Jane Smith", "Jane Ann Smith")
        alias_manager.add_alias("Bob Johnson", "Robert Johnson")

        result = alias_manager.get_all_aliases()

        assert len(result) == 3
        assert result["John Doe"]["display_name"] == "John Michael Doe"
        assert result["Jane Smith"]["display_name"] == "Jane Ann Smith"
        assert result["Bob Johnson"]["display_name"] == "Robert Johnson"

    def test_get_all_aliases_returns_copy(self, alias_manager):
        """Test that get_all_aliases returns copies, not references."""
        alias_manager.add_alias("John Doe", "John Michael Doe")

        result1 = alias_manager.get_all_aliases()
        result1["John Doe"]["display_name"] = "Modified Name"

        result2 = alias_manager.get_all_aliases()

        assert result2["John Doe"]["display_name"] == "John Michael Doe"

    def test_add_alias_success(self, alias_manager):
        """Test adding a new alias."""
        result = alias_manager.add_alias("John Doe", "John Michael Doe", "Developer")

        assert result["display_name"] == "John Michael Doe"
        assert result["ldap_uid"] == "john.michael.doe"
        assert result["notes"] == "Developer"
        assert "created_at" in result
        assert alias_manager.has_alias("John Doe")

    def test_add_alias_empty_notes(self, alias_manager):
        """Test adding alias with empty notes."""
        result = alias_manager.add_alias("John Doe", "John Michael Doe")

        assert result["notes"] == ""

    def test_add_alias_persists_to_file(self, temp_data_dir):
        """Test that added alias is persisted to file."""
        manager1 = AliasManager(data_dir=temp_data_dir)
        manager1.add_alias("John Doe", "John Michael Doe")

        # Load in a new instance
        manager2 = AliasManager(data_dir=temp_data_dir)

        assert manager2.has_alias("John Doe")
        assert manager2.get_display_name("John Doe") == "John Michael Doe"

    def test_add_alias_duplicate_raises_error(self, alias_manager):
        """Test that adding duplicate alias raises ValueError."""
        alias_manager.add_alias("John Doe", "John Michael Doe")

        with pytest.raises(ValueError, match="Alias already exists"):
            alias_manager.add_alias("John Doe", "Different Name")

    def test_add_alias_updates_last_modified(self, temp_data_dir):
        """Test that adding alias updates last_modified timestamp."""
        manager = AliasManager(data_dir=temp_data_dir)
        initial_modified = manager.last_modified

        manager.add_alias("John Doe", "John Michael Doe")

        # Parse timestamps to compare
        initial_dt = datetime.fromisoformat(initial_modified.rstrip("Z"))
        new_dt = datetime.fromisoformat(manager.last_modified.rstrip("Z"))

        assert new_dt >= initial_dt

    def test_update_alias_success(self, alias_manager):
        """Test updating an existing alias."""
        alias_manager.add_alias("John Doe", "John Michael Doe", "Developer")

        result = alias_manager.update_alias("John Doe", "John Marcus Doe", "Senior Dev")

        assert result["display_name"] == "John Marcus Doe"
        assert result["ldap_uid"] == "john.marcus.doe"
        assert result["notes"] == "Senior Dev"

    def test_update_alias_partial_update(self, alias_manager):
        """Test updating only display_name without changing notes."""
        alias_manager.add_alias("John Doe", "John Michael Doe", "Developer")

        result = alias_manager.update_alias("John Doe", "John M. Doe")

        assert result["display_name"] == "John M. Doe"
        assert result["notes"] == "Developer"  # Original notes preserved

    def test_update_alias_not_found(self, alias_manager):
        """Test updating non-existent alias returns None."""
        result = alias_manager.update_alias("Unknown Person", "New Name")

        assert result is None

    def test_update_alias_persists_to_file(self, temp_data_dir):
        """Test that updated alias is persisted to file."""
        manager1 = AliasManager(data_dir=temp_data_dir)
        manager1.add_alias("John Doe", "John Michael Doe")
        manager1.update_alias("John Doe", "John Marcus Doe")

        # Load in a new instance
        manager2 = AliasManager(data_dir=temp_data_dir)

        assert manager2.get_display_name("John Doe") == "John Marcus Doe"
        assert manager2.get_ldap_uid("John Doe") == "john.marcus.doe"

    def test_update_alias_updates_ldap_uid(self, alias_manager):
        """Test that updating display name updates LDAP uid."""
        alias_manager.add_alias("John Doe", "John Michael Doe")
        assert alias_manager.get_ldap_uid("John Doe") == "john.michael.doe"

        alias_manager.update_alias("John Doe", "Robert Smith")

        assert alias_manager.get_ldap_uid("John Doe") == "robert.smith"

    def test_delete_alias_success(self, alias_manager):
        """Test deleting an alias."""
        alias_manager.add_alias("John Doe", "John Michael Doe")

        result = alias_manager.delete_alias("John Doe")

        assert result is True
        assert not alias_manager.has_alias("John Doe")

    def test_delete_alias_not_found(self, alias_manager):
        """Test deleting non-existent alias returns False."""
        result = alias_manager.delete_alias("Unknown Person")

        assert result is False

    def test_delete_alias_persists_to_file(self, temp_data_dir):
        """Test that deleted alias is removed from file."""
        manager1 = AliasManager(data_dir=temp_data_dir)
        manager1.add_alias("John Doe", "John Michael Doe")
        manager1.delete_alias("John Doe")

        # Load in a new instance
        manager2 = AliasManager(data_dir=temp_data_dir)

        assert not manager2.has_alias("John Doe")

    def test_workflow_add_update_delete(self, alias_manager):
        """Test complete workflow: add, update, and delete."""
        # Add
        alias_manager.add_alias("John Doe", "John Michael Doe", "Developer")
        assert alias_manager.get_display_name("John Doe") == "John Michael Doe"

        # Update
        alias_manager.update_alias("John Doe", "John Marcus Doe", "Senior Dev")
        assert alias_manager.get_display_name("John Doe") == "John Marcus Doe"
        assert alias_manager.get_ldap_uid("John Doe") == "john.marcus.doe"

        # Delete
        assert alias_manager.delete_alias("John Doe") is True
        assert not alias_manager.has_alias("John Doe")

    def test_multiple_aliases_independent(self, alias_manager):
        """Test that multiple aliases are independent."""
        alias_manager.add_alias("John Doe", "John Michael Doe")
        alias_manager.add_alias("Jane Smith", "Jane Ann Smith")

        alias_manager.update_alias("John Doe", "John M. Doe")

        # Jane's alias should be unchanged
        assert alias_manager.get_display_name("Jane Smith") == "Jane Ann Smith"

    def test_json_schema_structure(self, temp_data_dir):
        """Test that JSON file has correct schema."""
        manager = AliasManager(data_dir=temp_data_dir)
        manager.add_alias("John Doe", "John Michael Doe", "Developer")

        aliases_file = Path(temp_data_dir) / "aliases.json"
        with open(aliases_file, "r") as f:
            data = json.load(f)

        # Verify top-level structure
        assert "aliases" in data
        assert "last_modified" in data

        # Verify alias structure
        alias = data["aliases"]["John Doe"]
        assert "display_name" in alias
        assert "ldap_uid" in alias
        assert "created_at" in alias
        assert "notes" in alias

    def test_timestamps_are_iso_format_with_z(self, alias_manager):
        """Test that timestamps are in ISO format with Z suffix."""
        alias_manager.add_alias("John Doe", "John Michael Doe")

        alias = alias_manager.get_alias("John Doe")
        created_at = alias["created_at"]

        # Should end with Z and be parseable as ISO format
        assert created_at.endswith("Z")
        # Remove Z and parse to verify it's valid ISO format
        datetime.fromisoformat(created_at.rstrip("Z"))

    def test_case_sensitive_calendar_names(self, alias_manager):
        """Test that calendar names are case sensitive."""
        alias_manager.add_alias("John Doe", "John Michael Doe")

        # Different case should be treated as different calendar name
        assert alias_manager.has_alias("John Doe")
        assert not alias_manager.has_alias("john doe")
        assert alias_manager.get_display_name("john doe") == "john doe"

    def test_special_characters_in_display_name(self, alias_manager):
        """Test handling special characters in display names."""
        alias_manager.add_alias("John Doe", "John O'Brien-Smith")

        alias = alias_manager.get_alias("John Doe")

        assert alias["display_name"] == "John O'Brien-Smith"
        # LDAP uid converts special chars appropriately
        assert alias["ldap_uid"] == "john.o'brien-smith"

    def test_concurrent_additions_overwrite_prevention(self, temp_data_dir):
        """Test that duplicate additions raise error even with timing issues."""
        manager = AliasManager(data_dir=temp_data_dir)

        manager.add_alias("John Doe", "John Michael Doe")

        # Try to add again - should raise error
        with pytest.raises(ValueError):
            manager.add_alias("John Doe", "Different Name")

        # Original should be preserved
        assert manager.get_display_name("John Doe") == "John Michael Doe"
