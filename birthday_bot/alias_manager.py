"""Manage calendar name to display name aliases with LDAP uid mapping."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class AliasManager:
    """Manages aliases for calendar names to display names with LDAP uid mapping."""

    def __init__(self, data_dir: str = "data") -> None:
        """Initialize the alias manager and load aliases from file.

        Args:
            data_dir: Directory to store aliases.json file. Defaults to "data".
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.aliases_file = self.data_dir / "aliases.json"

        # Load aliases from file
        self.aliases: Dict[str, Dict[str, Any]] = {}
        self.last_modified: str = datetime.utcnow().isoformat() + "Z"
        self._load_aliases()
        logger.info(f"AliasManager initialized with data_dir={data_dir}")

    def _load_aliases(self) -> None:
        """Load aliases from JSON file.

        Creates an empty aliases file if it doesn't exist.
        """
        try:
            if self.aliases_file.exists():
                with open(self.aliases_file, "r") as f:
                    data = json.load(f)
                    self.aliases = data.get("aliases", {})
                    default_timestamp = datetime.utcnow().isoformat() + "Z"
                    self.last_modified = data.get("last_modified", default_timestamp)
                logger.debug(
                    f"Loaded {len(self.aliases)} aliases from {self.aliases_file}"
                )
            else:
                logger.info(
                    f"No aliases file found at {self.aliases_file}, "
                    "creating empty structure"
                )
                self._save_aliases()
        except Exception as e:
            logger.error(f"Failed to load aliases from {self.aliases_file}: {e}")
            self.aliases = {}
            self.last_modified = datetime.utcnow().isoformat() + "Z"

    def _save_aliases(self) -> None:
        """Save aliases to JSON file."""
        try:
            self.last_modified = datetime.utcnow().isoformat() + "Z"
            data = {
                "aliases": self.aliases,
                "last_modified": self.last_modified
            }
            with open(self.aliases_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.aliases)} aliases to {self.aliases_file}")
        except Exception as e:
            logger.error(f"Failed to save aliases to {self.aliases_file}: {e}")

    @staticmethod
    def name_to_ldap_uid(name: str) -> str:
        """Convert display name to LDAP uid format.

        Converts spaces to dots and converts to lowercase.
        Example: "John Doe" -> "john.doe"

        Args:
            name: Display name to convert

        Returns:
            LDAP uid format string
        """
        return name.strip().replace(" ", ".").lower()

    def get_display_name(self, calendar_name: str) -> str:
        """Get display name for a calendar name.

        Args:
            calendar_name: Name from calendar event

        Returns:
            Display name if alias exists, otherwise returns original calendar_name
        """
        if calendar_name in self.aliases:
            display_name = self.aliases[calendar_name].get("display_name")
            if isinstance(display_name, str):
                return display_name
        return calendar_name

    def get_ldap_uid(self, calendar_name: str) -> str:
        """Get LDAP uid for a calendar name.

        Args:
            calendar_name: Name from calendar event

        Returns:
            LDAP uid if alias exists, otherwise generates from calendar_name
        """
        if calendar_name in self.aliases:
            ldap_uid = self.aliases[calendar_name].get("ldap_uid")
            if isinstance(ldap_uid, str):
                return ldap_uid

        # Generate LDAP uid from calendar_name if no alias
        return self.name_to_ldap_uid(calendar_name)

    def has_alias(self, calendar_name: str) -> bool:
        """Check if an alias exists for the given calendar name.

        Args:
            calendar_name: Name from calendar event

        Returns:
            True if alias exists, False otherwise
        """
        return calendar_name in self.aliases

    def get_alias(self, calendar_name: str) -> Optional[Dict[str, Any]]:
        """Get a single alias by calendar name.

        Args:
            calendar_name: Name from calendar event

        Returns:
            Alias dictionary if exists, None otherwise
        """
        if calendar_name in self.aliases:
            return self.aliases[calendar_name].copy()
        return None

    def get_all_aliases(self) -> Dict[str, Dict[str, Any]]:
        """Get all aliases.

        Returns:
            Dictionary of all aliases (deep copy to prevent external modification)
        """
        return {
            calendar_name: alias.copy()
            for calendar_name, alias in self.aliases.items()
        }

    def add_alias(self, calendar_name: str, display_name: str, notes: str = "") -> Dict[str, Any]:
        """Add a new alias.

        Args:
            calendar_name: Name from calendar event
            display_name: Display name for the person
            notes: Optional notes about the alias

        Returns:
            The created alias dictionary

        Raises:
            ValueError: If alias already exists for calendar_name
        """
        if calendar_name in self.aliases:
            raise ValueError(f"Alias already exists for calendar_name='{calendar_name}'")

        ldap_uid = self.name_to_ldap_uid(display_name)
        created_at = datetime.utcnow().isoformat() + "Z"

        alias_data = {
            "display_name": display_name,
            "ldap_uid": ldap_uid,
            "created_at": created_at,
            "notes": notes
        }

        self.aliases[calendar_name] = alias_data
        self._save_aliases()

        logger.info(f"Added alias: {calendar_name} -> {display_name} (ldap_uid={ldap_uid})")
        return alias_data.copy()

    def update_alias(
        self,
        calendar_name: str,
        display_name: str,
        notes: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing alias.

        Args:
            calendar_name: Name from calendar event
            display_name: New display name for the person
            notes: Optional notes to update (None to keep existing)

        Returns:
            Updated alias dictionary if successful, None if alias not found
        """
        if calendar_name not in self.aliases:
            logger.warning(f"Cannot update non-existent alias for calendar_name='{calendar_name}'")
            return None

        alias = self.aliases[calendar_name]
        old_display_name = alias.get("display_name")
        old_ldap_uid = alias.get("ldap_uid")

        # Update display name and LDAP uid
        alias["display_name"] = display_name
        alias["ldap_uid"] = self.name_to_ldap_uid(display_name)

        # Update notes if provided
        if notes is not None:
            alias["notes"] = notes

        self._save_aliases()

        logger.info(
            f"Updated alias: {calendar_name} -> "
            f"{old_display_name} ({old_ldap_uid}) to "
            f"{display_name} ({alias['ldap_uid']})"
        )
        return alias.copy()

    def delete_alias(self, calendar_name: str) -> bool:
        """Delete an alias.

        Args:
            calendar_name: Name from calendar event

        Returns:
            True if deleted successfully, False if alias not found
        """
        if calendar_name not in self.aliases:
            logger.warning(f"Cannot delete non-existent alias for calendar_name='{calendar_name}'")
            return False

        deleted_alias = self.aliases.pop(calendar_name)
        self._save_aliases()

        logger.info(
            f"Deleted alias: {calendar_name} -> {deleted_alias.get('display_name')}"
        )
        return True
