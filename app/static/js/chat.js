/**
 * Chat JavaScript Module
 * ======================
 * Real-time WebSocket communication with StormGuard backend
 */

// Configuration
const API_BASE_URL = window.location.origin + '/api/v1';
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const WS_BASE = `${WS_PROTOCOL}//${window.location.host}/api/v1`;

// State
let currentUser = null;
let currentSessionId = null;
let webSocket = null;
let messageAuthToken = localStorage.getItem('access_token');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is logged in
    if (!messageAuthToken) {
        showLoginModal();
    } else {
        initializeApp();
    }
});

// ===== Authentication =====

async function login(email) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        
        const data = await response.json();
        if (data.access_token) {
            messageAuthToken = data.access_token;
            currentUser = data.user;
            localStorage.setItem('access_token', messageAuthToken);
            localStorage.setItem('user_id', currentUser.id);
            
            // Close modal and initialize
            document.getElementById('login-modal').classList.remove('active');
            initializeApp();
        } else {
            showError('Login failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        showError('Login error: ' + error.message);
    }
}

async function register(formData) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        if (data.access_token) {
            messageAuthToken = data.access_token;
            currentUser = data.user;
            localStorage.setItem('access_token', messageAuthToken);
            localStorage.setItem('user_id', currentUser.id);
            
            // Close modal and initialize
            document.getElementById('register-modal').classList.remove('active');
            initializeApp();
        } else {
            showError('Registration failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        showError('Registration error: ' + error.message);
    }
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    if (webSocket) webSocket.close();
    location.reload();
}

// ===== App Initialization =====

async function initializeApp() {
    try {
        // Get user info
        const userId = localStorage.getItem('user_id');
        const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
            headers: { 'Authorization': `bearer ${messageAuthToken}` }
        });
        
        currentUser = await response.json();
        
        // Update UI
        document.getElementById('username').textContent = currentUser.full_name || currentUser.email;
        document.getElementById('current-location').textContent = 
            `Location: ${currentUser.latitude.toFixed(2)}, ${currentUser.longitude.toFixed(2)}`;
        
        // Load sessions
        loadChatSessions();
        
        // Load stats
        loadAlertStats();
        
        // Load recent alerts
        loadRecentAlerts();
        
        // Setup event listeners
        setupEventListeners();
        
        // Create new session
        startNewChat();
    } catch (error) {
        showError('Failed to initialize app: ' + error.message);
    }
}

// ===== Chat Functions =====

function startNewChat() {
    currentSessionId = generateUUID();
    
    // Clear messages
    const messagesContainer = document.getElementById('messages-container');
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <h2>New Conversation</h2>
            <p>Ask about disaster risks in your area</p>
        </div>
    `;
    
    // Connect WebSocket
    connectWebSocket();
}

function connectWebSocket() {
    const wsUrl = `${WS_BASE}/chat/ws/${currentUser.id}/${currentSessionId}`;
    webs = new WebSocket(wsUrl);
    
    webSocket.onopen = () => {
        console.log('WebSocket connected');
        addSystemMessage('Connected to StormGuard AI');
    };
    
    webSocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            
            if (data.error) {
                addSystemMessage('Error: ' + data.error);
            } else if (data.response) {
                addAssistantMessage(data.response, data.sources || []);
            }
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    };
    
    webSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        addSystemMessage('Connection error. Retrying...');
    };
    
    webSocket.onclose = () => {
        console.log('WebSocket closed');
    };
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add to UI
    addUserMessage(message);
    input.value = '';
    
    // Send via WebSocket if connected
    if (webSocket && webSocket.readyState === WebSocket.OPEN) {
        webSocket.send(JSON.stringify({ message }));
    } else {
        // Fallback to HTTP POST
        sendMessageHttp(message);
    }
    
    // Show loading
    showLoadingSpinner();
}

async function sendMessageHttp(message) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `bearer ${messageAuthToken}`
            },
            body: JSON.stringify({
                message,
                session_id: currentSessionId
            })
        });
        
        const data = await response.json();
        hideLoadingSpinner();
        
        if (data.assistant_response) {
            addAssistantMessage(data.assistant_response, data.sources || []);
        } else {
            showError('Failed to get response');
        }
    } catch (error) {
        hideLoadingSpinner();
        showError('Error sending message: ' + error.message);
    }
}

// ===== UI Functions =====

function addUserMessage(text) {
    const messagesContainer = document.getElementById('messages-container');
    
    // Remove welcome message if it exists
    const welcome = messagesContainer.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    
    const messageEl = document.createElement('div');
    messageEl.className = 'message user-message';
    messageEl.innerHTML = `
        <div class="message-content">${escapeHtml(text)}</div>
        <small>${new Date().toLocaleTimeString()}</small>
    `;
    
    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addAssistantMessage(text, sources = []) {
    const messagesContainer = document.getElementById('messages-container');
    
    const messageEl = document.createElement('div');
    messageEl.className = 'message assistant-message';
    
    let sourcesHtml = '';
    if (sources.length > 0) {
        sourcesHtml = '<div class="sources"><strong>Sources:</strong><ul>';
        sources.forEach(source => {
            sourcesHtml += `<li>${escapeHtml(source.content)}... (${(source.similarity * 100).toFixed(1)}%)</li>`;
        });
        sourcesHtml += '</ul></div>';
    }
    
    messageEl.innerHTML = `
        <div class="message-content">${text}</div>
        ${sourcesHtml}
        <small>${new Date().toLocaleTimeString()}</small>
    `;
    
    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addSystemMessage(text) {
    const messagesContainer = document.getElementById('messages-container');
    
    const messageEl = document.createElement('div');
    messageEl.className = 'message system-message';
    messageEl.innerHTML = `
        <div class="message-content"><em>${escapeHtml(text)}</em></div>
    `;
    
    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ===== Alert Functions =====

async function loadRecentAlerts() {
    try {
        const response = await fetch(
            `${API_BASE_URL}/alerts/user/${currentUser.id}?limit=5&unread_only=true`,
            { headers: { 'Authorization': `bearer ${messageAuthToken}` }}
        );
        
        const alerts = await response.json();
        const panel = document.getElementById('alerts-panel');
        
        if (alerts.length === 0) {
            panel.innerHTML = '<p class="placeholder">No recent alerts</p>';
            return;
        }
        
        let html = '';
        alerts.forEach(alert => {
            const emoji = alert.risk_level === 'CRITICAL' ? '🚨' : '⚠️';
            html += `
                <div class="alert-item ${alert.risk_level.toLowerCase()}">
                    <strong>${emoji} ${alert.disaster_type}</strong>
                    <p>${alert.message}</p>
                    <small>${new Date(alert.created_at).toLocaleString()}</small>
                </div>
            `;
        });
        
        panel.innerHTML = html;
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

async function loadAlertStats() {
    try {
        const response = await fetch(
            `${API_BASE_URL}/alerts/stats/${currentUser.id}`,
            { headers: { 'Authorization': `bearer ${messageAuthToken}` }}
        );
        
        const stats = await response.json();
        const panel = document.getElementById('stats-panel');
        
        let html = `
            <div class="stat">
                <span class="stat-value">${stats.total_alerts}</span>
                <span class="stat-label">Total</span>
            </div>
            <div class="stat">
                <span class="stat-value">${stats.read}</span>
                <span class="stat-label">Read</span>
            </div>
            <div class="stat">
                <span class="stat-value">${stats.clicked}</span>
                <span class="stat-label">Clicked</span>
            </div>
        `;
        
        panel.innerHTML = html;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadChatSessions() {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
            headers: { 'Authorization': `bearer ${messageAuthToken}` }
        });
        
        const sessions = await response.json();
        const list = document.getElementById('sessions-list');
        
        if (sessions.length === 0) {
            list.innerHTML = '<p class="placeholder">No conversations yet</p>';
            return;
        }
        
        let html = '';
        sessions.forEach(session => {
            html += `
                <div class="session-item" onclick="loadSession('${session.session_id}')">
                    <p class="session-preview">${escapeHtml(session.first_message)}</p>
                    <small>${session.message_count} messages</small>
                </div>
            `;
        });
        
        list.innerHTML = html;
    } catch (error) {
        console.error('Error loading sessions:', error);
    }
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/chat/history/${sessionId}`,
            { headers: { 'Authorization': `bearer ${messageAuthToken}` }}
        );
        
        const session = await response.json();
        const messagesContainer = document.getElementById('messages-container');
        
        messagesContainer.innerHTML = '';
        
        session.messages.forEach(msg => {
            addUserMessage(msg.user_message);
            addAssistantMessage(msg.assistant_response, msg.sources);
        });
    } catch (error) {
        showError('Error loading session: ' + error.message);
    }
    
    // Reconnect WebSocket
    if (webSocket) webSocket.close();
    connectWebSocket();
}

// ===== Event Listeners =====

function setupEventListeners() {
    // Send button
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    
    // Message input - Send on Enter, newline on Shift+Enter
    document.getElementById('message-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Logout button
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // New chat button
    document.getElementById('new-chat-btn').addEventListener('click', startNewChat);
    
    // Preferences button
    document.getElementById('preferences-btn').addEventListener('click', showPreferencesModal);
    
    // Login form
    document.getElementById('login-form').addEventListener('submit', (e) => {
        e.preventDefault();
        login(document.getElementById('login-email').value);
    });
    
    // Register form
    document.getElementById('register-form').addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = {
            email: document.getElementById('register-email').value,
            full_name: document.getElementById('register-name').value,
            city: document.getElementById('register-city').value,
            timezone: document.getElementById('register-timezone').value,
            latitude: parseFloat(document.getElementById('register-lat').value),
            longitude: parseFloat(document.getElementById('register-lon').value),
            interests: ['hurricane', 'heat_wave', 'flood']
        };
        register(formData);
    });
    
    // Preferences form
    document.getElementById('preferences-form').addEventListener('submit', savePreferences);
}

// ===== Modal Functions =====

function showLoginModal() {
    document.getElementById('login-modal').classList.add('active');
}

function showRegisterModal() {
    document.getElementById('register-modal').classList.add('active');
    document.getElementById('login-modal').classList.remove('active');
}

async function showPreferencesModal() {
    const modal = document.getElementById('preferences-modal');
    
    try {
        // Load current preferences
        const response = await fetch(
            `${API_BASE_URL}/users/${currentUser.id}/preferences`,
            { headers: { 'Authorization': `bearer ${messageAuthToken}` }}
        );
        
        const prefs = await response.json();
        
        // Fill form
        document.getElementById('pref-hurricane').checked = prefs.hurricane_alerts;
        document.getElementById('pref-heat').checked = prefs.heat_wave_alerts;
        document.getElementById('pref-flood').checked = prefs.flood_alerts;
        document.getElementById('pref-storm').checked = prefs.severe_storm_alerts;
        document.getElementById('pref-min-risk').value = prefs.min_risk_level;
        document.getElementById('pref-radius').value = prefs.alert_radius_km;
        document.getElementById('pref-push').checked = prefs.enable_push;
        document.getElementById('pref-email').checked = prefs.enable_email;
        
        modal.classList.add('active');
    } catch (error) {
        showError('Error loading preferences: ' + error.message);
    }
}

function closePreferencesModal() {
    document.getElementById('preferences-modal').classList.remove('active');
}

async function savePreferences(e) {
    e.preventDefault();
    
    const preferences = {
        hurricane_alerts: document.getElementById('pref-hurricane').checked,
        heat_wave_alerts: document.getElementById('pref-heat').checked,
        flood_alerts: document.getElementById('pref-flood').checked,
        severe_storm_alerts: document.getElementById('pref-storm').checked,
        min_risk_level: document.getElementById('pref-min-risk').value,
        alert_radius_km: parseInt(document.getElementById('pref-radius').value),
        enable_push: document.getElementById('pref-push').checked,
        enable_email: document.getElementById('pref-email').checked
    };
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/users/${currentUser.id}/preferences`,
            {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `bearer ${messageAuthToken}`
                },
                body: JSON.stringify(preferences)
            }
        );
        
        if (response.ok) {
            closePreferencesModal();
            addSystemMessage('Preferences saved successfully');
        } else {
            showError('Failed to save preferences');
        }
    } catch (error) {
        showError('Error saving preferences: ' + error.message);
    }
}

// ===== Utility Functions =====

function showLoadingSpinner() {
    document.getElementById('loading-spinner').classList.remove('hidden');
}

function hideLoadingSpinner() {
    document.getElementById('loading-spinner').classList.add('hidden');
}

function showError(message) {
    alert('❌ ' + message);
    console.error(message);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Auto-refresh alerts every 30 seconds
setInterval(() => {
    if (currentUser) {
        loadRecentAlerts();
        loadAlertStats();
    }
}, 30000);
