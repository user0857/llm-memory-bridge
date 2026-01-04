import os
import sys
import json
import requests
import google.generativeai as genai
from datetime import datetime
from pathlib import Path

# --- 配置 ---
BRIDGE_SERVER_URL = "http://127.0.0.1:8000"
API_KEY = os.getenv("GEMINI_API_KEY") # 请确保环境变量里有这个
HISTORY_FILE = Path("chat_history.json")

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
        # print(f"⚠️ 无法连接记忆服务器: {e}")
        pass
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

# --- Session Management ---
def load_chat_history():
    if not HISTORY_FILE.exists():
        return []
    
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 转换为 genai 需要的格式
            history = []
            for item in data:
                history.append({
                    "role": item["role"],
                    "parts": item["parts"]
                })
            return history
    except Exception as e:
        print(f"⚠️ 无法加载历史记录: {e}")
        return []

def save_chat_history(history):
    data = []
    for entry in history:
        # entry 是 google.ai.generativelanguage.Content 类型
        parts = []
        for part in entry.parts:
            parts.append(part.text)
        
        data.append({
            "role": entry.role,
            "parts": parts
        })
        
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 无法保存历史记录: {e}")

# --- 主程序 ---
def main():
    history = load_chat_history()
    model = genai.GenerativeModel('gemini-pro')
    chat = model.start_chat(history=history)
    
    print("\n🤖 Gemini CLI (Memory Synced + Session Restore)")
    print("--------------------------------")
    if history:
        print(f"🔄 已恢复之前的对话 ({len(history)} 条消息)")
    print("提示: 输入 'exit' 退出，输入 '/clear' 清除当前会话。")

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input: continue
            
            if user_input.lower() in ['exit', 'quit']: 
                break
            
            if user_input.lower() == '/clear':
                if HISTORY_FILE.exists():
                    os.remove(HISTORY_FILE)
                chat = model.start_chat(history=[])
                print("🧹 会话已重置。")
                continue

            if user_input.lower().startswith('/recall'):
                query = user_input[7:].strip()
                if not query:
                    print("⚠️ 请输入查询内容，例如: /recall 螃蟹")
                    continue
                
                print(f"🔍 正在检索关于 '{query}' 的记忆...")
                ctx = get_context_from_bridge(query)
                if ctx:
                    print(f"✅ 检索结果:\n{ctx}")
                else:
                    print("📭 未找到相关记忆 (可能是相似度过低或无数据)")
                continue

            # 1. RAG: 去本地服务器查记忆
            context_prompt = ""
            retrieved_context = get_context_from_bridge(user_input)
            
            if retrieved_context:
                print(f"   (🔗 已关联本地记忆)")
                context_prompt = f"{retrieved_context}\n\n基于以上背景，请回答：\n"

            # 2. 发送给 Gemini
            full_prompt = context_prompt + user_input
            
            # 捕获可能的 API 错误
            try:
                response = chat.send_message(full_prompt, stream=True)
                
                print("Gemini: ", end="", flush=True)
                full_response_text = ""
                for chunk in response:
                    text = chunk.text
                    print(text, end="", flush=True)
                    full_response_text += text
                print("\n")

                # 3. 双向同步
                save_chat_history(chat.history)
                save_memory_to_bridge(f"CLI User: {user_input}")
                save_memory_to_bridge(f"CLI Gemini: {full_response_text}")
                
            except Exception as api_err:
                print(f"\n❌ API Error: {api_err}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
