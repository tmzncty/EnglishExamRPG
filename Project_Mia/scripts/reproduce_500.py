import requests
import json

BASE_URL = "http://localhost:8000"

def test_subjective_submit():
    print("🚀 Triggering 'submit_subjective' to reproduce 500 error...")
    
    payload = {
        "q_id": "2023-eng1-translation-q46",
        "answer": "This is a test translation answer.",
        "section_type": "translation"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/api/exam/submit_subjective", json=payload)
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 500:
            print("✅ 500 Error Reproduced!")
        else:
            print("❌ Did NOT reproduce 500.")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_subjective_submit()
