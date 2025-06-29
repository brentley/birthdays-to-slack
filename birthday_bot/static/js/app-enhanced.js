// Enhanced app.js with OpenAI message support

// Note: This file expects app.js to be loaded first in the HTML

// VisiQuate standard time formatting function (if not already defined)
if (typeof formatTime === 'undefined') {
    window.formatTime = (timestamp) => {
        const date = new Date(timestamp);
        return date.toLocaleString(undefined, {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZoneName: 'short'
        });
    };
}

// Extended BirthdayManager for OpenAI features
class EnhancedBirthdayManager extends BirthdayManager {
    constructor() {
        super();
        this.autoRefreshInterval = null;
        this.lastUpdateTime = Date.now();
        this.currentBirthdayData = {};
        this.editStates = new Map(); // Track which messages are being edited
    }
    
    // Start auto-refresh of birthday data
    startAutoRefresh(intervalMinutes = 60) {
        // Clear any existing interval
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
        
        // Set up new interval (default 1 hour)
        this.autoRefreshInterval = setInterval(() => {
            this.refreshBirthdayData();
        }, intervalMinutes * 60 * 1000);
        
        console.log(`Auto-refresh enabled: updating every ${intervalMinutes} minutes`);
    }
    
    // Stop auto-refresh
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            console.log('Auto-refresh disabled');
        }
    }
    
    // Refresh birthday data without page reload
    async refreshBirthdayData() {
        try {
            console.log('Refreshing birthday data...');
            
            // Fetch latest data
            const response = await fetch('/api/birthdays');
            if (!response.ok) throw new Error('Failed to fetch birthdays');
            
            const newData = await response.json();
            
            // Update the display with smart updates
            this.smartUpdateBirthdays(newData);
            
            // Update last refresh time
            this.lastUpdateTime = Date.now();
            this.updateLastRefreshDisplay();
            
            // Update statistics without disrupting the UI
            this.updateStatistics();
            
        } catch (error) {
            console.error('Error refreshing birthday data:', error);
            this.showNotification('Failed to refresh birthday data', 'error');
        }
    }
    
    // Smart update that only changes what's different
    smartUpdateBirthdays(newData) {
        const birthdaySchedule = document.getElementById('birthday-schedule');
        if (!birthdaySchedule) {
            // Fallback to full render if container not found
            this.birthdayData = newData;
            this.renderBirthdaySchedule();
            return;
        }
        
        // Store edit states before update
        this.preserveEditStates();
        
        // Compare and update only changed elements
        const oldDates = Object.keys(this.currentBirthdayData);
        const newDates = Object.keys(newData);
        const allDates = new Set([...oldDates, ...newDates]);
        
        allDates.forEach(dateStr => {
            const oldDateData = this.currentBirthdayData[dateStr];
            const newDateData = newData[dateStr];
            
            if (!oldDateData && newDateData) {
                // New date added
                this.addDateSection(dateStr, newDateData);
            } else if (oldDateData && !newDateData) {
                // Date removed
                this.removeDateSection(dateStr);
            } else if (oldDateData && newDateData) {
                // Date exists, check for changes
                this.updateDateSection(dateStr, oldDateData, newDateData);
            }
        });
        
        // Update stored data
        this.currentBirthdayData = JSON.parse(JSON.stringify(newData));
        this.birthdayData = newData;
        
        // Restore edit states
        this.restoreEditStates();
    }
    
    // Preserve the state of any messages being edited
    preserveEditStates() {
        this.editStates.clear();
        const editContainers = document.querySelectorAll('.message-edit-container');
        editContainers.forEach(container => {
            if (container.style.display !== 'none') {
                const textarea = container.querySelector('textarea');
                const key = container.id;
                this.editStates.set(key, {
                    visible: true,
                    value: textarea ? textarea.value : ''
                });
            }
        });
    }
    
    // Restore edit states after update
    restoreEditStates() {
        this.editStates.forEach((state, key) => {
            const editContainer = document.getElementById(key);
            const messageContainer = key.replace('edit-', 'message-');
            const messageDiv = document.getElementById(messageContainer);
            
            if (editContainer && state.visible) {
                editContainer.style.display = 'block';
                if (messageDiv) messageDiv.style.display = 'none';
                
                const textarea = editContainer.querySelector('textarea');
                if (textarea) {
                    textarea.value = state.value;
                }
            }
        });
    }
    
    // Add a new date section
    addDateSection(dateStr, dateData) {
        const container = document.getElementById('birthday-schedule');
        if (!container) return;
        
        const isToday = dateStr === new Date().toISOString().split('T')[0];
        const newSection = document.createElement('div');
        newSection.innerHTML = this.renderBirthdayDayEnhanced(dateData, isToday);
        
        // Find correct position to insert (maintain date order)
        const existingSections = container.querySelectorAll('.birthday-day');
        let inserted = false;
        
        existingSections.forEach(section => {
            if (!inserted) {
                const sectionDate = section.getAttribute('data-date');
                if (sectionDate && sectionDate > dateStr) {
                    container.insertBefore(newSection.firstChild, section);
                    inserted = true;
                }
            }
        });
        
        if (!inserted) {
            container.appendChild(newSection.firstChild);
        }
        
        // Highlight new section
        this.highlightElement(newSection.firstChild);
    }
    
    // Remove a date section
    removeDateSection(dateStr) {
        const sections = document.querySelectorAll('.birthday-day');
        sections.forEach(section => {
            if (section.getAttribute('data-date') === dateStr) {
                section.style.transition = 'opacity 0.3s';
                section.style.opacity = '0';
                setTimeout(() => section.remove(), 300);
            }
        });
    }
    
    // Update existing date section
    updateDateSection(dateStr, oldData, newData) {
        // Deep comparison of events
        const eventsChanged = JSON.stringify(oldData.events) !== JSON.stringify(newData.events);
        
        if (eventsChanged) {
            const section = document.querySelector(`.birthday-day[data-date="${dateStr}"]`);
            if (section) {
                const eventsContainer = section.querySelector('.birthday-events');
                if (eventsContainer) {
                    // Update individual events
                    this.updateEvents(eventsContainer, oldData.events || [], newData.events || []);
                }
            }
        }
    }
    
    // Update individual events within a date
    updateEvents(container, oldEvents, newEvents) {
        const oldEventMap = new Map(oldEvents.map(e => [e.name, e]));
        const newEventMap = new Map(newEvents.map(e => [e.name, e]));
        
        // Remove events that no longer exist
        oldEvents.forEach(event => {
            if (!newEventMap.has(event.name)) {
                const eventEl = container.querySelector(`[data-name="${CSS.escape(event.name)}"]`);
                if (eventEl) {
                    eventEl.style.transition = 'opacity 0.3s';
                    eventEl.style.opacity = '0';
                    setTimeout(() => eventEl.remove(), 300);
                }
            }
        });
        
        // Add or update events
        newEvents.forEach((event, index) => {
            const oldEvent = oldEventMap.get(event.name);
            const eventEl = container.querySelector(`[data-name="${CSS.escape(event.name)}"]`);
            
            if (!oldEvent) {
                // New event
                const newEventEl = document.createElement('div');
                newEventEl.innerHTML = this.renderBirthdayEvent(event);
                container.appendChild(newEventEl.firstChild);
                this.highlightElement(newEventEl.firstChild);
            } else if (JSON.stringify(oldEvent) !== JSON.stringify(event)) {
                // Event changed
                if (eventEl) {
                    // Preserve edit state if editing
                    const editKey = `edit-${event.name.replace(/\s+/g, '-')}-${event.date}`;
                    const isEditing = this.editStates.has(editKey);
                    
                    if (!isEditing) {
                        const newEventEl = document.createElement('div');
                        newEventEl.innerHTML = this.renderBirthdayEvent(event);
                        eventEl.replaceWith(newEventEl.firstChild);
                        this.highlightElement(newEventEl.firstChild);
                    }
                }
            }
        });
    }
    
    // Highlight element to show it was updated
    highlightElement(element) {
        if (!element) return;
        
        element.style.transition = 'background-color 0.5s';
        element.style.backgroundColor = 'rgba(17, 109, 248, 0.1)';
        
        setTimeout(() => {
            element.style.backgroundColor = '';
        }, 2000);
    }
    
    // Enhanced render method with data-date attribute
    renderBirthdayDayEnhanced(dayData, isToday = false) {
        const formattedDate = formatDate(dayData.date);
        
        const todayClass = isToday ? 'today' : '';
        
        let eventsHtml = '';
        for (const event of dayData.events) {
            eventsHtml += this.renderBirthdayEvent(event);
        }
        
        return `
            <div class="birthday-day ${todayClass}" data-date="${dayData.date}">
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
    
    // Update last refresh time display
    updateLastRefreshDisplay() {
        const refreshDisplay = document.getElementById('last-refresh-time');
        if (refreshDisplay) {
            const now = new Date(this.lastUpdateTime);
            refreshDisplay.textContent = `Last updated: ${formatTime(now)}`;
        }
    }
    
    // Show notification
    showNotification(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }
    
    // Display birthdays data
    displayBirthdays(data) {
        // Store the initial data
        this.currentBirthdayData = JSON.parse(JSON.stringify(data));
        this.birthdayData = data;
        
        const birthdayList = document.getElementById('birthday-list');
        if (!birthdayList) return;
        
        // Clear existing content
        birthdayList.innerHTML = '';
        
        // Sort dates
        const sortedDates = Object.keys(data).sort();
        
        if (sortedDates.length === 0) {
            birthdayList.innerHTML = '<div class="alert alert-info">No upcoming birthdays found.</div>';
            return;
        }
        
        // Render each date's birthdays
        sortedDates.forEach(dateStr => {
            const dateData = data[dateStr];
            const dateCard = document.createElement('div');
            dateCard.className = 'birthday-date-card mb-3';
            
            const dateHeader = document.createElement('h5');
            dateHeader.className = 'date-header';
            dateHeader.innerHTML = `
                <i class="bi bi-calendar-event"></i>
                ${new Date(dateStr).toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
            `;
            dateCard.appendChild(dateHeader);
            
            const eventsList = document.createElement('div');
            eventsList.className = 'events-list';
            
            dateData.events.forEach(event => {
                const eventDiv = document.createElement('div');
                eventDiv.className = 'birthday-event';
                eventDiv.innerHTML = this.renderBirthdayEvent(event);
                eventsList.appendChild(eventDiv);
            });
            
            dateCard.appendChild(eventsList);
            birthdayList.appendChild(dateCard);
        });
    }
    updateServiceStatusDisplay(data) {
        super.updateServiceStatusDisplay(data);
        
        const openaiStatusElement = document.getElementById('openai-status');
        const editPromptBtn = document.getElementById('editPromptBtn');
        const historyPromptBtn = document.getElementById('historyPromptBtn');
        
        if (openaiStatusElement && data.openai_configured !== undefined) {
            if (data.openai_configured) {
                openaiStatusElement.innerHTML = '<i class="bi bi-robot text-success"></i> <span>Enabled</span>';
                openaiStatusElement.className = 'status-value text-success';
                if (editPromptBtn) editPromptBtn.style.display = 'inline-block';
                if (historyPromptBtn) historyPromptBtn.style.display = 'inline-block';
            } else {
                openaiStatusElement.innerHTML = '<i class="bi bi-dash-circle text-muted"></i> <span>Disabled</span>';
                openaiStatusElement.className = 'status-value text-muted';
                if (editPromptBtn) editPromptBtn.style.display = 'none';
                if (historyPromptBtn) historyPromptBtn.style.display = 'none';
            }
        }
    }

    renderBirthdayEvent(event) {
        const statusClass = event.ldap_valid ? 'status-valid' : 'status-invalid';
        const statusIcon = event.ldap_valid ? 'bi-check-circle-fill' : 'bi-x-circle-fill';
        const statusText = event.ldap_valid ? 'Will send notification' : 'Skipped (not in LDAP)';
        
        let messageHtml = '';
        if (event.message && event.ldap_valid) {
            const messageData = event.message_data || {};
            const isGenerated = messageData.message && !messageData.fallback;
            const historicalFact = messageData.historical_fact;
            
            messageHtml = `
                <div class="birthday-event-message mt-2">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <strong>Message:</strong>
                            <div class="message-preview" id="message-${this.escapeHtml(event.name).replace(/\s+/g, '-')}-${event.date}">${this.escapeHtml(event.message)}</div>
                            <div class="message-edit-container" id="edit-${this.escapeHtml(event.name).replace(/\s+/g, '-')}-${event.date}" style="display: none;">
                                <textarea class="form-control message-edit-textarea" rows="3">${this.escapeHtml(event.message)}</textarea>
                                <div class="mt-2">
                                    <button class="btn btn-sm btn-primary" onclick="saveEditedMessage('${this.escapeHtml(event.name)}', '${event.date}')">
                                        <i class="bi bi-check"></i> Save
                                    </button>
                                    <button class="btn btn-sm btn-secondary" onclick="cancelEditMessage('${this.escapeHtml(event.name)}', '${event.date}')">
                                        <i class="bi bi-x"></i> Cancel
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div class="btn-group ms-2">
                            <button class="btn btn-sm btn-outline-primary" 
                                    onclick="editMessage('${this.escapeHtml(event.name)}', '${event.date}')"
                                    title="Edit message">
                                <i class="bi bi-pencil"></i>
                            </button>
                            ${isGenerated ? `
                                <button class="btn btn-sm btn-outline-secondary" 
                                        onclick="regenerateMessage('${this.escapeHtml(event.name)}', '${event.date}')"
                                        title="Regenerate message">
                                    <i class="bi bi-arrow-clockwise"></i>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        }
        
        return `
            <div class="birthday-event" data-name="${this.escapeHtml(event.name)}" data-date="${event.date}">
                <div class="birthday-event-name">${this.escapeHtml(event.name)}</div>
                <div class="birthday-event-details">
                    <strong>Event:</strong> ${this.escapeHtml(event.summary)}
                </div>
                <div class="birthday-event-status ${statusClass}">
                    <i class="bi ${statusIcon}"></i>
                    ${statusText}
                </div>
                ${messageHtml}
            </div>
        `;
    }
}

// Prompt template management
async function showPromptModal() {
    try {
        const response = await fetch('/api/prompt-template');
        const data = await response.json();
        
        if (data.template) {
            document.getElementById('promptTemplate').value = data.template;
            const modal = new bootstrap.Modal(document.getElementById('promptModal'));
            modal.show();
        } else {
            alert('OpenAI is not configured');
        }
    } catch (error) {
        console.error('Error loading prompt template:', error);
        alert('Failed to load prompt template');
    }
}

async function savePromptTemplate() {
    const template = document.getElementById('promptTemplate').value;
    
    if (!template.includes('{employee_name}') || !template.includes('{birthday_date}')) {
        alert('Template must contain {employee_name} and {birthday_date} placeholders');
        return;
    }
    
    try {
        const response = await fetch('/api/prompt-template', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                template,
                description: document.getElementById('promptDescription')?.value || ''
            })
        });
        
        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('promptModal'));
            modal.hide();
            
            // Reload birthday data to regenerate messages
            loadBirthdayData();
            
            // Show success message
            showNotification('Prompt template updated successfully', 'success');
        } else {
            const error = await response.json();
            alert('Failed to save template: ' + (error.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error saving prompt template:', error);
        alert('Failed to save prompt template');
    }
}

// Message regeneration
async function regenerateMessage(name, date) {
    if (!confirm(`Regenerate message for ${name}?`)) {
        return;
    }
    
    // Show loading state
    const eventElement = document.querySelector(`[data-name="${name}"][data-date="${date}"]`);
    if (eventElement) {
        const messageDiv = eventElement.querySelector('.birthday-event-message');
        if (messageDiv) {
            messageDiv.innerHTML = '<div class="text-center"><div class="spinner-border spinner-border-sm"></div> Regenerating...</div>';
        }
    }
    
    try {
        // First, clear the sent tracking to prevent duplicate message issues
        await fetch('/api/clear-sent-tracking', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, date })
        });
        
        // Then regenerate the message
        const response = await fetch('/api/regenerate-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, date })
        });
        
        if (response.ok) {
            // Reload birthday data to show new message
            loadBirthdayData();
            showNotification(`Message regenerated for ${name}`, 'success');
        } else {
            const error = await response.json();
            alert('Failed to regenerate message: ' + (error.error || 'Unknown error'));
            loadBirthdayData(); // Reload to restore original state
        }
    } catch (error) {
        console.error('Error regenerating message:', error);
        alert('Failed to regenerate message');
        loadBirthdayData(); // Reload to restore original state
    }
}

// Notification helper
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Prompt history management
async function showPromptHistory() {
    try {
        const response = await fetch('/api/prompt-history');
        const data = await response.json();
        
        if (data.history) {
            const historyContainer = document.getElementById('promptHistoryList');
            historyContainer.innerHTML = '';
            
            data.history.forEach(entry => {
                const div = document.createElement('div');
                div.className = `prompt-history-item ${entry.active ? 'active' : ''}`;
                div.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6>${entry.description || 'No description'}</h6>
                            <small class="text-muted">${entry.created_at === 'current' ? 'Current' : formatTime(entry.created_at)}</small>
                            <pre class="prompt-preview mt-2">${entry.template.substring(0, 200)}${entry.template.length > 200 ? '...' : ''}</pre>
                        </div>
                        <div class="btn-group">
                            ${!entry.active ? `<button class="btn btn-sm btn-outline-primary" onclick="activatePrompt('${entry.id}')">Activate</button>` : ''}
                            <button class="btn btn-sm btn-outline-secondary" onclick="previewPrompt('${entry.id}')">Preview</button>
                        </div>
                    </div>
                `;
                historyContainer.appendChild(div);
            });
            
            const modal = new bootstrap.Modal(document.getElementById('promptHistoryModal'));
            modal.show();
        } else {
            alert('OpenAI is not configured');
        }
    } catch (error) {
        console.error('Error loading prompt history:', error);
        alert('Failed to load prompt history');
    }
}

async function activatePrompt(promptId) {
    if (!confirm('Are you sure you want to activate this prompt? This will regenerate all birthday messages.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/activate-prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt_id: promptId })
        });
        
        if (response.ok) {
            showNotification('Prompt activated successfully!', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('promptHistoryModal'));
            modal.hide();
            // Refresh data
            loadBirthdayData();
        } else {
            const error = await response.json();
            alert('Error activating prompt: ' + error.error);
        }
    } catch (error) {
        console.error('Error activating prompt:', error);
        alert('Failed to activate prompt');
    }
}

// Edit message functions
function editMessage(name, date) {
    const nameId = name.replace(/\s+/g, '-');
    const messageDiv = document.getElementById(`message-${nameId}-${date}`);
    const editDiv = document.getElementById(`edit-${nameId}-${date}`);
    
    if (messageDiv && editDiv) {
        messageDiv.style.display = 'none';
        editDiv.style.display = 'block';
        
        // Focus on textarea
        const textarea = editDiv.querySelector('textarea');
        if (textarea) {
            textarea.focus();
            textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        }
    }
}

function cancelEditMessage(name, date) {
    const nameId = name.replace(/\s+/g, '-');
    const messageDiv = document.getElementById(`message-${nameId}-${date}`);
    const editDiv = document.getElementById(`edit-${nameId}-${date}`);
    
    if (messageDiv && editDiv) {
        messageDiv.style.display = 'block';
        editDiv.style.display = 'none';
        
        // Reset textarea to original value
        const textarea = editDiv.querySelector('textarea');
        if (textarea) {
            textarea.value = messageDiv.textContent;
        }
    }
}

async function saveEditedMessage(name, date) {
    const nameId = name.replace(/\s+/g, '-');
    const editDiv = document.getElementById(`edit-${nameId}-${date}`);
    const textarea = editDiv.querySelector('textarea');
    
    if (!textarea) return;
    
    const newMessage = textarea.value.trim();
    if (!newMessage) {
        alert('Message cannot be empty');
        return;
    }
    
    // Show loading state
    const saveBtn = editDiv.querySelector('.btn-primary');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';
    saveBtn.disabled = true;
    
    try {
        const response = await fetch('/api/update-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                date: date,
                message: newMessage
            })
        });
        
        if (response.ok) {
            // Update the display
            const messageDiv = document.getElementById(`message-${nameId}-${date}`);
            if (messageDiv) {
                messageDiv.textContent = newMessage;
            }
            
            // Hide edit mode
            cancelEditMessage(name, date);
            
            // Show success notification
            showNotification('Message updated successfully', 'success');
        } else {
            const error = await response.json();
            alert('Failed to update message: ' + (error.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error updating message:', error);
        alert('Failed to update message');
    } finally {
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    }
}

// Override the global birthday manager with enhanced version
document.addEventListener('DOMContentLoaded', function() {
    // Replace with enhanced manager
    window.birthdayManager = new EnhancedBirthdayManager();
    
    // Start auto-refresh (1 hour intervals)
    window.birthdayManager.startAutoRefresh(60);
    
    // Add manual refresh button functionality
    const refreshButton = document.getElementById('refresh-birthdays-btn');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => {
            window.birthdayManager.refreshBirthdayData();
        });
    }
    
    // Add refresh controls to the page if not present
    const controlsContainer = document.querySelector('.controls-container') || document.querySelector('.card-body');
    if (controlsContainer && !document.getElementById('refresh-controls')) {
        const refreshControls = document.createElement('div');
        refreshControls.id = 'refresh-controls';
        refreshControls.className = 'mt-3 d-flex align-items-center gap-3';
        refreshControls.innerHTML = `
            <button id="refresh-birthdays-btn" class="btn btn-sm btn-outline-primary">
                <i class="bi bi-arrow-clockwise"></i> Refresh Now
            </button>
            <small id="last-refresh-time" class="text-muted">Loading...</small>
            <small class="text-muted">(Auto-refreshes hourly)</small>
        `;
        controlsContainer.appendChild(refreshControls);
        
        // Add event listener to the newly created button
        document.getElementById('refresh-birthdays-btn').addEventListener('click', () => {
            window.birthdayManager.refreshBirthdayData();
        });
    }
    
    // Update the initial refresh time
    window.birthdayManager.updateLastRefreshDisplay();
    
    console.log('Birthday Bot Dashboard with OpenAI support initialized');
    console.log('Auto-refresh enabled: data will update every 60 minutes without disrupting edits');
});