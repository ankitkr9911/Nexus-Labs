# 🎯 NEXUS AI - Voice-First Intelligent Automation Platform

## 🧠 v2.0 - LLM-Driven Intelligence

**Voice-controlled automation system with Gemini LLM decision-making**

### What Makes This Special?

✅ **True AI Intelligence** - Gemini LLM makes ALL decisions in n8n workflows  
✅ **Natural Language** - Understands variations, no hardcoded patterns  
✅ **Context-Aware** - Remembers conversations, resolves references  
✅ **Self-Hosted** - Full control, no cloud dependencies  
✅ **Voice-First** - Speak naturally, AI understands intent

### Architecture

```
User → FastAPI → n8n → 🧠 Gemini LLM (decides) → Gmail/Maps/Spotify
                          ↑
                    THE BRAIN
              (All intelligence here)
```

## Tech Stack

- **Frontend**: HTML/CSS/JavaScript with voice capture
- **Backend**: FastAPI (Python 3.10+) - Pass-through + memory
- **Intelligence**: Google Gemini 1.5 Pro/Flash (LLM decision-maker)
- **Voice**: Deepgram STT + Web Speech API fallback
- **Database**: SQLite (long-term memory)
- **Automation**: Self-hosted n8n with intelligent workflows
- **APIs**: Gmail, Google Maps, Spotify

## Project Structure

```
NEXUS Labs/
├── backend/
│   ├── app/
│   │   ├── main_intelligent.py     # ✅ USE THIS - Intelligent version
│   │   ├── main.py                 # ❌ Old pattern-based version
│   │   ├── config.py               # Configuration & env vars
│   │   ├── database.py             # SQLite setup
│   │   ├── models.py               # Database models
│   │   ├── memory/
│   │   │   └── manager.py          # Long-term memory storage
│   │   └── voice/
│   │       └── deepgram.py         # Voice transcription
│   ├── requirements.txt
│   └── .env.example
│
├── n8n-workflows/
│   ├── nexus-intelligent-agent.json  # ✅ USE THIS - Smart workflow
│   ├── gmail-reply.json              # ❌ Old dumb workflow
│   ├── gmail-summarize.json          # ❌ Old dumb workflow
│   ├── maps-distance.json            # ❌ Old dumb workflow
│   └── spotify-control.json          # ❌ Old dumb workflow
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js                  # Main application logic
│       ├── voice.js                # Voice capture
│       └── ui.js                   # UI updates
│
└── docs/
    ├── SETUP_MANUAL.md             # ✅ Complete setup guide
    ├── N8N_SELFHOST_GUIDE.md       # ✅ n8n deployment
    ├── ARCHITECTURE_V2.md          # ✅ Technical deep-dive
    ├── VISUAL_ARCHITECTURE.md      # ✅ Flow diagrams
    ├── QUICK_START_CHECKLIST.md    # ✅ Setup checklist
    ├── IMPLEMENTATION_V2_COMPLETE.md  # ✅ What's been built
    └── TROUBLESHOOTING.md          # ✅ Debug guide
```
│   └── assets/
│       └── images/
├── n8n-workflows/
│   ├── gmail-summarize.json
│   ├── gmail-reply.json
│   ├── maps-distance.json
│   └── spotify-control.json
└── docs/
    ├── SETUP.md
    └── DEMO_COMMANDS.md
```

## 🚀 Quick Start

### Step 1: Backend Setup (15 min)

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
uv pip install -r requirements.txt

# Configure
copy .env.example .env
notepad .env  # Add API keys

# Initialize database
python -c "from app.database import init_db; init_db()"

# Run intelligent backend
python -m uvicorn app.main_intelligent:app --reload --port 8000
```

### Step 2: n8n Setup (20 min)

```powershell
# Install n8n
npm install -g n8n

# Start n8n
n8n start

# Then:
# 1. Go to http://localhost:5678
# 2. Import: n8n-workflows/nexus-intelligent-agent.json
# 3. Add Gemini API credential (REQUIRED)
# 4. Activate workflow (toggle switch)
```

### Step 3: Frontend (5 min)

```powershell
cd frontend
python -m http.server 3000

# Access: http://localhost:3000
```

## 📚 Documentation

**Start Here:**
- [QUICK_START_CHECKLIST.md](QUICK_START_CHECKLIST.md) - Step-by-step checklist
- [SETUP_MANUAL.md](SETUP_MANUAL.md) - Complete setup with uv
- [N8N_SELFHOST_GUIDE.md](N8N_SELFHOST_GUIDE.md) - n8n installation

**Architecture:**
- [ARCHITECTURE_V2.md](ARCHITECTURE_V2.md) - Technical deep-dive
- [VISUAL_ARCHITECTURE.md](VISUAL_ARCHITECTURE.md) - Flow diagrams
- [IMPLEMENTATION_V2_COMPLETE.md](IMPLEMENTATION_V2_COMPLETE.md) - What's built

**Help:**
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Debug guide

## 🎯 Key Features

### Intelligent Decision-Making

```
User: "Check my emails from yesterday"

Gemini LLM in n8n:
├─ Understands: User wants email summary
├─ Decides: Route to Gmail
├─ Extracts: time_range = "yesterday"
└─ Executes: Gmail API with filters

No hardcoded patterns!
```

### Natural Language Understanding

All these work:
- "Check my emails"
- "What's in my inbox?"
- "Any new messages?"
- "Show me my mail"

Gemini understands the intent naturally!

### Context Memory

```
User: "Summarize my emails"
Bot: "You have 3 emails..."

User: "Reply to the first one"
Bot: *Understands "first one" from context*
```

## 🔑 Required API Keys

1. **Google Gemini API** (REQUIRED) - The brain!
   - Get: https://makersuite.google.com/app/apikey
   
2. **Deepgram API** (optional) - Voice transcription
   - Get: https://deepgram.com
   
3. **Gmail OAuth** (optional) - Email features
   - Setup: Google Cloud Console
   
4. **Spotify OAuth** (optional) - Music control
   - Setup: Spotify Developer Dashboard
   
5. **Google Maps API** (optional) - Directions
   - Setup: Google Cloud Console

## 🧪 Test Commands

- "Check my emails" / "What's in my inbox?" / "Any new messages?"
- "How far is New York from Boston?"
- "Play some relaxing music"
- "Summarize my emails" then "Reply to the first one"

All variations work - Gemini understands naturally!

## 🆘 Troubleshooting

**Backend won't start:**
- Check venv activated: `(venv)` in prompt
- Reinstall: `uv pip install -r requirements.txt --force-reinstall`

**n8n workflow not responding:**
- Check Gemini API key is set
- Check workflow is activated (green toggle)
- View execution logs in n8n

**Frontend can't connect:**
- Check CORS in `backend/.env`
- Restart backend after changes

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for complete guide.

## 🎓 How It Works

```
1. User speaks or types
2. FastAPI receives request
3. Fetches context from memory
4. Calls n8n webhook
5. 🧠 Gemini LLM analyzes request
6. Decides: service + action + parameters
7. n8n routes to appropriate API
8. Result returned to user
9. Stored in memory for context
```

**The key difference:** Gemini makes ALL decisions, not hardcoded patterns!

## 📊 Comparison

| Feature | v1.0 (Pattern) | v2.0 (Gemini) |
|---------|---------------|---------------|
| Understanding | Exact matches only | Semantic understanding |
| Variations | Must code each | Handles naturally |
| Context | Limited | Full conversation |
| Intelligence | ❌ Rules-based | ✅ True AI |

## 🏗️ Tech Architecture

- **FastAPI**: Lightweight pass-through + memory
- **n8n**: Workflow orchestration
- **Gemini LLM**: Decision-making brain
- **SQLite**: Long-term memory
- **Deepgram**: Voice transcription

## 🎯 Use Cases

- **Email Management**: "Summarize my emails", "Reply to that"
- **Navigation**: "How far is the office?", "Give me directions"
- **Music Control**: "Play some jazz", "Pause music"
- **Context Commands**: "Reply to the first one", "More about that"

## 📈 Future Extensions

Want to add WhatsApp?
1. Add WhatsApp node to n8n
2. Update Gemini prompt with WhatsApp actions
3. Done! No Python code changes

## 🤝 Contributing

This is a hackathon demo project. Feel free to:
- Add more services to n8n workflow
- Enhance Gemini prompts
- Improve UI/UX
- Add more memory features

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- Google Gemini for LLM capabilities
- n8n for workflow automation
- Deepgram for voice transcription
- FastAPI for Python backend

---

**Built with ❤️ for intelligent automation**

*The intelligence is in Gemini (n8n), not hardcoded patterns!*

## Configuration

All API keys and credentials go in `backend/.env`:

```env
# Deepgram
DEEPGRAM_API_KEY=your_key_here

# Google APIs
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_MAPS_API_KEY=your_maps_key

# Spotify
SPOTIFY_CLIENT_ID=your_spotify_id
SPOTIFY_CLIENT_SECRET=your_spotify_secret

# n8n
N8N_WEBHOOK_URL=http://localhost:5678/webhook
```

## License

Demo project for hackathon submission.
