import json
from mlx_lm import load, generate
from typing import Dict, Any, List, Optional
import os
import re

class Librarian:
    _instance = None
    _model = None
    _tokenizer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Librarian, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if Librarian._model is None:
            self.model_id = "mlx-community/Youtu-LLM-2B-4bit"
            print(f"🧠 Librarian is waking up (loading {self.model_id})...")
            Librarian._model, Librarian._tokenizer = load(self.model_id)
            print("📖 Librarian is ready.")

    def _generate_text(self, system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str:
        # 回归最朴素的 Prompt，避免特殊符号干扰
        formatted_prompt = f"{system_prompt}\n\nUser Input: {user_prompt}\n\nAssistant Response:"
        
        response = generate(
            Librarian._model, Librarian._tokenizer, 
            prompt=formatted_prompt, max_tokens=max_tokens, 
            verbose=False
        )
        
        # 🚨 调试核心：打印原始输出
        print(f"\n[DEBUG RAW] >>>{repr(response)}<<<")

        # 简单清洗
        clean_res = response.strip()
        
        # 移除 Assistant Response: 之后可能的重复
        if "Assistant Response:" in clean_res:
            clean_res = clean_res.split("Assistant Response:")[-1].strip()
            
        # 移除 think 标签 (DeepSeek/Qwen 风格，预防万一)
        clean_res = re.sub(r'(?i)<think>.*?</think>', '', clean_res, flags=re.DOTALL).strip()
        
        # 如果结果为空，返回原始值以便调试
        if not clean_res:
            return "[EMPTY_GENERATION]"
            
        return clean_res

    def classify_intent(self, user_input: str, context: str) -> str:
        # 极简分类，强制单字
        system = "Instruction: Classify intent as SAVE, UPDATE, or DISCARD. Return ONE word only."
        user = f"Context: {context}\nInput: {user_input}"
        
        res = self._generate_text(system, user, max_tokens=5).upper()
        
        # 宽松匹配
        if "UPDATE" in res: return "UPDATE"
        if "DISCARD" in res: return "DISCARD"
        return "SAVE" # 默认

    def process(self, user_input: str, context: Optional[str] = None) -> Dict[str, Any]:
        ctx_str = context if context and context.strip() else "None"
        
        # 1. 意图分类
        intent = self.classify_intent(user_input, ctx_str)
        print(f"🕵️ Intent: {intent}")

        if intent == "DISCARD":
            return {"thought": "Discarded", "tool": "discard", "args": {"reason": "Junk"}}

        if intent == "UPDATE":
            ids = re.findall(r"\[ID: ([a-f0-9]+)\]", ctx_str)
            target_id = ids[0] if ids else "unknown"
            
            system = "Instruction: Update the memory with new info. Output only the new content."
            user = f"Old: {ctx_str}\nNew: {user_input}"
            new_content = self._generate_text(system, user, max_tokens=128)
            
            return {
                "thought": "Updating",
                "tool": "update_memory",
                "args": {"memory_id": target_id, "new_content": new_content}
            }

        # SAVE
        system = "Instruction: Summarize into a fact and tags (Summary | Tag1, Tag2)."
        user = f"{user_input}"
        res = self._generate_text(system, user, max_tokens=128)
        
        if "|" in res:
            parts = res.split("|")
            summary = parts[0].strip()
            tags = [t.strip() for t in parts[1].split(",")]
        else:
            summary = res
            tags = []
            
        return {
            "thought": "Saving",
            "tool": "save_memory",
            "args": {"content": summary, "tags": tags}
        }

def get_librarian():
    return Librarian()