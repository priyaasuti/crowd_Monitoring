"""
Test Grok API loading - exactly like event_analysis.py does it
"""
import os
from pathlib import Path

print("Step 1: Import dotenv")
try:
    from dotenv import load_dotenv
    print("✅ dotenv imported successfully")
except ImportError:
    print("❌ dotenv NOT installed!")
    print("   Run: pip install python-dotenv")
    exit(1)

print("\nStep 2: Load .env file")
env_file = Path(__file__).resolve().parent / ".env"
print(f"   .env path: {env_file}")
print(f"   .env exists: {env_file.exists()}")

if env_file.exists():
    with open(env_file, 'r') as f:
        content = f.read()
        print(f"\n   .env content:")
        for line in content.split('\n'):
            if line.strip():
                if 'API' in line:
                    key = line.split('=')[0]
                    print(f"   Found key: {key}")
                else:
                    print(f"   {line[:50]}...")

load_dotenv(dotenv_path=str(env_file), override=True)
print("✅ dotenv loaded")

print("\nStep 3: Read API key")
api_key = os.getenv("API")
print(f"   API key found: {bool(api_key)}")
print(f"   API key length: {len(api_key) if api_key else 0}")

if api_key:
    print(f"   ✅ SUCCESS! API key is: {api_key[:40]}...")
else:
    print(f"   ❌ FAILED! API key not loaded")
    print("\n   Debugging: All environment variables with 'API':")
    for key, value in os.environ.items():
        if 'API' in key.upper():
            print(f"      {key}={value[:40]}...")
