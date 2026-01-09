import time
import os
import requests
import json
from dotenv import load_dotenv

# 加载 .env 获取可能需要的配置（虽然目前 API 地址是硬编码的）
load_dotenv()

# 配置
# 确保路径相对于项目根目录正确
MEMORY_FILE = ".gemini/GEMINI.md"
API_URL = "http://127.0.0.1:8000/api/gatekeeper/ingest"

def sync_to_chroma(text):
    """将新增内容发送给 Gatekeeper 进行智能入库"""
    # 忽略空行、分隔符和一级标题
    clean_text = text.strip()
    if not clean_text or clean_text.startswith("---") or clean_text.startswith("# "):
        return

    payload = {
        "text": clean_text,
        "context": "Source: .gemini/GEMINI.md (Auto-Sync)",
        "force_save": True,  # 强制保存，因为这是 AI 写入 GEMINI.md 的确认内容
        "source": "file_watcher"
    }
    
    try:
        resp = requests.post(API_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            # print(f"✅ Synced to Vector DB: {clean_text[:50]}...")
            pass
        else:
            print(f"❌ Sync Error ({resp.status_code}): {resp.text}")
    except Exception as e:
        # print(f"⚠️ Sync Connection Failed: {e}")
        pass

def watch_file():
    """监听文件变化"""
    if not os.path.exists(MEMORY_FILE):
        print(f"⏳ Waiting for {MEMORY_FILE} to be created...")
        while not os.path.exists(MEMORY_FILE):
            time.sleep(5)

    print(f"👀 Now watching {MEMORY_FILE} for new memories...")
    
    # 获取初始文件大小，跳过现有内容（避免重复同步历史记录）
    file_size = os.path.getsize(MEMORY_FILE)
    
    while True:
        try:
            current_size = os.path.getsize(MEMORY_FILE)
            if current_size > file_size:
                with open(MEMORY_FILE, 'r') as f:
                    f.seek(file_size)
                    new_data = f.read()
                    
                    # 按行处理新增内容
                    for line in new_data.splitlines():
                        if line.strip():
                            sync_to_chroma(line)
                            
                file_size = current_size
            elif current_size < file_size:
                # 文件被截断或重写了（比如手动编辑）
                file_size = current_size
                
            time.sleep(2)
        except Exception as e:
            print(f"Error in watcher: {e}")
            time.sleep(5)

if __name__ == "__main__":
    watch_file()
