"""
API测试脚本 - 验证VectorEngine Gemini API是否可用
"""

import requests
import json

API_KEY = "sk-bKBD5dwJCsaZRgKov0QCRxbOU1KogukIRjLCLx8Mp1NLJwYv"
BASE_URL = "https://api.vectorengine.ai/v1"
MODEL_NAME = "gemini-3-flash-preview"

def test_api():
    """测试API调用"""
    print("🧪 测试 VectorEngine Gemini API...\n")
    
    system_prompt = "你是Mia，一个可爱的猫娘助手。用简短可爱的语气回复。"
    user_prompt = "Master答对了一道题！请夸夸他，不超过30字。"
    
    print(f"📤 发送请求...")
    print(f"   System: {system_prompt}")
    print(f"   User: {user_prompt}\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            },
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.9,
                "max_tokens": 100
            },
            timeout=30
        )
        
        print(f"📥 响应状态码: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API调用成功！\n")
            print(f"完整响应:\n{json.dumps(data, indent=2, ensure_ascii=False)}\n")
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                print(f"🎭 Mia说: {content}")
                return True
        else:
            print(f"❌ API调用失败")
            print(f"响应内容:\n{response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api()
    print(f"\n{'='*50}")
    print(f"测试结果: {'✅ 通过' if success else '❌ 失败'}")
