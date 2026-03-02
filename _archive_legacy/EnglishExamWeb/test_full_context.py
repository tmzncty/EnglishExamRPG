"""直接测试完整上下文的API调用"""
import requests
import json

API_KEY = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
BASE_URL = "https://api.vectorengine.ai/v1"

# 模拟完整题目上下文
prompt = """你是Mia，Master的傲娇猫娘学习伙伴。你和Master正在一起做2010年考研英语真题。

刚才Master答对了下面这道题：

【题型】Use of English
【章节】Section I Use of English
【文章片段】As many people hit middle age, they often start to notice that their memory and mental clarity are not what they used to be...
【题目】we put the keys just a moment ago
【选项】
  A. that
  B. when
  C. why
  D. where
【正确答案】D

【场景设定】
Mia坐在Master身边，和他一起看着题目。你们刚刚一起读完了文章/题目，Master选了答案。
完形填空题很考验对文章的整体理解和语感。

【你的任务】
生成Mia的Galgame式对话（120-150字），要求：

1. **具体性**：提到文章/题目中的具体内容
2. **情感真实**：开心但要傲娇
3. **陪伴感**：用"我们一起..."、"Mia陪你..."
4. **语气自然**：口语化，适当用"喵~"

直接输出Mia说的话，不要其他格式："""

r = requests.post(
    f"{BASE_URL}/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    json={
        "model": "gemini-3-flash-preview",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85,
        "max_tokens": 600
    },
    timeout=45
)

data = r.json()

print("="*80)
print("📋 完整API响应：\n")
print(json.dumps(data, indent=2, ensure_ascii=False))

print("\n" + "="*80)
print("📝 message.content:")
print(data["choices"][0]["message"]["content"])

print("\n" + "="*80)
print("🧠 message.reasoning_content:")
reasoning = data["choices"][0]["message"].get("reasoning_content", "")
print(reasoning)

print("\n" + "="*80)
print(f"统计:")
print(f"  content长度: {len(data['choices'][0]['message']['content'])}")
print(f"  reasoning长度: {len(reasoning)}")
