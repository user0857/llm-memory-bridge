import os
from google import genai
from dotenv import load_dotenv

# 加载项目根目录的 .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        return

    print(f"🔑 Using Key: {api_key[:5]}...{api_key[-5:]}")
    
    try:
        client = genai.Client(api_key=api_key)
        print("\n📡 Fetching available models via google-genai SDK...")
        
        count = 0
        for m in client.models.list():
            # 新 SDK 中字段可能有所不同，我们直接打印能看到的
            # 常见的生成模型名字里带有 gemini
            if "gemini" in m.name.lower():
                print(f" - {m.name}")
                count += 1
        
        if count == 0:
            print("⚠️ No gemini models found. Check your API Key permissions.")
        else:
            print(f"\n✅ Found {count} Gemini models.")
            
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")

if __name__ == "__main__":
    list_models()
