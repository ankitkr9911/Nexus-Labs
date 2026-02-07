"""
Test script to verify LiveKit Voice Agent setup
Run this to check if all components are properly configured
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
env_paths = [
    '.env',
    'backend/.env',
    'XRAY_Agent/.env'
]

print("=" * 60)
print("  NEXUS LiveKit Voice Agent - Setup Verification")
print("=" * 60)
print()

# Load env files
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Loaded: {env_path}")

print()
print("Checking Required Environment Variables...")
print("-" * 60)

# Required variables
required_vars = {
    'LIVEKIT_URL': 'LiveKit WebSocket URL',
    'LIVEKIT_API_KEY': 'LiveKit API Key',
    'LIVEKIT_API_SECRET': 'LiveKit API Secret',
    'DEEPGRAM_API_KEY': 'Deepgram Speech-to-Text',
    'OPENAI_API_KEY': 'OpenAI GPT-4 & TTS',
    'N8N_WEBHOOK_BASE_URL': 'n8n Webhook Base URL'
}

all_present = True
for var, description in required_vars.items():
    value = os.getenv(var)
    if value:
        # Mask sensitive parts
        if 'KEY' in var or 'SECRET' in var:
            display = value[:10] + '...' + value[-5:] if len(value) > 15 else value[:5] + '...'
        else:
            display = value
        print(f"✓ {var:25} = {display}")
    else:
        print(f"✗ {var:25} = NOT SET")
        all_present = False

print()
print("Checking Python Dependencies...")
print("-" * 60)

dependencies = [
    ('livekit', 'LiveKit SDK'),
    ('livekit.agents', 'LiveKit Agents'),
    ('livekit.plugins.deepgram', 'Deepgram Plugin'),
    ('livekit.plugins.openai', 'OpenAI Plugin'),
    ('livekit.plugins.silero', 'Silero VAD Plugin'),
    ('loguru', 'Logging Library'),
    ('aiohttp', 'Async HTTP Client')
]

all_installed = True
for module, description in dependencies:
    try:
        __import__(module)
        print(f"✓ {description:30} - Installed")
    except ImportError:
        print(f"✗ {description:30} - NOT INSTALLED")
        all_installed = False

print()
print("Checking Services...")
print("-" * 60)

# Check n8n
import httpx
import asyncio

async def check_services():
    services_ok = True
    
    # Check n8n
    try:
        n8n_url = os.getenv('N8N_WEBHOOK_BASE_URL', 'http://localhost:5678/webhook')
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{n8n_url}/nexus-agent",
                json={"user_request": "health check", "context": ""}
            )
            if response.status_code == 200:
                print(f"✓ n8n Workflow      - Running at {n8n_url}")
            else:
                print(f"⚠ n8n Workflow      - Responded but returned {response.status_code}")
                services_ok = False
    except Exception as e:
        print(f"✗ n8n Workflow      - NOT ACCESSIBLE ({str(e)[:40]}...)")
        services_ok = False
    
    # Check backend
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/api/health")
            if response.status_code == 200:
                print("✓ Backend API       - Running at http://localhost:8000")
            else:
                print(f"⚠ Backend API       - Responded but returned {response.status_code}")
                services_ok = False
    except Exception as e:
        print(f"✗ Backend API       - NOT RUNNING (Start with: uvicorn app.main_intelligent:app --reload)")
        services_ok = False
    
    return services_ok

services_ok = asyncio.run(check_services())

print()
print("=" * 60)
print("  Summary")
print("=" * 60)

if all_present and all_installed and services_ok:
    print("✅ ALL CHECKS PASSED!")
    print()
    print("Your NEXUS Voice Agent is ready to use!")
    print()
    print("Next steps:")
    print("1. Start the voice agent:")
    print("   python voice_agent/nexus_livekit_agent.py")
    print()
    print("2. Open the frontend:")
    print("   Open frontend/index.html in your browser")
    print()
    print("3. Click 'Talk to NEXUS Voice Agent' button")
    print()
else:
    print("⚠️  SETUP INCOMPLETE")
    print()
    if not all_present:
        print("❌ Environment Variables Missing")
        print("   → Copy LiveKit credentials from XRAY_Agent/.env to backend/.env")
        print()
    if not all_installed:
        print("❌ Python Dependencies Missing")
        print("   → Run: pip install -r voice_agent/livekit_requirements.txt")
        print()
    if not services_ok:
        print("❌ Services Not Running")
        print("   → Start Backend: cd backend && uvicorn app.main_intelligent:app --reload")
        print("   → Start n8n: n8n start")
        print()
    
    print("See LIVEKIT_SETUP.md for detailed instructions")

print("=" * 60)
