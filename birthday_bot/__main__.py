"""Main entry point for Birthday Bot."""

import os
import sys
from birthday_bot.app import app, initialize_service, update_birthday_cache, start_scheduler

if __name__ == '__main__':
    # Initialize services
    initialize_service()
    
    # Initial cache update
    update_birthday_cache()
    
    # Start scheduler
    start_scheduler()
    
    # Run Flask app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"Starting Birthday Bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)