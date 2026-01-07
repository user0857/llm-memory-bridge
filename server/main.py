from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
import hashlib
import os

# 导入 Librarian
from agents.librarian import get_librarian

app = FastAPI(title="LLM Memory Bridge (Librarian Agentic)")

# --- 配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

# 初始化 ChromaDB
client = chromadb.PersistentClient(path=CHROMA_PATH)
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")

collection = client.get_or_create_collection(
    name="gemini_memory", 
    embedding_function=sentence_transformer_ef
)

# 在启动时获取 Librarian 实例
librarian = None

@app.on_event("startup")
async def startup_event():
    global librarian
    librarian = get_librarian()

class MemoryItem(BaseModel):
    content: str
    timestamp: Optional[str] = None
    tags: List[str] = []

class QueryRequest(BaseModel):
    user_input: str
    threshold: Optional[float] = None
    n_results: Optional[int] = 5

class DeleteRequest(BaseModel):
    memory_id: str

class UpdateRequest(BaseModel):
    memory_id: str
    new_content: str
    new_tags: Optional[List[str]] = None

class IngestRequest(BaseModel):
    text: str
    context: Optional[str] = None

# --- Librarian 内部工具 (仅供内部逻辑调用) ---

def _internal_save_memory(content: str, tags: List[str]):
    timestamp = datetime.now().isoformat()
    doc_id = hashlib.md5((content + timestamp).encode()).hexdigest()
    collection.add(
        documents=[content],
        metadatas=[{"timestamp": timestamp, "tags": ",".join(tags)}],
        ids=[doc_id]
    )
    return doc_id

def _internal_update_memory(memory_id: str, new_content: str):
    timestamp = datetime.now().isoformat()
    collection.update(
        ids=[memory_id],
        documents=[new_content],
        metadatas=[{"timestamp": timestamp}]
    )

# --- 核心 API ---

@app.get("/")
def read_root():
    return {"status": "running", "agent": "Librarian", "count": collection.count()}

@app.post("/api/librarian/ingest")
async def librarian_ingest(req: IngestRequest):
    """
    智能摄入接口：让 Librarian 决定如何处理输入
    """
    if not librarian:
        raise HTTPException(status_code=503, detail="Librarian is still sleeping...")
    
    # 0. 自动搜索上下文 (帮助 Librarian 判断是否是更新)
    context_str = ""
    search_results = collection.query(
        query_texts=[req.text],
        n_results=3
    )
    if search_results['documents'] and search_results['documents'][0]:
        context_parts = []
        for i in range(len(search_results['documents'][0])):
            doc = search_results['documents'][0][i]
            id_ = search_results['ids'][0][i]
            dist = search_results['distances'][0][i]
            # 仅提供相关度较高的记忆作为参考
            if dist < 1.5:
                context_parts.append(f"[ID: {id_}] {doc}")
        context_str = "\n".join(context_parts)

    # 1. 询问 Librarian 的意见
    # 优先使用请求自带的 context，如果没有则使用自动搜索的
    final_context = req.context or context_str
    decision = librarian.process(req.text, final_context)
    
    print(f"🧐 Librarian's Decision: {decision.get('thought')}")
    
    tool = decision.get("tool")
    args = decision.get("args", {})
    
    # 2. 根据决策执行工具
    result = {"decision": decision, "context_provided": bool(final_context)}
    
    if tool == "save_memory":
        doc_id = _internal_save_memory(args.get("content"), args.get("tags", []))
        result["action_result"] = f"Saved with ID {doc_id}"
    elif tool == "update_memory":
        _internal_update_memory(args.get("memory_id"), args.get("new_content"))
        result["action_result"] = f"Updated ID {args.get('memory_id')}"
    elif tool == "discard":
        result["action_result"] = f"Discarded: {args.get('reason')}"
    else:
        result["action_result"] = "No action taken or unknown tool"
        
    return result

@app.post("/add_memory")
def add_memory(item: MemoryItem):
    """
    (Legacy) 直接保存记忆
    """
    doc_id = _internal_save_memory(item.content, item.tags)
    return {"status": "success", "data": {"id": doc_id}}

@app.post("/api/update")
def update_memory(req: UpdateRequest):
    """
    (Legacy) 直接更新记忆
    """
    _internal_update_memory(req.memory_id, req.new_content)
    return {"status": "success", "message": "Updated"}

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
