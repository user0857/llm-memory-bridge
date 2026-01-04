from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions

app = FastAPI(title="Gemini Memory Bridge (Vector RAG Edition)")

# --- 配置 ---
DATA_FILE = "memory.json"
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

# --- 辅助函数 ---
def load_json_memories() -> List[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_json_memory(content: str, tags: list = None):
    memories = load_json_memories()
    timestamp = datetime.now().isoformat()
    new_memory = {
        "content": content,
        "timestamp": timestamp,
        "tags": tags or []
    }
    memories.append(new_memory)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)
    return new_memory, timestamp

# --- 迁移逻辑 (Migration) ---
# 每次启动时检查，如果 Chroma 是空的但 JSON 有数据，就导进去
def migrate_json_to_chroma():
    existing_count = collection.count()
    if existing_count == 0:
        json_data = load_json_memories()
        if json_data:
            print(f"🔄 Migrating {len(json_data)} memories from JSON to Vector DB...")
            ids = [f"mem_{i}" for i in range(len(json_data))]
            documents = [m["content"] for m in json_data]
            metadatas = [{"timestamp": m["timestamp"], "tags": ",".join(m["tags"])} for m in json_data]
            
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print("✅ Migration complete.")

# 执行迁移
migrate_json_to_chroma()

# --- 核心 API ---

@app.get("/")
def read_root():
    return {"status": "running", "mode": "Vector RAG", "count": collection.count()}

@app.post("/add_memory")
def add_memory(item: MemoryItem):
    """
    保存记忆：同时写入 JSON (备份) 和 ChromaDB (检索)
    """
    # 1. 存 JSON
    saved_item, timestamp = save_json_memory(item.content, item.tags)
    
    # 2. 存 ChromaDB
    # 生成唯一 ID (简单起见用时间戳+哈希，或者 UUID)
    import hashlib
    doc_id = hashlib.md5((item.content + timestamp).encode()).hexdigest()
    
    collection.add(
        documents=[item.content],
        metadatas=[{"timestamp": timestamp, "tags": ",".join(item.tags)}],
        ids=[doc_id]
    )
    
    print(f"📥 Saved memory: {item.content[:30]}...")
    return {"status": "success", "data": saved_item}

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