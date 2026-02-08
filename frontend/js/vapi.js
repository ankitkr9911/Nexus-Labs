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
            this.updateStatus('Listening...', 'Speak your command');
        };

        this.recognition.onend = () => {
            console.log('🔇 Stopped listening');
            this.isListening = false;
            this.updateUI('idle');
            this.updateStatus('Ready to assist', 'Press the button to start talking');
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
        // Stop speech recognition
        if (this.recognition && this.isListening) {
            try {
                this.recognition.stop();
            } catch (error) {
                console.error('❌ Failed to stop listening:', error);
            }
        }
        
        // Stop any ongoing speech synthesis
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
            console.log('🔇 Stopped speaking');
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
        console.log('💬 Processing:', text);

        // Check if user wants directions (after getting distance info)
        if (text.toLowerCase().includes('direction') || text.toLowerCase().includes('navigate') || text.toLowerCase().includes('give me directions')) {
            // Check if we have stored location data
            if (window.lastLocationData) {
                const { origin, destination } = window.lastLocationData;
                const mapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}`;
                window.open(mapsUrl, '_blank');
                this.updateStatus('Opening Maps...', 'Redirecting to Google Maps');
                this.speak('Opening Google Maps with your route');
                return;
            }
        }

        // Show processing state
        this.updateUI('processing');
        this.updateStatus('Processing...', 'NEXUS AI is thinking');

        // Send to backend
        try {
            const response = await fetch('http://localhost:8000/api/text/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();
            
            if (data.response) {
                // Store location data if this is a maps query
                if (data.service === 'maps' && (data.origin || data.destination)) {
                    window.lastLocationData = {
                        origin: data.origin || data.data?.origin || data.data?.parameters?.origin,
                        destination: data.destination || data.data?.destination || data.data?.parameters?.destination
                    };
                    console.log('📍 Stored location data:', window.lastLocationData);
                }
                
                // Speak the response
                this.speak(data.response);
            }
        } catch (error) {
            console.error('❌ Failed to send command:', error);
            this.updateStatus('Error', 'Failed to process command');
            this.speak('Sorry, I encountered an error. Please try again.');
        }
    }

    /**
     * Text-to-speech
     */
    speak(text) {
        if ('speechSynthesis' in window) {
            // Strip all markdown and special formatting before speaking
            const cleanText = text
                .replace(/\*\*/g, '')  // Remove bold **
                .replace(/\*/g, '')    // Remove italic *
                .replace(/#{1,6}\s/g, '')  // Remove headers ###
                .replace(/---+/g, '')  // Remove horizontal rules ---
                .replace(/\.\.\./g, '')  // Remove ellipsis ...
                .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')  // Remove links, keep text
                .replace(/`/g, '')     // Remove code backticks
                .replace(/~/g, '')     // Remove strikethrough ~
                .replace(/\|/g, '')    // Remove table pipes
                .replace(/>/g, '')     // Remove blockquotes >
                .replace(/\n\n+/g, '. ')  // Replace double newlines with period
                .replace(/\n/g, ' ')   // Replace single newlines with space
                .trim();
            
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            
            // Update UI when speaking
            utterance.onstart = () => {
                this.updateUI('speaking');
                this.updateStatus('Speaking...', 'NEXUS AI is responding');
            };
            
            utterance.onend = () => {
                this.updateUI('listening');
                this.updateStatus('Listening...', 'Speak your command');
            };
            
            speechSynthesis.speak(utterance);
        }
    }

    /**
     * Update UI visual state
     */
    updateUI(state) {
        const voiceInterface = document.querySelector('.voice-interface');
        if (!voiceInterface) return;

        // Remove all state classes
        voiceInterface.classList.remove('idle', 'listening', 'processing', 'speaking');
        
        // Add current state class
        voiceInterface.classList.add(state);
    }

    /**
     * Update status text
     */
    updateStatus(title, subtitle) {
        const statusTitle = document.querySelector('.status-title');
        const statusSubtitle = document.querySelector('.status-subtitle');
        
        if (statusTitle) statusTitle.textContent = title;
        if (statusSubtitle) statusSubtitle.textContent = subtitle;
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
