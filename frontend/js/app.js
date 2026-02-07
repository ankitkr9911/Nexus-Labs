/**
 * Main Application Logic - VAPI Only Version
 * Simple orchestration for VAPI voice agent
 */

class NexusApp {
    constructor() {
        this.API_BASE_URL = 'http://localhost:8000/api';
        this.ui = new UIManager();
        this.init();
    }

    init() {
        // Event Listeners for text input only
        document.getElementById('send-btn').addEventListener('click', () => {
            this.handleSendButton();
        });

        document.getElementById('text-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSendButton();
            }
        });

        document.getElementById('clear-btn').addEventListener('click', () => {
            this.ui.clearTranscript();
        });

        // Hide Quick Voice button (not needed with VAPI)
        const quickVoiceBtn = document.getElementById('voice-btn');
        if (quickVoiceBtn) {
            quickVoiceBtn.style.display = 'none';
        }

        // Load service status
        this.checkServiceStatus();

        console.log('✅ NEXUS AI initialized');
        console.log('🎤 Voice: Using VAPI cloud agent');
    }

    // Text Input Handler
    async handleSendButton() {
        const input = document.getElementById('text-input');
        const text = input.value.trim();

        if (!text) return;

        input.value = '';
        this.ui.addUserMessage(text);
        await this.processCommand(text);
    }

    // Send audio to backend for Deepgram transcription
    async sendAudioToBackend(audioBlob) {
        try {
            this.ui.showLoading();

            // Convert blob to base64
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            
            reader.onloadend = async () => {
                const base64Audio = reader.result.split(',')[1];

                const response = await fetch(`${this.API_BASE_URL}/voice/process`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        audio: base64Audio,
                        format: 'audio/webm'
                    })
                });

                this.ui.hideLoading();

                if (!response.ok) {
                    throw new Error('Failed to process audio');
                }

                const result = await response.json();
                this.handleCommandResult(result);
            };

        } catch (error) {
            console.error('Error sending audio:', error);
            this.ui.hideLoading();
            this.ui.addSystemMessage('Error processing voice command.');
        }
    }

    // Send Button Handler
    handleSendButton() {
        const input = document.getElementById('text-input');
        const command = input.value.trim();

        if (!command) return;

        this.ui.addUserMessage(command);
        this.ui.updateTranscript(command);
        input.value = '';

        this.processCommand(command);
    }

    // Process command through backend
    async processCommand(command) {
        try {
            this.ui.showLoading();

            const response = await fetch(`${this.API_BASE_URL}/text/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: command })
            });

            this.ui.hideLoading();

            if (!response.ok) {
                throw new Error('Failed to process command');
            }

            const result = await response.json();
            this.handleCommandResult(result);

        } catch (error) {
            console.error('Error processing command:', error);
            this.ui.hideLoading();
            this.ui.addSystemMessage('Sorry, I encountered an error. Please try again.');
        }
    }

    // Handle command result from backend
    handleCommandResult(result) {
        console.log('Result:', result);

        // Clarification needed
        if (result.type === 'clarification') {
            this.ui.addAssistantMessage(result.question);
            if (result.options && result.options.length > 0) {
                this.ui.showClarification(result.question, result.options);
            }
            return;
        }

        // UI Handoff (open external app)
        if (result.type === 'ui_handoff') {
            this.ui.addAssistantMessage(result.voice_response);
            if (result.url) {
                this.ui.openURL(result.url);
            }
            return;
        }

        // API Response
        if (result.type === 'api_response') {
            this.ui.addAssistantMessage(result.voice_response);
            return;
        }

        // Error
        if (result.type === 'error') {
            this.ui.addSystemMessage(result.voice_response || result.message);
            return;
        }

        // Success response from n8n workflow
        if (result.success && result.message) {
            this.ui.addAssistantMessage(result.message);
            return;
        }

        // Default
        this.ui.addAssistantMessage(result.voice_response || result.message || 'Command processed.');
    }

    // Check service connection status
    async checkServiceStatus() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/services/status`);
            
            if (response.ok) {
                const status = await response.json();
                
                this.ui.updateServiceStatus('gmail', status.gmail);
                this.ui.updateServiceStatus('maps', status.maps);
            }

        } catch (error) {
            console.error('Error checking service status:', error);
        }
    }

    // Public method for clarification handling
    handleTextCommand(command) {
        this.ui.addUserMessage(command);
        this.processCommand(command);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NexusApp();
});
