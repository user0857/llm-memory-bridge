import sys
import os
import json

# 将 server 目录添加到路径
sys.path.append(os.path.join(os.getcwd(), 'server'))

from agents.gatekeeper import get_gatekeeper

def test_force_save():
    print("🧠 Initializing Gatekeeper (Gemini API)...")
    gk = get_gatekeeper()
    
    # 这是一个典型的垃圾信息，正常会被 DISCARD
    junk_input = "嗯嗯，好的，我知道了。"
    context = "无"
    
    print(f"\n[Test: FORCE_SAVE with JUNK]")
    print(f"Input: {junk_input}")
    
    try:
        # 强制保存
        result = gk.process(junk_input, context, force_save=True)
        print(f"Result (Should be SAVE): {json.dumps(result, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_force_save()

