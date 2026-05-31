"""
Verify Grok API configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).resolve().parent / ".env"
print(f"Loading .env from: {env_path}")
print(f"File exists: {env_path.exists()}")

load_dotenv(dotenv_path=str(env_path))

# Check API key
api_key = os.getenv("API")
print(f"\n{'='*60}")
print("🔍 GROK API CONFIGURATION CHECK")
print(f"{'='*60}")
print(f"API Key found: {bool(api_key)}")

if api_key:
    print(f"API Key length: {len(api_key)} characters")
    print(f"API Key starts with: {api_key[:20]}...")
    print(f"✅ GROK API IS CONFIGURED!")
else:
    print(f"❌ GROK API KEY NOT FOUND!")
    print("Make sure your .env file has:")
    print("   API=xai-your-api-key-here")

# Check requests library
print(f"\n{'='*60}")
print("📦 CHECKING DEPENDENCIES")
print(f"{'='*60}")

try:
    import requests
    print(f"✅ requests library: INSTALLED (v{requests.__version__})")
except ImportError:
    print("❌ requests library: NOT INSTALLED")
    print("   Run: pip install requests")

# Test Grok API connection
if api_key:
    print(f"\n{'='*60}")
    print("🌐 TESTING GROK API CONNECTION")
    print(f"{'='*60}")
    
    import requests
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "grok-2",
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello from Grok' in 5 words.",
            }
        ],
        "max_tokens": 50,
    }
    
    try:
        print("Sending test request to Grok API...")
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ Grok API RESPONDING!")
            print(f"Response: {message}")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.Timeout:
        print("⚠️  Request timed out (>10s)")
    except Exception as e:
        print(f"❌ Connection error: {e}")

print(f"\n{'='*60}")
