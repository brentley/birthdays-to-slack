// Enhanced app.js with OpenAI message support

// Include existing app.js content
document.write('<script src="/static/js/app.js"></script>');

// Extended BirthdayManager for OpenAI features
class EnhancedBirthdayManager extends BirthdayManager {
    updateServiceStatusDisplay(data) {
        super.updateServiceStatusDisplay(data);
        
        const openaiStatusElement = document.getElementById('openai-status');
        const editPromptBtn = document.getElementById('editPromptBtn');
        
        if (openaiStatusElement && data.openai_configured !== undefined) {
            if (data.openai_configured) {
                openaiStatusElement.innerHTML = '<i class="bi bi-robot text-success"></i> <span>Enabled</span>';
                openaiStatusElement.className = 'status-value text-success';
                if (editPromptBtn) editPromptBtn.style.display = 'inline-block';
            } else {
                openaiStatusElement.innerHTML = '<i class="bi bi-dash-circle text-muted"></i> <span>Disabled</span>';
                openaiStatusElement.className = 'status-value text-muted';
                if (editPromptBtn) editPromptBtn.style.display = 'none';
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
                            <div class="message-preview">${this.escapeHtml(event.message)}</div>
                        </div>
                        ${isGenerated ? `
                            <button class="btn btn-sm btn-outline-secondary ms-2" 
                                    onclick="regenerateMessage('${this.escapeHtml(event.name)}', '${event.date}')"
                                    title="Regenerate message">
                                <i class="bi bi-arrow-clockwise"></i>
                            </button>
                        ` : ''}
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
            body: JSON.stringify({ template })
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

// Override the global birthday manager with enhanced version
document.addEventListener('DOMContentLoaded', function() {
    // Replace with enhanced manager
    window.birthdayManager = new EnhancedBirthdayManager();
    
    console.log('Birthday Bot Dashboard with OpenAI support initialized');
});