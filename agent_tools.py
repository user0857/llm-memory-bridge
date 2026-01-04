import requests
import json
import sys

BRIDGE_URL = "http://127.0.0.1:8000"

def query_memory(query_text):
    """向本地 Bridge Server 查询记忆"""
    try:
        resp = requests.post(f"{BRIDGE_URL}/search_context", json={"user_input": query_text}, timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            context = data.get("context", "")
            if context:
                print(f"✅ Found Memory:\n{context}")
            else:
                print("📭 No relevant memory found.")
        else:
            print(f"❌ Server Error: {resp.status_code}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

def save_memory(content):
    """向本地 Bridge Server 保存记忆"""
    try:
        resp = requests.post(
            f"{BRIDGE_URL}/add_memory", 
            json={"content": content, "tags": ["agent-cli"]},
            timeout=2
        )
        if resp.status_code == 200:
            print("💾 Memory Saved.")
        else:
            print(f"❌ Save Failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    # 简单的命令行接口供 Agent 调用
    if len(sys.argv) < 3:
        print("Usage: python agent_tools.py [search|save] 'content'")
        sys.exit(1)
        
    action = sys.argv[1]
    text = sys.argv[2]
    
    if action == "search":
        query_memory(text)
    elif action == "save":
        save_memory(text)
    else:
        print("Unknown action")
