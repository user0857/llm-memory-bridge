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
    Persist a new fact, insight, or task to the long-term vector memory.

    **CRITICAL Workflow:**
    1. **Search First**: Before calling this tool, you MUST use `search_memory` to check if similar information already exists.
    2. **Check for Conflict**: 
       - If a conflicting or outdated memory exists (e.g., "Favorite color is Blue" vs "Favorite color is Red"), use `update_memory` to overwrite it.
       - If the new information is a duplicate, DO NOT save it again.
    3. **Save New**: Only use `save_memory` if the information is truly new and non-conflicting.

    **When to use:**
    - Call this tool ONLY when there is significant progress in the conversation or a key conclusion is reached.
    - ALWAYS summarize the information before saving.

    Args:
        content: The summarized text content to store.
        tags: Optional list of strings for categorization (e.g., ["project-a", "preference"])
    """
    try:
        payload = {
            "content": content,
            "tags": tags or ["cli-agent"]
        }
        resp = requests.post(
            f"{API_BASE_URL}/add_memory", 
            json=payload,
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            mem_id = data.get("data", {}).get("id", "unknown")
            return f"Successfully saved to memory. (ID: {mem_id})"
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