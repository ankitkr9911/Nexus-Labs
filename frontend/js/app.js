/**
 * Main Application Logic - Voice-Only Version
 * Minimal setup for voice-first interface
 */

class NexusApp {
    constructor() {
        this.API_BASE_URL = 'http://localhost:8000/api';
        this.init();
    }

    init() {
        // Load service status
        this.checkServiceStatus();

        console.log('✅ NEXUS AI initialized');
        console.log('🎤 Voice-Only Mode: Using Web Speech API');
    }

    // Check service connection status
    async checkServiceStatus() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/services/status`);
            
            if (response.ok) {
                const status = await response.json();
                
                // Update service badges
                const updateBadge = (id, isConnected) => {
                    const badge = document.querySelector(`#${id} .status-badge`);
                    if (badge) {
                        badge.textContent = isConnected ? 'Ready' : 'Disconnected';
                        badge.classList.toggle('connected', isConnected);
                        badge.classList.toggle('disconnected', !isConnected);
                    }
                };

                updateBadge('gmail-status', status.gmail);
                updateBadge('maps-status', status.maps);
            }

        } catch (error) {
            console.error('Error checking service status:', error);
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NexusApp();
});
