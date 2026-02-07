/**
 * Voice Capture Module
 * Handles microphone input and audio streaming
 */

class VoiceCapture {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.stream = null;
    }

    async startRecording() {
        try {
            // Request microphone access
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 16000
                } 
            });

            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: 'audio/webm'
            });

            this.audioChunks = [];

            // Collect audio data
            this.mediaRecorder.addEventListener('dataavailable', event => {
                this.audioChunks.push(event.data);
            });

            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;

            console.log('🎤 Recording started');
            return true;

        } catch (error) {
            console.error('Error starting recording:', error);
            alert('Could not access microphone. Please check permissions.');
            return false;
        }
    }

    async stopRecording() {
        return new Promise((resolve, reject) => {
            if (!this.mediaRecorder || !this.isRecording) {
                reject(new Error('Not recording'));
                return;
            }

            this.mediaRecorder.addEventListener('stop', () => {
                // Create audio blob
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                
                // Stop all tracks
                if (this.stream) {
                    this.stream.getTracks().forEach(track => track.stop());
                }

                this.isRecording = false;
                console.log('🛑 Recording stopped');

                resolve(audioBlob);
            });

            this.mediaRecorder.stop();
        });
    }

    isCurrentlyRecording() {
        return this.isRecording;
    }
}

// Alternative: Web Speech API (simpler but less accurate)
class WebSpeechRecognition {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        
        // Check browser support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';
        }
    }

    isSupported() {
        return this.recognition !== null;
    }

    startListening(onResult, onError) {
        if (!this.recognition) {
            onError(new Error('Speech recognition not supported'));
            return;
        }

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            onResult(transcript);
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            onError(event);
        };

        this.recognition.onend = () => {
            this.isListening = false;
        };

        this.recognition.start();
        this.isListening = true;
        console.log('👂 Listening...');
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

    isCurrentlyListening() {
        return this.isListening;
    }
}

// Export for use in app.js
window.VoiceCapture = VoiceCapture;
window.WebSpeechRecognition = WebSpeechRecognition;
