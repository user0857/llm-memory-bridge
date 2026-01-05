import os
import sys
import json
import requests
import google.generativeai as genai
from google.generativeai.types import content_types
from collections.abc import Iterable
from pathlib import Path

# --- 配置 ---
BRIDGE_SERVER_URL = "http://127.0.0.1:8000"
API_KEY = os.getenv("GEMINI_API_KEY")
HISTORY_FILE = Path("chat_history.json")

if not API_KEY:
    print("❌ 错误: 未找到 GEMINI_API_KEY 环境变量。")
    sys.exit(1)

genai.configure(api_key=API_KEY)

# --- Tool Functions (供 Gemini 调用) ---
def search_memory_tool(query: str):
    """
    Search the long-term memory for relevant context.
    Use this when the user asks about past events, preferences, or specific project details.
    """
    print(f"  🔍 [Tool] Searching memory for: '{query}'...")
    try:
        resp = requests.post(f"{BRIDGE_SERVER_URL}/search_context", json={"user_input": query}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            ctx = data.get("context", "")
            if ctx:
                return ctx
            return "No relevant memories found."
    except Exception as e:
        return f"Error connecting to memory bridge: {e}"
    return "No result."

def save_memory_tool(content: str, tags: str = ""):
    """
    Save important information to long-term memory.
    Use this when the user explicitly asks to remember something, or shares significant personal/project info.
    Args:
        content: The text to remember.
        tags: Comma-separated tags (e.g. "project,preference").
    """
    print(f"  💾 [Tool] Saving memory: '{content}'...")
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    try:
        requests.post(
            f"{BRIDGE_SERVER_URL}/add_memory", 
            json={"content": content, "tags": tag_list},
            timeout=5
        )
        return "Memory saved successfully."
    except Exception as e:
        return f"Error saving memory: {e}"

# 工具映射表
tools_map = {
    'search_memory_tool': search_memory_tool,
    'save_memory_tool': save_memory_tool
}

# --- Session Management ---
# 简化版历史记录，主要用于恢复，但在 Function Calling 场景下
# 复杂的 FunctionResponse 序列化比较麻烦，这里暂时只保存简单的文本交互作为上下文恢复参考
# 或者完全重置以保证工具调用的连贯性。
def load_chat_history():
    # 暂时禁用历史恢复，因为 Tool Call 的历史结构比较复杂，
    # 简单的 JSON 恢复容易导致 SDK 报错。
    # 建议每次启动都是新会话，但拥有长期记忆库。
    return []

# --- 主程序 ---
def main():
    # 1. 初始化模型，绑定工具
    tools = [search_memory_tool, save_memory_tool]
    model = genai.GenerativeModel('gemini-1.5-flash', tools=tools) # 使用支持工具更好的模型
    
    # 开启自动函数调用 (Auto-function calling)
    # SDK 会自动处理 function_call -> function_response 的往返
    chat = model.start_chat(enable_automatic_function_calling=True)
    
    print("\n🤖 Gemini CLI (Tool Use / Agent Mode)")
    print("-------------------------------------")
    print("提示: 我现在有自主权，会根据需要查阅记忆或记录信息。")
    print("      输入 '/recall <query>' 可强制手动检索。")

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input: continue
            
            if user_input.lower() in ['exit', 'quit']: 
                break
            
            # 手动指令保留
            if user_input.lower().startswith('/recall'):
                q = user_input[7:].strip()
                print(search_memory_tool(q))
                continue

            # 发送给 Gemini (SDK 自动处理工具调用)
            response = chat.send_message(user_input)
            
            # 打印回复
            print(f"Gemini: {response.text}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
