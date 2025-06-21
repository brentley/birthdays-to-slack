#!/usr/bin/env python3

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from threading import Lock
import json
import time

from birthday_bot.service import BirthdayService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')

# Add context processor for git commit
@app.context_processor
def inject_git_commit():
    return {
        'git_commit_short': os.getenv('GIT_COMMIT_SHORT', 'unknown')
    }

# Track service start time
START_TIME = time.time()

# Global state
birthday_service = None
scheduler = None
birthday_cache = {}
cache_lock = Lock()

def initialize_service():
    """Initialize the birthday service"""
    global birthday_service
    birthday_service = BirthdayService(
        ics_url=os.getenv('ICS_URL'),
        webhook_url=os.getenv('WEBHOOK_URL'),
        ldap_server=os.getenv('LDAP_SERVER'),
        search_base=os.getenv('SEARCH_BASE'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )

def update_birthday_cache():
    """Update the cached birthday data for the configured look-ahead period"""
    global birthday_cache
    
    if not birthday_service:
        logger.error("Birthday service not initialized")
        return
    
    try:
        logger.info("Updating birthday cache...")
        
        # Get look-ahead days from environment variable (default 30)
        look_ahead_days = int(os.getenv('BIRTHDAY_LOOK_AHEAD_DAYS', '30'))
        
        # Get events for the configured period
        today = datetime.now().date()
        end_date = today + timedelta(days=look_ahead_days)
        
        new_cache = {}
        
        current_date = today
        while current_date <= end_date:
            events = birthday_service.get_birthday_events_for_date(current_date)
            if events:
                new_cache[current_date.isoformat()] = events
            current_date += timedelta(days=1)
        
        with cache_lock:
            birthday_cache = new_cache
            
        logger.info(f"Birthday cache updated with {len(new_cache)} days of events (look-ahead: {look_ahead_days} days)")
        
    except Exception as e:
        logger.error(f"Error updating birthday cache: {e}")

def send_daily_birthdays():
    """Send birthday messages for today"""
    if not birthday_service:
        logger.error("Birthday service not initialized")
        return
    
    try:
        logger.info("Checking for today's birthdays...")
        today = datetime.now().date()
        
        # Update cache first to ensure we have the latest messages
        update_birthday_cache()
        
        # Send birthday messages
        birthday_service.send_birthday_messages(today)
        
    except Exception as e:
        logger.error(f"Error sending daily birthdays: {e}")

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/birthdays')
def api_birthdays():
    """API endpoint to get upcoming birthdays"""
    with cache_lock:
        # Convert dates to include day of week and format for display
        formatted_data = {}
        for date_str, events in birthday_cache.items():
            date_obj = datetime.fromisoformat(date_str).date()
            formatted_data[date_str] = {
                'date': date_str,
                'day_of_week': date_obj.strftime('%A'),
                'events': events
            }
    
    return jsonify(formatted_data)

@app.route('/api/status')
def api_status():
    """API endpoint to get service status"""
    slack_enabled = os.getenv('SLACK_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
    look_ahead_days = int(os.getenv('BIRTHDAY_LOOK_AHEAD_DAYS', '30'))
    
    status_data = {
        'status': 'running',
        'service_initialized': birthday_service is not None,
        'cache_size': len(birthday_cache),
        'last_updated': datetime.utcnow().isoformat() + 'Z',
        'slack_notifications_enabled': slack_enabled,
        'look_ahead_days': look_ahead_days
    }
    
    if birthday_service:
        service_status = birthday_service.get_service_status()
        status_data.update(service_status)
    
    return jsonify(status_data)

@app.route('/health')
def health():
    """Standardized health check endpoint."""
    health_status = {
        'status': 'healthy',
        'service': os.getenv('SERVICE_NAME', 'birthdays-to-slack'),
        'version': os.getenv('VERSION', '1.0.0'),
        'commit': os.getenv('GIT_COMMIT_SHORT', 'unknown'),
        'build_date': os.getenv('BUILD_DATE', 'unknown'),
        'uptime': int(time.time() - START_TIME),
        'environment': os.getenv('ENVIRONMENT', 'production'),
        'checks': {}
    }
    
    # Check if scheduler is running
    try:
        if scheduler and scheduler.running:
            health_status['checks']['scheduler'] = 'healthy'
            health_status['checks']['scheduled_jobs'] = len(scheduler.get_jobs())
        else:
            health_status['checks']['scheduler'] = 'unhealthy: not running'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['scheduler'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check if birthday service is initialized
    if birthday_service is not None:
        health_status['checks']['birthday_service'] = 'healthy'
        health_status['checks']['cache_size'] = len(birthday_cache)
    else:
        health_status['checks']['birthday_service'] = 'unhealthy: not initialized'
        health_status['status'] = 'unhealthy'
    
    # Check LDAP connectivity if service is initialized
    if birthday_service:
        try:
            service_status = birthday_service.get_service_status()
            health_status['checks']['ldap'] = 'healthy' if service_status.get('ldap_connected', False) else 'unhealthy: not connected'
            health_status['checks']['ics_url'] = 'configured' if service_status.get('ics_configured', False) else 'not configured'
            health_status['checks']['webhook_url'] = 'configured' if service_status.get('webhook_configured', False) else 'not configured'
        except Exception as e:
            health_status['checks']['services'] = f'unhealthy: {str(e)}'
    
    # Return pretty-printed JSON
    response = jsonify(health_status)
    response.headers['Content-Type'] = 'application/json'
    return response, 200 if health_status['status'] == 'healthy' else 503

@app.route('/api/regenerate-message', methods=['POST'])
def api_regenerate_message():
    """API endpoint to regenerate a birthday message"""
    if not birthday_service:
        return jsonify({'error': 'Service not initialized'}), 503
    
    data = request.get_json()
    if not data or 'name' not in data or 'date' not in data:
        return jsonify({'error': 'Missing name or date'}), 400
    
    try:
        birthday_date = datetime.fromisoformat(data['date']).date()
        message_data = birthday_service.regenerate_message(data['name'], birthday_date)
        
        if message_data:
            # Update cache
            update_birthday_cache()
            return jsonify({
                'success': True,
                'message_data': message_data
            })
        else:
            return jsonify({'error': 'Failed to regenerate message'}), 500
            
    except Exception as e:
        logger.error(f"Error regenerating message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prompt-template', methods=['GET', 'POST'])
def api_prompt_template():
    """API endpoint to get or update the prompt template"""
    if not birthday_service:
        return jsonify({'error': 'Service not initialized'}), 503
    
    if request.method == 'GET':
        template = birthday_service.get_prompt_template()
        return jsonify({
            'template': template,
            'has_openai': template is not None
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'template' not in data:
            return jsonify({'error': 'Missing template'}), 400
        
        description = data.get('description', '')
        success = birthday_service.update_prompt_template(data['template'], description)
        if success:
            # Clear cache to regenerate messages with new template
            update_birthday_cache()
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to update template'}), 500

@app.route('/api/prompt-history')
def api_prompt_history():
    """API endpoint to get prompt template history"""
    if not birthday_service:
        return jsonify({'error': 'Service not initialized'}), 503
    
    try:
        history = birthday_service.get_prompt_history()
        return jsonify({'history': history})
    except Exception as e:
        logger.error(f"Failed to get prompt history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/activate-prompt', methods=['POST'])
def api_activate_prompt():
    """API endpoint to activate a prompt from history"""
    if not birthday_service:
        return jsonify({'error': 'Service not initialized'}), 503
    
    data = request.get_json()
    if not data or 'prompt_id' not in data:
        return jsonify({'error': 'Missing prompt_id'}), 400
    
    try:
        success = birthday_service.activate_prompt_from_history(data['prompt_id'])
        if success:
            # Update cache to regenerate messages with new prompt
            update_birthday_cache()
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Prompt not found'}), 404
    except Exception as e:
        logger.error(f"Failed to activate prompt: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear-sent-tracking', methods=['POST'])
def api_clear_sent_tracking():
    """API endpoint to clear sent message tracking for a specific person/date"""
    if not birthday_service:
        return jsonify({'error': 'Service not initialized'}), 503
    
    data = request.get_json()
    if not data or 'name' not in data or 'date' not in data:
        return jsonify({'error': 'Missing name or date'}), 400
    
    try:
        birthday_date = datetime.fromisoformat(data['date']).date()
        if birthday_service.message_generator:
            birthday_service.message_generator.clear_sent_tracking(data['name'], birthday_date)
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Message generator not initialized'}), 503
    except Exception as e:
        logger.error(f"Failed to clear sent tracking: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-message', methods=['POST'])
def api_update_message():
    """API endpoint to update a birthday message"""
    if not birthday_service:
        return jsonify({'error': 'Service not initialized'}), 503
    
    data = request.get_json()
    if not data or 'name' not in data or 'date' not in data or 'message' not in data:
        return jsonify({'error': 'Missing name, date, or message'}), 400
    
    try:
        birthday_date = datetime.fromisoformat(data['date']).date()
        new_message = data['message'].strip()
        
        if not new_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Update the message
        success = birthday_service.update_message(data['name'], birthday_date, new_message)
        
        if success:
            # Update cache to reflect the change
            update_birthday_cache()
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to update message'}), 500
            
    except Exception as e:
        logger.error(f"Failed to update message: {e}")
        return jsonify({'error': str(e)}), 500

def start_scheduler():
    """Start the background scheduler"""
    global scheduler
    
    scheduler = BackgroundScheduler(daemon=True)
    
    # Schedule daily birthday check at 7 AM Central Time
    central_tz = pytz.timezone('America/Chicago')
    scheduler.add_job(
        func=send_daily_birthdays,
        trigger=CronTrigger(hour=7, minute=0, timezone=central_tz),
        id='daily_birthday_check',
        name='Daily Birthday Check',
        replace_existing=True
    )
    
    # Schedule cache updates every 6 hours
    scheduler.add_job(
        func=update_birthday_cache,
        trigger=CronTrigger(hour='*/6', minute=0),
        id='cache_update',
        name='Birthday Cache Update',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler started successfully")

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
    
    logger.info(f"Starting birthday service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)