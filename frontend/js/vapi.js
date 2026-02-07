/**
 * Simple Browser Voice Input using Web Speech API
 * No external dependencies - works in Chrome/Edge
 */

class VapiClient {
    constructor() {
        this.isListening = false;
        this.recognition = null;
    }

    /**
     * Initialize Web Speech API
     */
    async init() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.error('❌ Speech recognition not supported in this browser');
            return false;
        }

        try {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';

            this.setupEventListeners();
            
            console.log('✅ Voice recognition initialized');
            return true;
        } catch (error) {
            console.error('❌ Failed to initialize voice recognition:', error);
            return false;
        }
    }

    /**
     * Set up speech recognition event listeners
     */
    setupEventListeners() {
        this.recognition.onstart = () => {
            console.log('🎤 Listening...');
            this.isListening = true;
            this.updateUI('listening');
        };

        this.recognition.onend = () => {
            console.log('🔇 Stopped listening');
            this.isListening = false;
            this.updateUI('disconnected');
        };

        this.recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }

            if (finalTranscript) {
                console.log('💬 You said:', finalTranscript.trim());
                this.handleCommand(finalTranscript.trim());
            }
        };

        this.recognition.onerror = (event) => {
            console.error('❌ Speech recognition error:', event.error);
            if (event.error === 'not-allowed') {
                alert('Microphone access denied. Please allow microphone access and try again.');
            }
            this.updateUI('error');
        };
    }

    /**
     * Start listening
     */
    async startCall() {
        if (!this.recognition) {
            alert('Voice recognition not initialized. Please refresh the page.');
            return;
        }

        if (this.isListening) {
            console.log('⚠️ Already listening');
            return;
        }

        try {
            this.recognition.start();
        } catch (error) {
            console.error('❌ Failed to start listening:', error);
        }
    }

    /**
     * Stop listening
     */
    stopCall() {
        if (!this.recognition || !this.isListening) {
            return;
        }

        try {
            this.recognition.stop();
        } catch (error) {
            console.error('❌ Failed to stop listening:', error);
        }
    }

    /**
     * Toggle listening
     */
    toggleCall() {
        if (this.isListening) {
            this.stopCall();
        } else {
            this.startCall();
        }
    }

    /**
     * Handle voice command
     */
    async handleCommand(text) {
        // Add to chat
        this.addMessage('user', text);

        // Send to backend
        try {
            const response = await fetch('http://localhost:8000/api/text/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            
            if (data.response) {
                this.addMessage('assistant', data.response);
                // Speak the response
                this.speak(data.response);
            }
        } catch (error) {
            console.error('❌ Failed to send command:', error);
            this.addMessage('system', 'Failed to process command. Please try again.');
        }
    }

    /**
     * Text-to-speech
     */
    speak(text) {
        if ('speechSynthesis' in window) {
            // Strip markdown formatting before speaking
            const cleanText = text
                .replace(/\*\*/g, '')  // Remove bold **
                .replace(/\*/g, '')    // Remove italic *
                .replace(/#{1,6}\s/g, '')  // Remove headers
                .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')  // Remove links, keep text
                .replace(/`/g, '');    // Remove code backticks
            
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            speechSynthesis.speak(utterance);
        }
    }

    /**
     * Update UI
     */
    updateUI(state) {
        const vapiBtn = document.getElementById('vapi-voice-btn');
        const vapiStatus = document.getElementById('vapi-status');
        
        if (!vapiBtn || !vapiStatus) return;

        switch (state) {
            case 'listening':
                vapiBtn.classList.add('active');
                vapiBtn.querySelector('.status-text').textContent = 'Stop Listening';
                vapiStatus.classList.remove('hidden');
                vapiStatus.innerHTML = '<span class="pulse-green"></span><span>Listening...</span>';
                break;
                
            case 'disconnected':
                vapiBtn.classList.remove('active');
                vapiBtn.querySelector('.status-text').textContent = 'Talk to AI';
                vapiStatus.classList.add('hidden');
                break;
                
            case 'error':
                vapiBtn.classList.remove('active');
                vapiBtn.querySelector('.status-text').textContent = 'Try Again';
                vapiStatus.classList.add('hidden');
                break;
        }
    }

    /**
     * Add message to chat
     */
    addMessage(role, text) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        // Convert markdown to HTML for display
        const htmlContent = this.markdownToHtml(text);
        messageDiv.innerHTML = `<div class="message-content">${htmlContent}</div>`;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    /**
     * Convert basic markdown to HTML
     */
    markdownToHtml(text) {
        return text
            // Bold text
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            // Italic text
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            // Line breaks
            .replace(/\n/g, '<br>')
            // Escape HTML
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            // Re-enable our formatted tags
            .replace(/&lt;strong&gt;/g, '<strong>')
            .replace(/&lt;\/strong&gt;/g, '</strong>')
            .replace(/&lt;em&gt;/g, '<em>')
            .replace(/&lt;\/em&gt;/g, '</em>')
            .replace(/&lt;br&gt;/g, '<br>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global instance
window.vapiClient = new VapiClient();

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🔧 Initializing voice recognition...');
    
    const success = await window.vapiClient.init();
    if (success) {
        // Set up button
        const vapiBtn = document.getElementById('vapi-voice-btn');
        if (vapiBtn) {
            vapiBtn.addEventListener('click', () => {
                window.vapiClient.toggleCall();
            });
        }
    } else {
        console.error('💡 Voice recognition not available. Use Chrome/Edge for voice features.');
    }
});
