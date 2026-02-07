# NEXUS Voice Agent - LiveKit Integration

Voice-first interface for NEXUS automation platform using LiveKit Cloud.

## 📋 Features

- **Natural Voice Interaction**: Speak commands naturally
- **Real-time Processing**: Immediate response through LiveKit
- **Smart Understanding**: AI-powered intent recognition via Gemini
- **Service Integration**: Gmail, Google Maps, and more
- **Low Latency**: LiveKit cloud infrastructure for fast responses

## 🏗️ Architecture

```
User → Frontend (voice_client.html) → LiveKit Cloud → Voice Agent → NEXUS Backend → n8n + Gemini
```

1. User speaks to `voice_client.html` in browser
2. Audio streamed to LiveKit Cloud
3. Voice Agent (Deepgram STT + GPT-4 + OpenAI TTS) processes
4. Agent calls NEXUS Backend API for actions
5. Backend routes to n8n workflow with Gemini
6. Response flows back to user as speech

## 🚀 Setup Instructions

### Prerequisites

1. **LiveKit Cloud Account**
   - Sign up at https://cloud.livekit.io
   - Create a new project
   - Note down: API Key, API Secret, WebSocket URL

2. **Existing NEXUS Components**
   - ✅ Backend running (port 8000)
   - ✅ n8n running (port 5678)
   - ✅ Deepgram API key (already have)

3. **Additional API Keys**
   - OpenAI API key (for GPT-4 reasoning and TTS)

### Step 1: Install Dependencies

```bash
cd voice_agent

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install packages (uses EXACT versions from XRAY_Agent)
pip install -r requirements.txt
```

### Step 2: Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# LiveKit (from your LiveKit Cloud dashboard)
LIVEKIT_URL=wss://your-project-xxxxx.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxxxxxxxxxxxx

# Deepgram (you already have this)
DEEPGRAM_API_KEY=fbadb1f62172434f56ae19518e03870e1989bdc3

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# NEXUS Backend (should be running)
NEXUS_BACKEND_URL=http://localhost:8000
N8N_WEBHOOK_URL=http://localhost:5678/webhook/nexus-agent
```

### Step 3: Test Configuration

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓ Loaded' if os.getenv('LIVEKIT_URL') else '✗ Missing LIVEKIT_URL')"
```

### Step 4: Start Voice Server

```bash
python voice_server.py
```

This starts the FastAPI server on port **8001** that:
- Creates LiveKit rooms
- Generates access tokens
- Manages voice sessions

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Step 5: Test API

Open another terminal:

```bash
curl http://localhost:8001/api/voice/test
```

Expected response:
```json
{
  "status": "ready",
  "message": "All credentials configured correctly",
  "livekit_url": "wss://...",
  "has_deepgram": true,
  "has_openai": true
}
```

### Step 6: Open Voice Client

Open `voice_client.html` in your browser (Chrome/Edge recommended):

```bash
# Windows
start voice_client.html

# Mac
open voice_client.html

# Or just double-click the file
```

### Step 7: Connect and Speak!

1. Click **"Connect to Voice Agent"**
2. Allow microphone access when prompted
3. Wait for "Connected! You can speak now"
4. Speak naturally:
   - "Check my emails"
   - "Send email to john@example.com about project update"
   - "Distance from Mumbai to Delhi"

## 🎯 How It Works

### Voice Flow

```
You: "Check my emails"
  ↓
[Deepgram STT] → "check my emails" (text)
  ↓
[GPT-4 LLM] → Understands intent: Gmail summarize
  ↓
[NEXUS Backend API] → POST /api/text/process {"text": "check my emails"}
  ↓
[n8n Workflow] → Gemini classifies → Gmail node → Fetches emails
  ↓
[Response] → {"success": true, "message": "You have 5 new emails..."}
  ↓
[OpenAI TTS] → Speaks response back to you
```

### Components

1. **voice_client.html** - Frontend interface with LiveKit Client SDK
2. **voice_server.py** - FastAPI server for room/token management
3. **nexus_voice_agent.py** - LiveKit agent worker (connects to rooms)
4. **requirements.txt** - Python dependencies (exact versions!)

## 🔧 Troubleshooting

### "Failed to create room"

- Check `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` in `.env`
- Verify LiveKit project is active
- Test at: https://cloud.livekit.io

### "Missing API keys"

```bash
curl http://localhost:8001/api/voice/test
```

Will show which keys are missing.

### "Can't connect to NEXUS backend"

- Ensure backend is running: http://localhost:8000
- Check `NEXUS_BACKEND_URL` in `.env`
- Test backend: `curl http://localhost:8000/`

### "Microphone permission denied"

- Must use HTTPS or localhost
- Check browser microphone settings
- Try Chrome/Edge (best WebRTC support)

## 📦 Version Compatibility

**CRITICAL**: We use **exact versions** from XRAY_Agent to avoid compatibility issues:

- `livekit-agents==0.8.12`
- `livekit-plugins-deepgram==0.6.8`
- `livekit-plugins-openai==0.7.1`
- `livekit-plugins-silero==0.6.4`

DO NOT upgrade these without testing!

## 🌐 Integration with Main Website

To add "Talk to AI" button to your main NEXUS website:

```html
<button onclick="window.open('voice_client.html', '_blank', 'width=600,height=800')">
  🎤 Talk to NEXUS AI
</button>
```

Or redirect:
```javascript
// In your frontend/js/app.js
document.getElementById('voice-btn').addEventListener('click', () => {
    window.location.href = '/voice_client.html';
});
```

## 🚀 Next Steps

1. ✅ Get LiveKit Cloud credentials
2. ✅ Configure `.env` file
3. ✅ Start voice_server.py
4. ✅ Test voice_client.html
5. 🔄 Integrate with main website
6. 🎯 Add more voice commands
7. 📊 Add analytics/logging
8. 🎨 Customize voice/persona

## 📝 Notes

- Voice agent runs in LiveKit Cloud (not locally)
- Free tier: 10,000 minutes/month
- Uses your existing Deepgram key
- OpenAI TTS: ~$15 per 1M characters
- GPT-4: ~$0.03 per 1K tokens

## 🔗 Resources

- LiveKit Docs: https://docs.livekit.io
- LiveKit Cloud: https://cloud.livekit.io
- Deepgram STT: https://deepgram.com
- OpenAI TTS: https://platform.openai.com/docs/guides/text-to-speech
