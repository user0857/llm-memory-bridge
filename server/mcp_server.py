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
    Search long-term memory for relevant information.
    Returns a list of memories with their IDs and content.
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
    Save a new piece of information to long-term memory.
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
async def delete_memory(memory_id: str) -> str:
    """
    Delete a specific memory by its ID. 
    Use 'search_memory' first to find the ID of the memory you want to delete.
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