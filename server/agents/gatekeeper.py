import os
import json
from google import genai
from google.genai import types
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Gatekeeper:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Gatekeeper, cls).__new__(cls)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GATEKEEPER_MODEL", "gemini-2.0-flash")
        
        if not api_key:
            print("⚠️ WARNING: GEMINI_API_KEY not found in .env. Gatekeeper will fail.")
            self.client = None
            return

        # 新 SDK 初始化方式
        self.client = genai.Client(api_key=api_key)
        print(f"☁️ Gatekeeper connected to {self.model_name} (via google-genai SDK).")

    def process(self, user_input: str, context: Optional[str] = None, force_save: bool = False, source_url: str = None) -> Dict[str, Any]:
        if not self.client:
            return {"error": "API Key missing"}

        ctx_str = context if context and context.strip() else "None"
        source_context = f"\nSource URL: {source_url}" if source_url else ""

        # 根据是否强制保存，调整 Prompt
        if force_save:
            intent_instruction = "2. Intent is ALWAYS 'SAVE'. You MUST preserve the User Input EXACTLY as it is."
        else:
            intent_instruction = """2. Determine the Intent based on "Knowledge Increment":
   - SAVE: If the input contains new facts.
   - UPDATE: If it refines existing context.
   - DISCARD: If it is pure chatter or exact duplicate."""

        system_instruction = "You are a data preservation specialist. Your ONLY task is to extract information without altering its original wording or format."

        prompt = f"""
Context: {ctx_str}
Source URL: {source_url or "None"}

User Input:
{user_input}

Instructions:
1. Determine if the input should be SAVED, UPDATED, or DISCARDED.
2. For SAVED or UPDATED entries: You MUST copy the 'User Input' into the 'content' field VERBATIM. 
   - DO NOT summarize.
   - DO NOT rephrase.
   - DO NOT remove bullet points.
   - DO NOT change the perspective (e.g., don't change 'I' to 'the user').
   - Keep the EXACT same characters, newlines, and symbols.

JSON Schema:
{{
  "intent": "SAVE" | "UPDATE" | "DISCARD",
  "reason": "Brief explanation",
  "content": "COPY OF USER INPUT VERBATIM",
  "tags": ["tag1", "tag2"],
  "target_id": null
}}
"""
        try:
            # 新 SDK 调用方式
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.0
                )
            )
            
            # 解析 JSON
            result = json.loads(response.text)
            
            # 转换为工具调用格式
            intent = result.get("intent", "DISCARD")
            
            if intent == "DISCARD":
                return {
                    "thought": f"Discarded: {result.get('reason')}",
                    "tool": "discard",
                    "args": {"reason": result.get("reason")}
                }
            
            elif intent == "UPDATE":
                return {
                    "thought": f"Updating memory: {result.get('reason')}",
                    "tool": "update_memory",
                    "args": {
                        "memory_id": result.get("target_id") or "unknown",
                        "new_content": result.get("content")
                    }
                }
            
            else: # SAVE
                return {
                    "thought": "Saving new memory",
                    "tool": "save_memory",
                    "args": {
                        "content": result.get("content"),
                        "tags": result.get("tags", [])
                    }
                }

        except Exception as e:
            print(f"❌ Gatekeeper Error: {e}")
            return {
                "thought": "Gatekeeper failed, falling back to raw save.",
                "tool": "save_memory",
                "args": {"content": user_input, "tags": ["raw_fallback"]}
            }

def get_gatekeeper():
    return Gatekeeper()
