"""
test_real_connection.py — 真实 API 连通性测试
==============================================
警告：此脚本会产生真实 API 调用消耗！
"""
import sys
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# 1. 强制加载 .env (优先加载 backend/.env)
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
ENV_PATH = BACKEND_DIR / ".env"
load_dotenv(ENV_PATH, override=True)

sys.path.insert(0, str(BACKEND_DIR))

# 2. 引入服务
# 注意：llm_service 实例化时会读取环境变量，所以必须先 load_dotenv
from app.services.llm_service import llm_service

async def main():
    print(f"\n📡 Testing Real API Connection...")
    print(f"   Provider: {llm_service.provider}")
    print(f"   Base URL: {getattr(llm_service, 'base_url', 'N/A')}")
    print(f"   Model:    {getattr(llm_service, 'model', 'N/A')}")
    
    # 构造一个真实的 Prompt
    system_prompt = "你是 Mia，一只赛博猫娘。请用傲娇的语气向你的主人'绯墨'打个招呼。"
    
    try:
        print("\n🚀 Sending request... (Waiting for response)")
        
        # 调用真实接口
        response = await llm_service.generate(
            prompt="快点跟我打招呼！",
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        print(f"\n✅ API Response Received:\n{'='*40}")
        print(response)
        print(f"{'='*40}\n")
        
    except Exception as e:
        print(f"\n❌ API Call Failed!")
        print(f"   Error: {str(e)}")
        print("\nPossible fixes:")
        print("1. Check if .env file exists in backend/")
        print("2. Check if OPENAI_API_KEY is correct")
        print("3. Check if your VPN/Proxy is interfering")

if __name__ == "__main__":
    asyncio.run(main())
