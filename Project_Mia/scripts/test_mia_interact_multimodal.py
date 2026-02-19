import requests
import json
import sseclient

# Configuration
BASE_URL = "http://localhost:8000/api/mia/interact"
Q_ID = "2023-eng1-writing-partB" # Assuming this q_id has an image and user history

def test_mia_interact():
    print(f"🚀 Testing Mia Interact Multimodal for Q_ID: {Q_ID}")
    
    payload = {
        "context_type": "chat",
        "context_data": {
            "message": "我不理解这道题的图片什么意思，还有我的作文哪里写得不好？",
            "q_id": Q_ID,
            "attach_context": True,
            "rpg_mode": False
        }
    }
    
    try:
        response = requests.post(BASE_URL, json=payload, stream=True)
        if response.status_code != 200:
             print(f"❌ HTTP Error {response.status_code}: {response.text}")
             return

        print(f"✅ Response Status: {response.status_code}")
        
        full_reply = ""
        print("\n--- Mia's Stream Response (Raw) ---")
        try:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    print(decoded_line)
                    if decoded_line.startswith("data:"):
                        try:
                            data = json.loads(decoded_line[5:])
                            if "mia_reply" in data:
                                full_reply += data["mia_reply"]
                        except:
                            pass
        except Exception as e:
             print(f"\n❌ Stream Error: {e}")
             
        print("\n\n✅ Stream completed.")
        
        # Simple verification checks
        if "图片" in full_reply or "作文" in full_reply or "DEBUG" in full_reply:
             print("✅ Keyword found in response.")
        else:
             print("⚠️ Warning: Keywords not found.")

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_mia_interact()
