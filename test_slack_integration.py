#!/usr/bin/env python3
"""Test script to verify Slack integration without waiting for the daily schedule"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_slack_webhook():
    """Send a test message to Slack"""
    webhook_url = os.getenv('WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ WEBHOOK_URL not found in environment")
        return False
    
    # Test message
    message = {
        "text": f"🧪 Test Message from Birthday Bot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nThis is a test to verify Slack integration is working correctly. If you see this message, the webhook is configured properly!"
    }
    
    try:
        response = requests.post(webhook_url, json=message)
        
        if response.status_code == 200:
            print("✅ Test message sent successfully!")
            return True
        else:
            print(f"❌ Failed to send message. Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

if __name__ == "__main__":
    print("Testing Slack webhook integration...")
    test_slack_webhook()