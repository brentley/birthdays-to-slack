#!/usr/bin/env python3
"""Simple test runner script."""

import subprocess
import sys

def main():
    """Run basic tests."""
    print("Running basic validation tests...")
    
    # Test imports
    try:
        import birthday_bot
        print("✓ Birthday bot module imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import birthday_bot: {e}")
        return 1
    
    # Test Flask app
    try:
        from birthday_bot.app import app
        print("✓ Flask app imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import Flask app: {e}")
        return 1
    
    # Test service
    try:
        from birthday_bot.service import BirthdayService
        print("✓ Birthday service imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import service: {e}")
        return 1
    
    # Test message generator
    try:
        from birthday_bot.message_generator import MessageGenerator
        print("✓ Message generator imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import message generator: {e}")
        return 1
    
    print("\nAll basic tests passed!")
    return 0

if __name__ == '__main__':
    sys.exit(main())