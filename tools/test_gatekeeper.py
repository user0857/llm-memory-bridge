import sys
import os
import json

# 将 server 目录添加到路径
sys.path.append(os.path.join(os.getcwd(), 'server'))

from agents.gatekeeper import get_gatekeeper

def test_gatekeeper():
    print("🧠 Initializing Gatekeeper (Gemini API)...")
    gk = get_gatekeeper()
    
    test_cases = [
        {
            "name": "NEW_INFO",
            "input": "记住我的幸运数字是 42。",
            "context": "无"
        },
        {
            "name": "UPDATE_INFO",
            "input": "其实我的幸运数字改成了 18，不再是 42 了。",
            "context": "[ID: mem_1] 用户的幸运数字是 42。"
        },
        {
            "name": "JUNK_INFO",
            "input": "哈哈，今天天气不错。",
            "context": "无"
        }
    ]
    
    print("\n--- Starting Functional Tests ---")
    
    for case in test_cases:
        print(f"\n[Test: {case['name']}]")
        print(f"Input: {case['input']}")
        print(f"Context: {case['context']}")
        
        try:
            result = gk.process(case['input'], case['context'])
            print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Error during test: {e}")

if __name__ == "__main__":
    test_gatekeeper()
