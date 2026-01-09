
import asyncio
import json
import websockets

async def simulate_browser_extension_message():
    # 模拟 Chrome Extension 发送的 payload
    # 注意：这实际上是模拟 content.js 的行为，通过 HTTP 请求到 server
    # background.js 只是转发，最终还是调用的 server API
    
    import requests
    
    API_URL = "http://127.0.0.1:8000/add_memory"
    
    # 1. Test the LEGACY endpoint (add_memory) used by background.js 
    # This was the one previously missing 'source'
    print("\n--- Testing Browser Background (Legacy /add_memory) ---")
    payload_legacy = {
        "content": "Browser Test: This memory came from the background script.",
        "tags": ["web-chat"],
        "source": "web_extension" 
    }
    
    try:
        resp = requests.post(API_URL, json=payload_legacy)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        if resp.status_code == 200:
             print("✅ Legacy Add Memory Successful")
    except Exception as e:
        print(f"❌ Legacy Add Memory Failed: {e}")

    # 2. Test the NEW Gatekeeper endpoint used by Content Script
    print("\n--- Testing Browser Content Script (Gatekeeper /ingest) ---")
    INGEST_URL = "http://127.0.0.1:8000/api/gatekeeper/ingest"
    
    payload_ingest = {
        "text": "Browser Test: The user is reading about JavaScript Promises.",
        "source": "web_extension",
        "source_url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise",
        "force_save": False # Let Gatekeeper decide
    }
    
    try:
        resp = requests.post(INGEST_URL, json=payload_ingest)
        print(f"Status: {resp.status_code}")
        # print(f"Response: {resp.json()}") 
        # Don't print full JSON, just decision
        data = resp.json()
        print(f"Decision: {data.get('decision', {}).get('tool')}")
        if resp.status_code == 200:
             print("✅ Gatekeeper Ingest Successful")
    except Exception as e:
        print(f"❌ Gatekeeper Ingest Failed: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_browser_extension_message())
