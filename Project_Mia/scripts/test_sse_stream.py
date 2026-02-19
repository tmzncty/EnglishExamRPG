import requests
import json
import sys

# Ensure unicode output works correctly on Windows console
sys.stdout.reconfigure(encoding='utf-8')

url = "http://localhost:8000/api/mia/interact"
payload = {
    "context_type": "chat",
    "conversation_id": None,
    "context_data": {
        "message": "测试流式传输，收到请回复",
        "attach_context": False, 
        "rpg_mode": False,
        "history": []
    }
}

print("🚀 发起请求...")
try:
    with requests.post(url, json=payload, stream=True, timeout=10) as r:
        r.raise_for_status()
        print("✅ 连接成功，开始接收数据流：")
        # Use iter_lines directly, requests handles decoding if stream=True and iter_lines(decode_unicode=True) is used,
        # otherwise decode manually. User code provided manual decode.
        for line in r.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                print(f"📦 收到数据块: {decoded_line}")
except Exception as e:
    print(f"❌ 请求失败: {e}")
