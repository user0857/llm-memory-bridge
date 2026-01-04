import os
import sys
import requests
import google.generativeai as genai
from datetime import datetime

# --- 配置 ---
BRIDGE_SERVER_URL = "http://127.0.0.1:8000"
API_KEY = os.getenv("GEMINI_API_KEY") # 请确保环境变量里有这个

if not API_KEY:
    print("❌ 错误: 未找到 GEMINI_API_KEY 环境变量。")
    print("请执行: export GEMINI_API_KEY='你的key'")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# --- Bridge API ---
def get_context_from_bridge(query):
    try:
        resp = requests.post(f"{BRIDGE_SERVER_URL}/search_context", json={"user_input": query}, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("context", "")
    except Exception as e:
        print(f"⚠️ 无法连接记忆服务器: {e}")
    return ""

def save_memory_to_bridge(content):
    try:
        requests.post(
            f"{BRIDGE_SERVER_URL}/add_memory", 
            json={"content": content, "tags": ["cli-chat"]},
            timeout=2
        )
    except Exception:
        pass # 静默失败，不打断对话

# --- 主程序 ---
def main():
    model = genai.GenerativeModel('gemini-pro')
    chat = model.start_chat(history=[])
    
    print("\n🤖 Gemini CLI (Memory Synced)")
    print("--------------------------------")
    print("提示: 输入 'exit' 退出。")

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input: continue
            if user_input.lower() in ['exit', 'quit']: break

            # 1. RAG: 去本地服务器查记忆
            context_prompt = ""
            retrieved_context = get_context_from_bridge(user_input)
            
            if retrieved_context:
                print(f"   (🔗 已关联本地记忆)")
                # 构造包含记忆的 Prompt
                # 注意：在 Chat 模式下，通常建议把 Context 放在 System Instruction 里，
                # 但这里为了简单，我们直接附着在 User Message 里
                context_prompt = f"{retrieved_context}\n\n基于以上背景，请回答：\n"

            # 2. 发送给 Gemini
            full_prompt = context_prompt + user_input
            response = chat.send_message(full_prompt, stream=True)
            
            print("Gemini: ", end="", flush=True)
            full_response_text = ""
            for chunk in response:
                text = chunk.text
                print(text, end="", flush=True)
                full_response_text += text
            print("\n")

            # 3. 双向同步：把这次对话存回 Server
            # 保存用户的话
            save_memory_to_bridge(f"CLI User: {user_input}")
            # 保存 AI 的话
            save_memory_to_bridge(f"CLI Gemini: {full_response_text}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
