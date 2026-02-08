# 🎯 NEXUS AI - Voice-First Intelligent Automation Platform

## Overview

**NEXUS AI** is a voice-controlled automation platform that enables users to interact with their digital services (Gmail, Google Maps) through natural conversation. Unlike traditional chatbots with rigid command patterns, NEXUS uses Google Gemini LLM for true semantic understanding, making it feel like talking to a human assistant.

## 🎥 Demo

Voice-only interface with real-time visual feedback - no typing, no text display, just natural conversation.

## 🚀 The Problem We're Solving

Modern digital workflows are fragmented:
- **Multiple apps** for different tasks (Gmail, Maps, Spotify, etc.)
- **Complex UIs** requiring manual navigation
- **Context switching** between applications
- **Time-consuming** repetitive tasks

**Traditional voice assistants are limited:**
- Rigid command structures ("Say exactly this...")
- No conversational context
- Cloud-dependent with privacy concerns
- Limited customization

**NEXUS Solution:**
- 🎤 **Natural conversation** - Speak naturally, AI understands variations
- 🧠 **Context-aware** - Remembers conversation history
- 🔒 **Self-hosted** - Full control over your data
- 🎯 **Extensible** - Add new services without coding
- 🌐 **No dependencies** - Browser-native speech APIs

## 🏗️ Architecture

### High-Level Flow

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐      ┌──────────────┐
│   Browser   │      │   FastAPI    │      │     n8n     │      │   Services   │
│   (Voice)   │─────▶│   Backend    │─────▶│  Workflow   │─────▶│ Gmail, Maps  │
│ Web Speech  │      │  Port 8000   │      │  Port 5678  │      │  APIs        │
└─────────────┘      └──────────────┘      └─────────────┘      └──────────────┘
                            │                      │
                            │                      │
                            ▼                      ▼
                     ┌─────────────┐      ┌──────────────┐
                     │   SQLite    │      │  Gemini LLM  │
                     │   Memory    │      │  (Decision   │
                     │   Context   │      │   Maker)     │
                     └─────────────┘      └──────────────┘
```

### Component Breakdown

#### 1. **Frontend** (Browser)
- **Technology**: Vanilla HTML/CSS/JavaScript
- **Voice Input**: Web Speech API (`webkitSpeechRecognition`)
- **Voice Output**: Speech Synthesis API (`speechSynthesis`)
- **UI State Machine**: 
  - `idle` → Blue gradient orb
  - `listening` → Green pulsing animation
  - `processing` → Orange spinning animation
  - `speaking` → Purple pulsing animation

**Why no frameworks?**
- Zero dependencies = faster load, no npm vulnerabilities
- Native browser APIs = better performance
- Simple deployment = just open `index.html`

#### 2. **Backend** (FastAPI)
- **Role**: Thin orchestration layer
- **Responsibilities**:
  - Receive voice commands from frontend
  - Maintain conversation context (SQLite)
  - Forward to n8n workflow
  - Clean response for TTS (remove markdown)
  - Return structured data to frontend

**Key Features:**
- Context memory: Stores last N interactions
- Origin/destination extraction for maps
- Markdown cleanup for clean voice output
- CORS enabled for browser access

**Endpoints:**
```python
POST /api/text/process
  Body: { "message": "user command" }
  Returns: { 
    "response": "cleaned text for TTS",
    "origin": "location A",
    "destination": "location B",
    "service": "maps|gmail|general"
  }

GET /api/services/status
  Returns: Service availability status
```

#### 3. **n8n Workflow** (Intelligence Engine)
- **Role**: Decision-making and API orchestration
- **Architecture**:

```
Webhook Trigger
    │
    ▼
Parse User Request
    │
    ▼
Gemini Decision Maker ◄─── 🧠 THE BRAIN
    │                       Semantic understanding
    ├─ Service: "gmail|maps|general"
    ├─ Action: "summarize|send|distance"
    ├─ Parameters: { origin, destination, to, subject }
    └─ Summary: "brief description"
    │
    ▼
Router (based on service)
    │
    ├──▶ [Gmail Path]
    │      ├─ Get Emails (Gmail API)
    │      ├─ Gemini Summarize
    │      └─ Return Summary
    │
    ├──▶ [Maps Path]
    │      ├─ Distance Matrix API (driving, walking, transit)
    │      ├─ Format Response
    │      ├─ Gemini Conversational Reply
    │      └─ Return with origin/destination
    │
    └──▶ [General Path]
           └─ Gemini General Response
```

**Why n8n?**
- Visual workflow editor (no code deployment)
- Built-in API node templates
- Easy to add new services
- Self-hosted = data privacy

#### 4. **Gemini LLM** (Google)
- **Model**: Gemini 1.5 Pro/Flash
- **Role**: Natural language understanding and decision routing
- **Tasks**:
  1. **Intent Classification**: Determine which service to use
  2. **Parameter Extraction**: Pull structured data from natural text
  3. **Response Generation**: Create conversational replies

**Example Flow:**
```
User: "How far is New Delhi to Rajiv Chowk?"

Gemini Analyzes:
{
  "service": "maps",
  "action": "distance",
  "origin": "New Delhi",
  "destination": "Rajiv Chowk",
  "summary": "User wants distance information"
}

n8n Routes: → Maps Distance Matrix API
           → Calculates driving/walking/transit times
           → Gemini formats conversational response
           
Response: "From New Delhi to Rajiv Chowk:
           By car: 3.4 km in 9 minutes
           Walking: 3.4 km in 41 minutes
           By transit: 3.4 km in 11 minutes
           Say give me directions to open Google Maps."
```

### Data Flow Example

**User Command:** "Summarize my latest emails"

```
1. Frontend (Voice Recognition)
   ├─ Captures: "Summarize my latest emails"
   └─ POST → http://localhost:8000/api/text/process

2. Backend (FastAPI)
   ├─ Loads context from SQLite (last 5 interactions)
   ├─ POST → http://localhost:5678/webhook/nexus-agent
   └─ Body: { "user_request": "Summarize...", "context": [...] }

3. n8n Workflow
   ├─ Gemini Decision Maker:
   │   {
   │     "service": "gmail",
   │     "action": "summarize",
   │     "parameters": {},
   │     "summary": "User wants email summary"
   │   }
   ├─ Router → Gmail Path
   ├─ Gmail: Get Emails node (last 5)
   ├─ Gemini Summarizer: Creates summary
   └─ Returns: { "text": "You have 3 new emails..." }

4. Backend (Response Processing)
   ├─ Strips markdown (**bold** → bold)
   ├─ Stores in memory
   └─ Returns: { "response": "You have 3 new emails..." }

5. Frontend (TTS)
   ├─ Calls speechSynthesis.speak()
   ├─ Updates UI to 'speaking' state
   └─ Purple pulsing animation
```

## 🛠️ Technology Stack

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Animations, gradients, responsive design
- **Vanilla JavaScript** - No frameworks
- **Web Speech API** - Voice recognition (Chrome/Edge)
- **Speech Synthesis API** - Text-to-speech

### Backend
- **Python 3.10+**
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **SQLite** - Embedded database for memory
- **httpx** - Async HTTP client for n8n calls
- **python-dotenv** - Environment configuration

### Automation & AI
- **n8n** - Workflow automation (self-hosted)
### Automation & AI
- **n8n** - Workflow automation (self-hosted)
- **Docker Compose** - Container orchestration
- **Google Gemini** - LLM for decision-making

### External APIs
- **Gmail API** - Email management
- **Google Maps Distance Matrix API** - Route calculation
- **Google Maps Directions** - Turn-by-turn navigation

## 📂 Project Structure

```
NEXUS Labs/
├── backend/
│   ├── app/
│   │   ├── main_intelligent.py     # ✅ Main FastAPI app
│   │   ├── config.py               # Environment configuration
│   │   ├── database.py             # SQLite setup
│   │   ├── models.py               # Database models
│   │   └── memory/
│   │       ├── manager.py          # Conversation memory
│   │       └── context.py          # Context handling
│   ├── requirements.txt
│   ├── .env.template              # API keys template
│   └── Dockerfile
│
├── frontend/
│   ├── index.html                  # Voice-only interface
│   ├── css/
│   │   └── style.css              # Visual states, animations
│   └── js/
│       ├── app.js                 # Service status
│       ├── vapi.js                # Voice recognition & TTS
│       └── ui.js                  # UI helpers
│
├── n8n-workflows/
│   └── nexus-intelligent-agent.json  # ✅ Main workflow
│
├── docker-compose.yml              # n8n container setup
└── README.md                       # This file
```

## 🚀 Setup Instructions

### Prerequisites

- **Python 3.10+** ([Download](https://python.org))
- **Node.js 18+** ([Download](https://nodejs.org))
- **Docker Desktop** ([Download](https://docker.com)) - For n8n
- **Chrome or Edge** - For Web Speech API
- **Google Gemini API Key** - [Get here](https://makersuite.google.com/app/apikey)

### Step 1: Clone Repository

```powershell
git clone https://github.com/ankitkr9911/Nexus-Labs.git
cd "Nexus Labs"
```

### Step 2: Backend Setup

```powershell
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.template .env
notepad .env  # Add your API keys (see below)

# Initialize database
python -c "from app.database import init_db; init_db()"

# Start backend
python -m uvicorn app.main_intelligent:app --reload --host 0.0.0.0 --port 8000
```

#### Required API Keys in `.env`:

```env
# Google Gemini (REQUIRED - for n8n workflow)
GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here

# Gmail API (Optional - for email features)
GOOGLE_CLIENT_ID=your_gmail_client_id
GOOGLE_CLIENT_SECRET=your_gmail_client_secret

# Google Maps (Optional - for navigation features)
GOOGLE_MAPS_API_KEY=your_maps_api_key

# Backend Configuration
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
N8N_WEBHOOK_URL=http://localhost:5678/webhook/nexus-agent
```

**Where to get API keys:**
- **Gemini**: https://makersuite.google.com/app/apikey
- **Gmail**: https://console.cloud.google.com/apis/credentials
- **Maps**: https://console.cloud.google.com/google/maps-apis

### Step 3: n8n Setup (Docker)

```powershell
# Start n8n container
docker-compose up -d

# Check if running
docker ps  # Should show 'nexus-n8n' container

# Access n8n
# Open browser → http://localhost:5678
```

#### Import Workflow:

1. **Create account** (first time only)
2. Click **"Workflows"** → **"Import from File"**
3. Select: `n8n-workflows/nexus-intelligent-agent.json`
4. **Add Gemini Credential:**
   - Click any "Gemini" node
   - Click "Credential to connect with"
   - "Create new credential"
   - Paste your Gemini API key
   - Save
5. **Activate workflow:**
   - Toggle switch at top-right (should turn green)
6. **Test webhook:**
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:5678/webhook/nexus-agent" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"user_request": "Hello"}'
   ```

### Step 4: Frontend Setup

```powershell
cd frontend

# Option 1: Python HTTP server
python -m http.server 3000

# Option 2: Node.js http-server
npx http-server -p 3000

# Access: http://localhost:3000
```

### Step 5: Test the System

1. **Open browser**: http://localhost:3000
2. **Allow microphone** access when prompted
3. **Click the voice button** (🎤)
4. **Say**: "How far is New Delhi to Rajiv Chowk?"
5. **AI should respond** with distance and time options
6. **Say**: "Give me directions"
7. **Google Maps opens** with route

## 🎯 Key Features

### 1. Voice-Only Interface

**No text input, no chat history - just natural conversation**

- Gemini-like visual orb with state animations
- Real-time visual feedback (idle → listening → processing → speaking)
- Clean, distraction-free UI
- Automatically opens Google Maps for navigation

### 2. Multi-Mode Route Calculation

**For maps queries, get ALL travel options:**

```
User: "How far is Location A to Location B?"

Response:
- 🚗 By car: 3.4 km in 9 minutes
- 🚶 Walking: 3.4 km in 41 minutes
- 🚇 By transit: 3.4 km in 11 minutes

Say give me directions to open Google Maps.
```

### 3. Natural Language Understanding

**All these variations work:**

Maps:
- "How far is New Delhi to Rajiv Chowk?"
- "Distance from my home to office"
- "How long to get to downtown?"

Gmail:
- "Check my emails"
- "What's in my inbox?"
- "Any new messages?"
- "Summarize latest emails"

The LLM handles semantic variations automatically!

### 4. Context-Aware Conversations

```
User: "How far is New Delhi to Rajiv Chowk?"
AI: [Gives distance options]

User: "Give me directions"
AI: [Opens Google Maps with stored origin/destination]
```

Backend stores location data from previous query.

### 5. Progressive Web Enhancement

- Works offline (after first load)
- No external dependencies
- Fast load times (<1 second)
- Mobile-responsive design

## 🧪 Testing & Debugging

### Test Commands

**Maps:**
```
"How far is New Delhi to Rajiv Chowk?"
"Distance from Connaught Place to India Gate"
"Give me directions"  (after a maps query)
```

**Gmail:**
```
"Check my emails"
"Summarize my inbox"
"What's in my mailbox?"
```

### Debug Mode

**Check Backend Logs:**
```powershell
# Backend terminal shows:
INFO: 📝 User command: How far is...
INFO: 🚀 Calling n8n workflow
INFO: ✅ n8n response received
```

**Check n8n Workflow:**
1. Go to http://localhost:5678
2. Click "Executions" tab
3. See each request with full data

**Browser Console:**
```javascript
// Open DevTools (F12) → Console
// Check for errors
// Voice recognition logs: 🎤 Listening...
// Processing logs: 📍 Stored location data
```

### Common Issues

**1. "No microphone access"**
- Chrome/Edge only (Firefox doesn't support `webkitSpeechRecognition`)
- Click "Allow" when prompted
- Check browser settings → Privacy → Microphone

**2. "n8n workflow not responding"**
```powershell
# Check if n8n is running
docker ps

# Restart n8n
docker-compose restart

# Check logs
docker logs nexus-n8n
```

**3. "Backend can't reach n8n"**
- Check both are running: `netstat -ano | Select-String "8000|5678"`
- Verify n8n webhook URL in `.env`
- Test directly: 
  ```powershell
  Invoke-RestMethod -Uri "http://localhost:5678/webhook/nexus-agent" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"user_request": "test"}'
  ```

**4. "Voice not working"**
- Only Chrome/Edge supported
- Check microphone permissions in browser
- Try: chrome://settings/content/microphone

**5. "Empty response from n8n"**
- Check Gemini API key is set in n8n credential
- Check workflow is activated (green toggle at top)
- Look at n8n execution logs for errors

## 📊 Technical Decisions & Rationale

### Why Web Speech API instead of LiveKit/VAPI?

**Tried:**
- **LiveKit Agents**: 401 authentication errors (Agent API not enabled on free tier)
- **VAPI SDK**: CommonJS module, not browser-compatible

**Chose Web Speech API:**
- ✅ Browser-native (no dependencies)
- ✅ Works offline after first load
- ✅ Zero configuration
- ✅ Reliable in Chrome/Edge
- ❌ Chrome/Edge only (acceptable tradeoff)

### Why n8n for orchestration?

**Alternatives considered:**
- **Langchain**: Too much code for simple routing
- **Direct API calls**: Hard to maintain, no visual debugging
- **Cloud functions**: Vendor lock-in, cold starts

**Why n8n:**
- ✅ Visual workflow editor
- ✅ Built-in API nodes (Gmail, HTTP, etc.)
- ✅ Self-hosted = data privacy
- ✅ Easy to modify without redeploying backend
- ✅ Execution logs for debugging

### Why Gemini LLM?

**Alternatives:**
- **GPT-4**: Excellent but expensive ($0.03/1K tokens)
- **Claude**: Good but API access limited
- **Local LLM (Llama 2)**: Slow inference, needs GPU

**Chose Gemini:**
- ✅ Free tier (60 requests/min)
- ✅ Fast responses (<2 seconds)
- ✅ Excellent JSON parsing
- ✅ Good at intent classification
- ✅ Handles Indian names/places well

## 🔒 Security & Privacy

### Self-Hosted Architecture

**Data never leaves your infrastructure:**
- n8n runs locally (Docker)
- Backend runs locally (Python)
- Frontend runs in browser

**Only external calls:**
- Google Gemini API (for LLM)
- Gmail API (if configured)
- Maps API (if configured)

### API Key Safety

**Never commit real keys:**
- Use `.env.template` with placeholders
- `.env` is in `.gitignore`
- n8n credentials encrypted in database

## 📈 Performance Metrics

**End-to-end latency:**

```
Voice Command → Response
├─ Voice Recognition: ~500-1000ms
├─ Backend: ~50ms
├─ n8n + Gemini: ~2000ms
├─ Backend Cleanup: ~20ms
└─ TTS: ~100ms

Total: ~3 seconds
```

## 🚀 Future Enhancements

### Short-term
- [ ] WhatsApp integration
- [ ] Voice wake word ("Hey NEXUS")
- [ ] Multi-language support
- [ ] Mobile PWA

### Long-term
- [ ] Multi-user authentication
- [ ] Custom workflows
- [ ] Desktop app (Electron)
- [ ] Plugin marketplace

## 🤝 Contributing

Contributions welcome!

### Adding a New Service

1. Update n8n workflow (add nodes)
2. Update Gemini prompt
3. No backend changes needed!

## 📄 License

MIT License - Copyright (c) 2026 NEXUS Labs

## 🙏 Acknowledgments

- **Google Gemini** - Natural language understanding
- **n8n.io** - Workflow automation
- **FastAPI** - Python web framework
- **Web Speech API** - Browser voice capabilities

GitHub: [@ankitkr9911](https://github.com/ankitkr9911)

---

**Last Updated:** February 8, 2026  
**Version:** 3.0  
**Status:** Active Development  

---

*"Voice is the future of human-computer interaction. NEXUS makes it accessible, private, and extensible."*
