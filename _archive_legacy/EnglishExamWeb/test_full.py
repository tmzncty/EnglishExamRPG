"""检查API实际返回内容"""
import requests

API_KEY = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
BASE_URL = "https://api.vectorengine.ai/v1"

prompt = """你是Mia，傲娇猫娘。Master刚答对了2010年Section I Use of English的一道题。

请用100-120字生成Mia的Galgame式对话：
- 开心夸奖，但要傲娇口吻
- 用颜文字和"喵~"
- 有代入感，像真的在陪伴他学习
- 不要复述题目内容

直接回复对话，不要其他格式："""

r = requests.post(
    f"{BASE_URL}/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    json={
        "model": "gemini-3-flash-preview",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 200
    },
    timeout=30
)

data = r.json()
content = data["choices"][0]["message"]["content"]

print("📝 完整返回内容:")
print(content)
print(f"\n📊 字符数: {len(content)}")
print(f"📊 Tokens: {data['usage']['completion_tokens']}")
