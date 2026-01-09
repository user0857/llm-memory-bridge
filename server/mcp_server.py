import asyncio
import sys
import os
import requests
import json
from mcp.server.fastmcp import FastMCP

# 配置 API 地址
API_BASE_URL = "http://127.0.0.1:8000"

mcp = FastMCP("LLM Memory Bridge")

def _check_api_health():
    """检查后端 API 是否存活"""
    try:
        resp = requests.get(f"{API_BASE_URL}/")
        return resp.status_code == 200
    except:
        return False

@mcp.tool()
async def search_memory(query: str) -> str:
    """
    Search for memories in the vector database using semantic similarity.
    
    This tool is best used when you need to recall facts, user preferences, or past project context.
    The 'query' can be a natural language question (e.g., "What is the project roadmap?") or keywords.
    
    Returns:
        A formatted string containing a list of relevant memories. Each memory includes:
        - ID: Unique identifier (crucial for deletion/update).
        - Time: Timestamp of creation.
        - Tags: Associated categories.
        - Content: The actual memory text.
    """
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/search", 
            json={"user_input": query},
            timeout=5
        )
        if resp.status_code != 200:
            return f"Error: API returned status {resp.status_code}"
        
        data = resp.json()
        results = data.get("results", [])
        
        if not results:
            return "No relevant memories found."
            
        # 格式化输出，包含 ID 方便 AI 决定是否删除
        output = []
        for item in results:
            # 过滤掉距离太远的 (可选，目前在 API 端没做过滤，这里可以简单过滤)
            if item.get("distance", 0) < 1.8:
                meta = item.get("metadata", {})
                timestamp = meta.get("timestamp", "Unknown time")
                tags = meta.get("tags", "")
                output.append(f"ID: {item['id']}\nTime: {timestamp}\nTags: {tags}\nContent: {item['content']}\n")
        
        return "\n---\n".join(output) if output else "No relevant memories found (low similarity)."
        
    except requests.exceptions.ConnectionError:
        return "Error: Memory server (FastAPI) is offline. Please start the server first."
    except Exception as e:
        return f"Error searching memory: {str(e)}"

@mcp.tool()
async def save_memory(content: str, tags: list[str] = None) -> str:
    """
    智能保存记忆 (Smart Save).
    
    只需提供原始文本，Server 端的 Gatekeeper AI 会自动进行：
    1. 意图识别 (过滤无用闲聊)
    2. 隐私检查
    3. 自动摘要与打标签
    4. 冲突检测 (如果是旧信息会自动转为更新)
    
    Args:
        content: The raw text, observation, or fact you want to remember.
        tags: (Optional) Legacy parameter, ignored by Gatekeeper.
    """
    try:
        # 调用智能摄入接口
        payload = {
            "text": content,
            # 上下文让 Server 自己去搜，或者未来扩展让 Claude 传
            "context": None,
            # MCP 来源的数据被视为可信，强制进行处理（只做摘要，不做过滤）
            "force_save": True,
            "source": "mcp"
        }
        
        resp = requests.post(
            f"{API_BASE_URL}/api/gatekeeper/ingest", 
            json=payload,
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            decision = data.get("decision", {})
            action_result = data.get("action_result", "")
            
            tool_used = decision.get("tool")
            thought = decision.get("thought")
            
            return f"Gatekeeper Processed: {tool_used}\nThought: {thought}\nResult: {action_result}"
        else:
            return f"Failed to save memory. Status: {resp.status_code}"
            
    except requests.exceptions.ConnectionError:
        return "Error: Memory server (FastAPI) is offline."
    except Exception as e:
        return f"Error saving memory: {str(e)}"

@mcp.tool()
async def update_memory(memory_id: str, new_content: str, new_tags: list[str] = None) -> str:
    """
    Update an existing memory with new content or tags.
    
    Use this tool when you need to correct, refine, or update a specific memory found via `search_memory`.
    This maintains the cleanliness of the database by avoiding duplicates.
    
    Args:
        memory_id: The exact ID of the memory to update (get this from `search_memory`).
        new_content: The new, corrected text content.
        new_tags: (Optional) New list of tags to replace the old ones.
    """
    try:
        payload = {
            "memory_id": memory_id,
            "new_content": new_content
        }
        if new_tags:
            payload["new_tags"] = new_tags
            
        resp = requests.post(
            f"{API_BASE_URL}/api/update",
            json=payload,
            timeout=5
        )
        if resp.status_code == 200:
            return f"Successfully updated memory {memory_id}."
        else:
            return f"Failed to update memory. Status: {resp.status_code}"
            
    except requests.exceptions.ConnectionError:
        return "Error: Memory server (FastAPI) is offline."
    except Exception as e:
        return f"Error updating memory: {str(e)}"

@mcp.tool()
async def delete_memory(memory_id: str) -> str:
    """
    Permanently delete a specific memory from the database by its ID.
    
    CRITICAL: You MUST use 'search_memory' first to find the exact 'memory_id'.
    Do not guess the ID. This operation cannot be undone.
    """
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/delete",
            json={"memory_id": memory_id},
            timeout=5
        )
        if resp.status_code == 200:
            return f"Successfully deleted memory {memory_id}."
        else:
            return f"Failed to delete memory. Status: {resp.status_code}"
            
    except requests.exceptions.ConnectionError:
        return "Error: Memory server (FastAPI) is offline."
    except Exception as e:
        return f"Error deleting memory: {str(e)}"

if __name__ == "__main__":
    mcp.run()