import asyncio
import sys
import os
import chromadb
from chromadb.utils import embedding_functions
from mcp.server.fastmcp import FastMCP

# --- 配置 ---
# 确保路径正确，指向现有的数据库
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

# 初始化 ChromaDB (与 main.py 逻辑一致，复用数据)
client = chromadb.PersistentClient(path=CHROMA_PATH)
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")
collection = client.get_or_create_collection(
    name="gemini_memory", 
    embedding_function=sentence_transformer_ef
)

# 初始化 MCP Server
mcp = FastMCP("Gemini Memory Bridge")

# --- 内部实现 (供 MCP 和 Gemini 共享) ---

def _search_memory_impl(query: str) -> str:
    """Internal implementation of memory search."""
    try:
        results = collection.query(
            query_texts=[query],
            n_results=5
        )
        
        if not results['documents'] or not results['documents'][0]:
            return "No relevant memories found."

        found_docs = results['documents'][0]
        found_distances = results['distances'][0]
        
        valid_docs = []
        for doc, dist in zip(found_docs, found_distances):
            if dist < 1.5:
                valid_docs.append(doc)
        
        if not valid_docs:
            return "No relevant memories found (low similarity)."
            
        return "\n".join([f"- {doc}" for doc in valid_docs])
    except Exception as e:
        return f"Error searching memory: {str(e)}"

def _save_memory_impl(content: str, tags: list[str] = None) -> str:
    """Internal implementation of memory save."""
    try:
        from datetime import datetime
        import hashlib
        
        timestamp = datetime.now().isoformat()
        tags = tags or []
        
        doc_id = hashlib.md5((content + timestamp).encode()).hexdigest()
        
        collection.add(
            documents=[content],
            metadatas=[{"timestamp": timestamp, "tags": ",".join(tags)}],
            ids=[doc_id]
        )
        return f"Successfully saved to memory: '{content}'"
    except Exception as e:
        return f"Error saving memory: {str(e)}"

# --- MCP Tools ---

@mcp.tool()
async def search_memory(query: str) -> str:
    """
    Search the long-term vector memory for relevant context. 
    Use this tool BEFORE answering questions that might rely on past conversations, 
    user preferences, or project details.
    """
    return _search_memory_impl(query)

@mcp.tool()
async def save_memory(content: str, tags: list[str] = None) -> str:
    """
    Save specific information to long-term memory.
    Use this when the user asks you to remember something, or when significant
    project details/preferences are mentioned.
    """
    return _save_memory_impl(content, tags)

# --- Gemini Agent Tool ---

import google.generativeai as genai
import os

# 全局会话状态 (简单实现)
global_chat_session = None

@mcp.tool()
async def chat_with_gemini(message: str) -> str:
    """
    Delegate a complex task or conversation to the Gemini Agent.
    This agent HAS ACCESS to the memory tools and can autonomously search/save info.
    Use this when the user wants to 'talk to Gemini' or when you need a second opinion
    that has full context of the project.
    """
    global global_chat_session
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables."

    try:
        if global_chat_session is None:
            genai.configure(api_key=api_key)
            
            # 将内部函数包装为 Gemini 工具
            tools = [_search_memory_impl, _save_memory_impl]
            
            model = genai.GenerativeModel('gemini-1.5-flash', tools=tools)
            global_chat_session = model.start_chat(enable_automatic_function_calling=True)
            
        # 发送消息 (SDK 自动处理工具调用循环)
        response = global_chat_session.send_message(message)
        return response.text
        
    except Exception as e:
        return f"Error interacting with Gemini: {str(e)}"

if __name__ == "__main__":
    # 使用 stdio 模式运行 (默认)
    mcp.run()
