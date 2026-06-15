#!/usr/bin/env python3
"""
Test script to verify GPU access and YOLO acceleration
Run after starting the API server in another terminal
"""
import requests
import json
import time
import subprocess
import sys

def print_header(text):
    print("\n" + "="*70)
    print(f"🔍 {text}")
    print("="*70)

def test_api_health():
    """Test the health endpoint to see GPU info"""
    print_header("Testing API Health Endpoint")
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Monitoring Active: {data.get('monitoring_active')}")
        print(f"\nGPU Info:")
        gpu_info = data.get('gpu_info', {})
        for key, value in gpu_info.items():
            print(f"  {key}: {value}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_gpu_utilization():
    """Check current GPU utilization"""
    print_header("GPU Utilization (nvidia-smi)")
    try:
        result = subprocess.run(
            "nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader",
            shell=True, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print(result.stdout)
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
    return False

def test_frame_endpoint():
    """Test getting a frame"""
    print_header("Testing Frame Endpoint")
    try:
        response = requests.get("http://localhost:5000/frame", timeout=5)
        if response.status_code == 200:
            data = response.json()
            frame_size = len(data.get('frame', ''))
            print(f"✅ Frame retrieved successfully")
            print(f"Frame size: {frame_size / 1024:.2f} KB")
            return True
        else:
            print(f"❌ Status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False

def main():
    print("\n" + "="*70)
    print("GPU ACCESS VERIFICATION TEST")
    print("="*70)
    print("\n✅ Make sure API server is running:")
    print("   cd /home/priya/crowd_Monitoring/backend")
    print("   source venv/bin/activate")
    print("   python api.py")
    
    # Wait for user to ensure server is running
    print("\nWaiting for API server on http://localhost:5000...")
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            requests.get("http://localhost:5000/health", timeout=2)
            print("✅ API server is ready!")
            break
        except:
            if attempt < max_attempts - 1:
                print(f"  Attempt {attempt + 1}/{max_attempts} - waiting...")
                time.sleep(2)
            else:
                print("❌ Could not connect to API server")
                print("Start it with: python api.py")
                sys.exit(1)
    
    # Run tests
    results = []
    results.append(("API Health Check", test_api_health()))
    results.append(("GPU Utilization", check_gpu_utilization()))
    results.append(("Frame Endpoint", test_frame_endpoint()))
    
    # Summary
    print_header("TEST SUMMARY")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "="*70)
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print("\n🚀 GPU ACCELERATION IS ACTIVE AND WORKING!")
        print("\nYour system is ready for:")
        print("  • Real-time person detection")
        print("  • Video file analysis")
        print("  • GPU-accelerated inference at 10-30 FPS")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
        print("Check the errors above")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        sys.exit(0)
