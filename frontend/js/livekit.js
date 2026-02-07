/**
 * LiveKit Voice Agent Integration
 * Handles connection to LiveKit cloud for smart voice conversations
 */

class LiveKitVoiceAgent {
    constructor() {
        this.room = null;
        this.isConnected = false;
        this.apiBaseUrl = 'http://localhost:8000';
    }

    /**
     * Initialize and connect to LiveKit voice agent
     */
    async connect(userName = 'User') {
        try {
            console.log('🎙️ Connecting to NEXUS Voice Agent...');
            
            // Show status
            this.updateStatus('Connecting...', true);
            
            // Create LiveKit room and get token
            const response = await fetch(`${this.apiBaseUrl}/api/livekit/create-room`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_name: userName
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create room');
            }

            const roomData = await response.json();
            console.log('✓ Room created:', roomData);

            // Open LiveKit Playground with room details
            const livekitUrl = roomData.url;
            const token = roomData.token;
            const roomName = roomData.room_name;

            // Construct LiveKit Playground URL
            const playgroundUrl = this.buildPlaygroundUrl(livekitUrl, token, roomName);
            
            console.log('🚀 Opening LiveKit Playground:', playgroundUrl);
            
            // Open in new window
            const width = 1200;
            const height = 800;
            const left = (screen.width - width) / 2;
            const top = (screen.height - height) / 2;
            
            const voiceWindow = window.open(
                playgroundUrl,
                'nexus-voice-agent',
                `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
            );

            if (!voiceWindow) {
                throw new Error('Popup blocked. Please allow popups for this site.');
            }

            this.isConnected = true;
            this.updateStatus('Voice Agent Active', true);

            // Show message in main UI
            this.addMessage('system', 
                `🎙️ Voice Agent Connected!\n\n` +
                `Room: ${roomName}\n` +
                `You can now talk to NEXUS in the voice window.\n\n` +
                `Capabilities:\n` +
                `• Email management\n` +
                `• Navigation & directions\n` +
                `• Music control\n` +
                `• General assistance`
            );

            // Monitor window close
            const checkWindow = setInterval(() => {
                if (voiceWindow.closed) {
                    clearInterval(checkWindow);
                    this.disconnect();
                }
            }, 1000);

            return roomData;

        } catch (error) {
            console.error('❌ LiveKit connection error:', error);
            this.updateStatus('Connection Failed', false);
            this.addMessage('error', 
                `Failed to connect to Voice Agent: ${error.message}\n\n` +
                `Please ensure:\n` +
                `• Backend server is running (port 8000)\n` +
                `• LiveKit credentials are configured\n` +
                `• Voice agent is running: python voice_agent/nexus_livekit_agent.py`
            );
            throw error;
        }
    }

    /**
     * Build LiveKit Playground URL with authentication
     */
    buildPlaygroundUrl(livekitUrl, token, roomName) {
        // LiveKit Playground URL format
        // https://meet.livekit.io/custom?url=wss://...&token=...
        
        const wsUrl = livekitUrl.replace('wss://', '').replace('https://', '');
        
        // Use custom LiveKit meet interface
        const playgroundBase = 'https://meet.livekit.io/custom';
        const params = new URLSearchParams({
            liveKitUrl: `wss://${wsUrl}`,
            token: token,
            // Optional: customize appearance
            name: 'NEXUS Voice Agent',
            theme: 'dark'
        });

        return `${playgroundBase}?${params.toString()}`;
    }

    /**
     * Disconnect from voice agent
     */
    disconnect() {
        if (this.room) {
            this.room.disconnect();
            this.room = null;
        }
        
        this.isConnected = false;
        this.updateStatus('Disconnected', false);
        
        console.log('🔌 Disconnected from Voice Agent');
        this.addMessage('system', '🔌 Voice Agent disconnected');
    }

    /**
     * Update status indicator
     */
    updateStatus(text, isActive) {
        const statusElement = document.getElementById('livekit-status');
        if (!statusElement) return;

        if (isActive) {
            statusElement.classList.remove('hidden');
            statusElement.querySelector('span:last-child').textContent = text;
        } else {
            statusElement.classList.add('hidden');
        }
    }

    /**
     * Add message to chat UI
     */
    addMessage(type, text) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const textContent = document.createElement('p');
        textContent.style.whiteSpace = 'pre-line';
        textContent.textContent = text;
        
        contentDiv.appendChild(textContent);
        messageDiv.appendChild(contentDiv);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Check if LiveKit is available
     */
    async checkStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/livekit/status`);
            const status = await response.json();
            return status;
        } catch (error) {
            console.error('Error checking LiveKit status:', error);
            return { available: false, configured: false };
        }
    }
}

// Initialize global instance
window.livekitAgent = new LiveKitVoiceAgent();

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    const livekitBtn = document.getElementById('livekit-voice-btn');
    
    if (livekitBtn) {
        // Check status
        const status = await window.livekitAgent.checkStatus();
        
        if (!status.available || !status.configured) {
            livekitBtn.disabled = true;
            livekitBtn.title = 'LiveKit not configured. See setup instructions.';
            livekitBtn.style.opacity = '0.5';
            console.warn('⚠️ LiveKit not available');
        }

        // Add click handler
        livekitBtn.addEventListener('click', async () => {
            try {
                // Prompt for user name
                const userName = prompt('Enter your name:', 'User') || 'User';
                
                // Connect to voice agent
                await window.livekitAgent.connect(userName);
                
            } catch (error) {
                console.error('Error connecting to voice agent:', error);
            }
        });
    }
});
