// Theme management
class ThemeManager {
    constructor() {
        this.theme = this.getStoredTheme() || this.getPreferredTheme();
        this.initTheme();
        this.bindEvents();
    }

    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    setStoredTheme(theme) {
        localStorage.setItem('theme', theme);
    }

    getPreferredTheme() {
        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    setTheme(theme) {
        if (theme === 'auto') {
            document.documentElement.setAttribute('data-theme', this.getPreferredTheme());
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
    }

    initTheme() {
        this.setTheme(this.theme);
        document.documentElement.setAttribute('data-theme', this.theme);
    }

    toggleTheme() {
        const themes = ['light', 'dark', 'auto'];
        const currentIndex = themes.indexOf(this.theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        this.theme = themes[nextIndex];
        
        this.setStoredTheme(this.theme);
        this.setTheme(this.theme);
    }

    bindEvents() {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Listen for system theme changes when in auto mode
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
            if (this.theme === 'auto') {
                this.setTheme(this.theme);
            }
        });
    }
}

// Birthday data management
class BirthdayManager {
    constructor() {
        this.lastUpdated = null;
        this.birthdayData = {};
    }

    async loadServiceStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            this.updateServiceStatusDisplay(data);
            
        } catch (error) {
            console.error('Error loading service status:', error);
            this.updateServiceStatusDisplay({ status: 'error' });
        }
    }

    updateServiceStatusDisplay(data) {
        const statusElement = document.getElementById('service-status');
        const slackStatusElement = document.getElementById('slack-status');
        const lastUpdatedElement = document.getElementById('last-updated');
        
        if (statusElement) {
            let statusHtml = '';
            let statusClass = 'text-secondary';
            
            if (data.status === 'running') {
                statusHtml = '<i class="bi bi-circle-fill text-success"></i> <span>Running</span>';
                statusClass = 'text-success';
            } else if (data.status === 'error') {
                statusHtml = '<i class="bi bi-circle-fill text-danger"></i> <span>Error</span>';
                statusClass = 'text-danger';
            } else {
                statusHtml = '<i class="bi bi-circle-fill text-warning"></i> <span>Unknown</span>';
                statusClass = 'text-warning';
            }
            
            statusElement.innerHTML = statusHtml;
            statusElement.className = `status-value ${statusClass}`;
        }
        
        if (slackStatusElement && data.slack_notifications_enabled !== undefined) {
            if (data.slack_notifications_enabled) {
                slackStatusElement.innerHTML = '<i class="bi bi-bell-fill text-success"></i> <span>Enabled</span>';
                slackStatusElement.className = 'status-value text-success';
            } else {
                slackStatusElement.innerHTML = '<i class="bi bi-bell-slash-fill text-warning"></i> <span>Disabled</span>';
                slackStatusElement.className = 'status-value text-warning';
            }
        }
        
        if (lastUpdatedElement && data.last_updated) {
            const lastUpdated = new Date(data.last_updated);
            const now = new Date();
            const diffMinutes = Math.floor((now - lastUpdated) / 1000 / 60);
            
            let timeText = '';
            if (diffMinutes < 1) {
                timeText = 'Just now';
            } else if (diffMinutes < 60) {
                timeText = `${diffMinutes} minutes ago`;
            } else {
                const diffHours = Math.floor(diffMinutes / 60);
                timeText = `${diffHours} hours ago`;
            }
            
            lastUpdatedElement.textContent = `Last updated: ${timeText}`;
        }
    }

    async loadBirthdayData() {
        try {
            const response = await fetch('/api/birthdays');
            const data = await response.json();
            
            this.birthdayData = data;
            this.renderBirthdaySchedule();
            this.updateStatistics();
            
        } catch (error) {
            console.error('Error loading birthday data:', error);
            this.showError();
        }
    }

    renderBirthdaySchedule() {
        const container = document.getElementById('birthday-schedule');
        const loadingSpinner = document.getElementById('loading-spinner');
        const noBirthdaysMessage = document.getElementById('no-birthdays');
        
        if (!container) return;
        
        // Hide loading spinner
        if (loadingSpinner) {
            loadingSpinner.classList.add('d-none');
        }
        
        // Check if we have any data
        const hasData = Object.keys(this.birthdayData).length > 0;
        
        if (!hasData) {
            container.classList.add('d-none');
            if (noBirthdaysMessage) {
                noBirthdaysMessage.classList.remove('d-none');
            }
            return;
        }
        
        // Hide no-birthdays message and show container
        if (noBirthdaysMessage) {
            noBirthdaysMessage.classList.add('d-none');
        }
        container.classList.remove('d-none');
        
        // Sort dates and render
        const sortedDates = Object.keys(this.birthdayData).sort();
        const today = new Date().toISOString().split('T')[0];
        
        let html = '';
        
        for (const dateStr of sortedDates) {
            const dayData = this.birthdayData[dateStr];
            const isToday = dateStr === today;
            
            if (dayData.events && dayData.events.length > 0) {
                html += this.renderBirthdayDay(dayData, isToday);
            }
        }
        
        container.innerHTML = html;
    }

    renderBirthdayDay(dayData, isToday = false) {
        const date = new Date(dayData.date + 'T00:00:00');
        const formattedDate = date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        const todayClass = isToday ? 'today' : '';
        
        let eventsHtml = '';
        for (const event of dayData.events) {
            eventsHtml += this.renderBirthdayEvent(event);
        }
        
        return `
            <div class="birthday-day ${todayClass}">
                <div class="birthday-day-header">
                    <div class="birthday-day-date">${formattedDate}</div>
                    <div class="birthday-day-name">${dayData.day_of_week}</div>
                </div>
                <div class="birthday-events">
                    ${eventsHtml}
                </div>
            </div>
        `;
    }

    renderBirthdayEvent(event) {
        const statusClass = event.ldap_valid ? 'status-valid' : 'status-invalid';
        const statusIcon = event.ldap_valid ? 'bi-check-circle-fill' : 'bi-x-circle-fill';
        const statusText = event.ldap_valid ? 'Will send notification' : 'Skipped (not in LDAP)';
        
        return `
            <div class="birthday-event">
                <div class="birthday-event-name">${this.escapeHtml(event.name)}</div>
                <div class="birthday-event-details">
                    <strong>Event:</strong> ${this.escapeHtml(event.summary)}
                </div>
                <div class="birthday-event-status ${statusClass}">
                    <i class="bi ${statusIcon}"></i>
                    ${statusText}
                </div>
            </div>
        `;
    }

    updateStatistics() {
        let totalEvents = 0;
        let validEvents = 0;
        let skippedEvents = 0;
        
        for (const dateStr of Object.keys(this.birthdayData)) {
            const dayData = this.birthdayData[dateStr];
            if (dayData.events) {
                for (const event of dayData.events) {
                    totalEvents++;
                    if (event.ldap_valid) {
                        validEvents++;
                    } else {
                        skippedEvents++;
                    }
                }
            }
        }
        
        const totalElement = document.getElementById('total-events');
        const validElement = document.getElementById('valid-events');
        const skippedElement = document.getElementById('skipped-events');
        
        if (totalElement) totalElement.textContent = totalEvents;
        if (validElement) validElement.textContent = validEvents;
        if (skippedElement) skippedElement.textContent = skippedEvents;
    }

    showError() {
        const container = document.getElementById('birthday-schedule');
        const loadingSpinner = document.getElementById('loading-spinner');
        
        if (loadingSpinner) {
            loadingSpinner.classList.add('d-none');
        }
        
        if (container) {
            container.innerHTML = `
                <div class="text-center py-4 text-danger">
                    <i class="bi bi-exclamation-triangle display-1"></i>
                    <h5 class="mt-2">Error Loading Data</h5>
                    <p>Unable to load birthday data. Please try refreshing the page.</p>
                </div>
            `;
            container.classList.remove('d-none');
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global functions for template usage
function loadBirthdayData() {
    if (window.birthdayManager) {
        window.birthdayManager.loadBirthdayData();
    }
}

function loadServiceStatus() {
    if (window.birthdayManager) {
        window.birthdayManager.loadServiceStatus();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme manager
    window.themeManager = new ThemeManager();
    
    // Initialize birthday manager
    window.birthdayManager = new BirthdayManager();
    
    console.log('Birthday Bot Dashboard initialized');
});