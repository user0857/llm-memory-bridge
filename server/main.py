from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions

app = FastAPI(title="Gemini Memory Bridge (Vector RAG Only)")

# --- 配置 ---
CHROMA_PATH = "chroma_db"

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

class MemoryResponse(BaseModel):
    context: str
    source_count: int

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
            "content": item.content,
            "timestamp": timestamp,
            "tags": tags
        }
    }

@app.post("/search_context", response_model=MemoryResponse)
def search_context(query: QueryRequest):
    """
    向量检索接口
    """
    user_text = query.user_input
    
    # 执行查询
    results = collection.query(
        query_texts=[user_text],
        n_results=3  # 返回最相关的 3 条
    )
    
    # 解析结果
    # results['documents'] 是一个 list of list
    if not results['documents'] or not results['documents'][0]:
        return {"context": "", "source_count": 0}

    # 简单的距离阈值过滤 (可选)
    # results['distances'] 越小越相似 (L2 距离)
    # 对于 paraphrase-multilingual-MiniLM-L12-v2, 距离通常在 0 ~ 2 之间
    # 经验阈值: < 1.2 表示有一定相关性, < 0.8 表示强相关
    THRESHOLD = 1.2
    
    found_docs = results['documents'][0]
    found_distances = results['distances'][0]
    
    valid_docs = []
    for doc, dist in zip(found_docs, found_distances):
        print(f"🔍 Match: {doc[:20]}... (Dist: {dist:.4f})")
        
        if dist < THRESHOLD:
            valid_docs.append(doc)

    if not valid_docs:
        print("   -> No documents met the threshold.")
        return {"context": "", "source_count": 0}

    context_text = "【本地记忆库提示】:\n" + "\n".join([f"- {d}" for d in valid_docs])
    
    return {"context": context_text, "source_count": len(valid_docs)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
