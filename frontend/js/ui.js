/**
 * UI Management Module
 * Handles UI updates and interactions
 */

class UIManager {
    constructor() {
        this.chatMessages = document.getElementById('chat-messages');
        this.transcript = document.getElementById('transcript');
        this.voiceBtn = document.getElementById('voice-btn');
        this.recordingIndicator = document.getElementById('recording-indicator');
        this.clarificationModal = document.getElementById('clarification-modal');
    }

    // Message Management
    addMessage(content, type = 'assistant') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (typeof content === 'string') {
            contentDiv.innerHTML = this.formatMessage(content);
        } else {
            contentDiv.appendChild(content);
        }
        
        messageDiv.appendChild(contentDiv);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.scrollToBottom();
        
        // Speak response if assistant message
        if (type === 'assistant' && window.speechSynthesis) {
            this.speak(content);
        }
    }

    formatMessage(text) {
        // Convert newlines to <br>
        return text.replace(/\n/g, '<br>');
    }

    addUserMessage(text) {
        this.addMessage(text, 'user');
    }

    addAssistantMessage(text) {
        this.addMessage(text, 'assistant');
    }

    addSystemMessage(text) {
        this.addMessage(text, 'system');
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    // Transcript Management
    updateTranscript(text) {
        // Remove placeholder if present
        const placeholder = this.transcript.querySelector('.placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        const p = document.createElement('p');
        p.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
        this.transcript.appendChild(p);
        
        // Scroll to bottom
        this.transcript.scrollTop = this.transcript.scrollHeight;
    }

    clearTranscript() {
        this.transcript.innerHTML = '<p class="placeholder">Your voice commands will appear here...</p>';
    }

    // Recording UI
    setRecordingState(isRecording) {
        if (isRecording) {
            this.voiceBtn.classList.add('recording');
            this.voiceBtn.querySelector('.status-text').textContent = 'Recording...';
            this.recordingIndicator.classList.remove('hidden');
        } else {
            this.voiceBtn.classList.remove('recording');
            this.voiceBtn.querySelector('.status-text').textContent = 'Tap to Speak';
            this.recordingIndicator.classList.add('hidden');
        }
    }

    // Service Status
    updateServiceStatus(service, status) {
        const statusElement = document.getElementById(`${service}-status`);
        if (!statusElement) return;

        const badge = statusElement.querySelector('.status-badge');
        
        if (status === 'connected') {
            badge.textContent = 'Connected';
            badge.classList.remove('disconnected');
            badge.classList.add('connected');
        } else {
            badge.textContent = 'Disconnected';
            badge.classList.remove('connected');
            badge.classList.add('disconnected');
        }
    }

    // Clarification Modal
    showClarification(question, options) {
        const modal = this.clarificationModal;
        const questionEl = document.getElementById('clarification-question');
        const optionsEl = document.getElementById('clarification-options');

        questionEl.textContent = question;
        optionsEl.innerHTML = '';

        options.forEach(option => {
            const btn = document.createElement('button');
            btn.textContent = option;
            btn.onclick = () => {
                this.hideClarification();
                // Trigger command with selected option
                window.app.handleTextCommand(option);
            };
            optionsEl.appendChild(btn);
        });

        modal.classList.remove('hidden');
    }

    hideClarification() {
        this.clarificationModal.classList.add('hidden');
    }

    // Text-to-Speech
    speak(text) {
        if (!window.speechSynthesis) return;

        // Cancel any ongoing speech
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        window.speechSynthesis.speak(utterance);
    }

    // Loading state
    showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant loading';
        loadingDiv.innerHTML = '<div class="message-content">⏳ Processing...</div>';
        loadingDiv.id = 'loading-message';
        this.chatMessages.appendChild(loadingDiv);
        this.scrollToBottom();
    }

    hideLoading() {
        const loading = document.getElementById('loading-message');
        if (loading) {
            loading.remove();
        }
    }

    // UI Handoff - Open external URL
    openURL(url) {
        window.open(url, '_blank');
    }
}

// Export
window.UIManager = UIManager;
