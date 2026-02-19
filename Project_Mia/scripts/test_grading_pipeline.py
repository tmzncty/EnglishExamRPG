import requests
import json
import base64
import sys
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / 'backend' / '.env'
load_dotenv(dotenv_path=env_path, override=True)
print(f"🔑 AI_PROVIDER: {os.getenv('AI_PROVIDER')}")

# Ensure unicode output works correctly on Windows console
sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://localhost:8000/api/exam/submit_subjective"
HEADERS = {"Content-Type": "application/json"}

def print_result(title, payload):
    print(f"\n🚀 Running Test Case: {title}")
    try:
        resp = requests.post(API_URL, json=payload, headers=HEADERS, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        print(f"✅ Status Code: {resp.status_code}")
        print(f"💰 Score: {data.get('score')}/{data.get('max_score')}")
        print(f"🐱 Mia Feedback: {data.get('mia_feedback')}")
        print(f"📝 Detailed Analysis (Preview): {data.get('detailed_analysis')[:100]}...")
        
        # Validation
        if "喵" in str(data.get("mia_feedback", "")):
             print("✨ Persona Check: PASSED (Contains '喵')")
        else:
             print("⚠️ Persona Check: FAILED (Missing '喵')")
             
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Server Response: {e.response.text}")

def test_translation():
    # Test Case 1: Translation with errors - REAL LLM CHECK
    # User requirement: "People is very much good in science." -> Must correct "is" to "are"
    payload = {
        "q_id": "2010-text1-trans-01", 
        "section_type": "translation",
        "answer": "People is very much good in science."
    }
    print_result("Translation (Bad Grammar Check)", payload)

def test_writing_with_image():
    # Test Case 2: Writing B (Multimodal if backend has image, otherwise text only)
    # We use a known q_id. If database is empty, it might default to text-only grading.
    payload = {
        "q_id": "2010-writing-b", 
        "section_type": "writing_b",
        "answer": "Looking at the drawing, we can see a hot pot containing many cultural elements. This symbolizes cultural integration. In my opinion, we should accept different cultures while keeping our own traditions. The world is a village."
    }
    print_result("Writing B (Multimodal Check)", payload)

if __name__ == "__main__":
    test_translation()
    test_writing_with_image()
