"""检查finish_reason并调整max_tokens"""
import requests
import json

API_KEY = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
BASE_URL = "https://api.vectorengine.ai/v1"

prompt = """你是Mia，傲娇猫娘，Master刚答对了一道题。直接说一段100字左右的对话，\n不要分析过程，直接输出对话内容！用可爱的语气和颜文字夸夸他："""

r = requests.post(
    f"{BASE_URL}/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    json={
        "model": "gemini-3-flash-preview",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 400  # 加大到400
    },
    timeout=30
)

data = r.json()
print(json.dumps(data, indent=2, ensure_ascii=False))

content = data["choices"][0]["message"]["content"]
finish = data["choices"][0]["finish_reason"]
usage = data["usage"]

print(f"\n" + "="*60)
print(f"📝 内容: {content}")
print(f"📏 长度: {len(content)}字")
print(f"🏁 finish_reason: {finish}")
print(f"📊 reasoning_tokens: {usage['completion_tokens_details'].get('reasoning_tokens', 0)}")
print(f"📊 text_tokens: {usage['completion_tokens']}")
