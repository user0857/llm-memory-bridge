from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions

app = FastAPI(title="LLM Memory Bridge (Vector RAG Only)")

import os
# --- 配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

# 初始化 ChromaDB
# 使用持久化客户端
client = chromadb.PersistentClient(path=CHROMA_PATH)

# 使用支持中文的多语言模型
# 第一次运行会自动下载 (约 470MB)
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")

collection = client.get_or_create_collection(
    name="gemini_memory", 
    embedding_function=sentence_transformer_ef
)

class MemoryItem(BaseModel):
    content: str
    timestamp: Optional[str] = None
    tags: List[str] = []

class QueryRequest(BaseModel):
    user_input: str
    threshold: Optional[float] = None
    n_results: Optional[int] = 5  # Default to 5

class DeleteRequest(BaseModel):
    memory_id: str

class UpdateRequest(BaseModel):
    memory_id: str
    new_content: str
    new_tags: Optional[List[str]] = None

# --- 核心 API ---

@app.get("/")
def read_root():
    return {"status": "running", "mode": "Vector RAG Only", "count": collection.count()}

@app.post("/add_memory")
def add_memory(item: MemoryItem):
    """
    保存记忆：只写入 ChromaDB (检索)
    """
    timestamp = datetime.now().isoformat()
    tags = item.tags or []
    
    # 生成唯一 ID (简单起见用时间戳+哈希，或者 UUID)
    import hashlib
    doc_id = hashlib.md5((item.content + timestamp).encode()).hexdigest()
    
    collection.add(
        documents=[item.content],
        metadatas=[{"timestamp": timestamp, "tags": ",".join(tags)}],
        ids=[doc_id]
    )
    
    print(f"📥 Saved memory: {item.content[:30]}...")
    return {
        "status": "success", 
        "data": {
            "id": doc_id,
            "content": item.content,
            "timestamp": timestamp,
            "tags": tags
        }
    }

@app.post("/api/update")
def update_memory(req: UpdateRequest):
    """
    更新指定 ID 的记忆内容
    """
    try:
        timestamp = datetime.now().isoformat()
        metadata = {"timestamp": timestamp}
        if req.new_tags:
            metadata["tags"] = ",".join(req.new_tags)
            
        # ChromaDB update 接口: 如果 ID 存在则更新，不存在不报错但也没效果
        # 注意: update 会重新计算 embedding
        collection.update(
            ids=[req.memory_id],
            documents=[req.new_content],
            metadatas=[metadata]
        )
        print(f"🔄 Updated memory {req.memory_id}: {req.new_content[:30]}...")
        return {"status": "success", "message": f"Memory {req.memory_id} updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
def api_search(query: QueryRequest):
    """
    通用搜索接口 (供 MCP Agent 等使用)
    返回详细的 JSON 结构，包含 ID，方便后续删除或修改
    """
    num_results = query.n_results if query.n_results else 5
    results = collection.query(
        query_texts=[query.user_input],
        n_results=num_results
    )
    
    if not results['documents'] or not results['documents'][0]:
        return {"results": []}

    structured_results = []
    # ChromaDB returns lists of lists
    docs = results['documents'][0]
    ids = results['ids'][0]
    metadatas = results['metadatas'][0]
    distances = results['distances'][0]

    # Filter by threshold if provided
    threshold = query.threshold if query.threshold is not None else 1.0
    
    for i in range(len(docs)):
        dist = distances[i]
        if dist < threshold:
            structured_results.append({
                "id": ids[i],
                "content": docs[i],
                "metadata": metadatas[i],
                "distance": dist
            })
        
    return {"results": structured_results}

@app.post("/api/delete")
def delete_memory(req: DeleteRequest):
    """
    删除指定 ID 的记忆
    """
    try:
        # chroma collection.delete supports where filters or ids
        collection.delete(ids=[req.memory_id])
        return {"status": "success", "message": f"Memory {req.memory_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
