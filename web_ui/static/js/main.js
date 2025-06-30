// Main Application JavaScript - Modular and optimized

class WebUIApp {
    constructor() {
        this.apiBase = '/api';
        this.sessionId = null;
        this.websocket = null;
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Web UI App initializing...');
        
        // Initialize session
        await this.initSession();
        
        // Setup event listeners
        this.setupEventListeners();
        
        console.log('✅ Web UI App initialized');
    }
    
    async initSession() {
        try {
            // Create a session ID locally for now
            this.sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
        } catch (error) {
            console.error('Failed to initialize session:', error);
        }
    }
    
    setupEventListeners() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
        });
        
        // Connection status
        window.addEventListener('online', () => {
            this.showNotification('Connection restored', 'success');
        });
        
        window.addEventListener('offline', () => {
            this.showNotification('Connection lost', 'warning');
        });
    }
    
    showNotification(message, type = 'info') {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            background-color: ${type === 'success' ? '#10b981' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
            z-index: 1000;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WebUIApp();
});