import asyncio
import sys
import os
import chromadb
from chromadb.utils import embedding_functions
from mcp.server.fastmcp import FastMCP

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

client = chromadb.PersistentClient(path=CHROMA_PATH)
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
collection = client.get_or_create_collection(
    name="gemini_memory", 
    embedding_function=sentence_transformer_ef
)

mcp = FastMCP("LLM Memory Bridge")

def _search_memory_impl(query: str) -> str:
    try:
        results = collection.query(query_texts=[query], n_results=5)
        if not results['documents'] or not results['documents'][0]:
            return "No relevant memories found."
        valid_docs = [doc for doc, dist in zip(results['documents'][0], results['distances'][0]) if dist < 1.5]
        return "\n".join([f"- {doc}" for doc in valid_docs]) or "No relevant memories found (low similarity)."
    except Exception as e:
        return f"Error searching memory: {str(e)}"

def _save_memory_impl(content: str, tags: list[str] = None) -> str:
    try:
        from datetime import datetime
        import hashlib
        timestamp = datetime.now().isoformat()
        doc_id = hashlib.md5((content + timestamp).encode()).hexdigest()
        collection.add(documents=[content], metadatas=[{"timestamp": timestamp, "tags": ",".join(tags or [])}], ids=[doc_id])
        return f"Successfully saved to memory: '{content}'"
    except Exception as e:
        return f"Error saving memory: {str(e)}"

@mcp.tool()
async def search_memory(query: str) -> str:
    """Search long-term memory."""
    return _search_memory_impl(query)

@mcp.tool()
async def save_memory(content: str, tags: list[str] = None) -> str:
    """Save to long-term memory."""
    return _save_memory_impl(content, tags)

if __name__ == "__main__":
    mcp.run()
