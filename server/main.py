from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
import hashlib
import os # 确保 import os 存在且在顶层

# 导入 Gatekeeper
from agents.gatekeeper import get_gatekeeper

app = FastAPI(title="LLM Memory Bridge (Gatekeeper Enhanced)")

# --- 配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源 (生产环境建议限制为 chrome-extension://ID)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 ChromaDB
client = chromadb.PersistentClient(path=CHROMA_PATH)
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-MiniLM-L12-v2")

collection = client.get_or_create_collection(
    name="gemini_memory", 
    embedding_function=sentence_transformer_ef
)

# 在启动时获取 Gatekeeper 实例
gatekeeper = None

@app.on_event("startup")
async def startup_event():
    global gatekeeper
    gatekeeper = get_gatekeeper()

class MemoryItem(BaseModel):
    content: str
    tags: List[str] = []
    source: str = "unknown"
    source_url: Optional[str] = None

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
    force_save: Optional[bool] = False
    source: str = "unknown"
    source_url: Optional[str] = None

# --- 内部工具 ---

def _internal_save_memory(content: str, tags: List[str], source: str = "unknown", source_url: str = None):
    # Append Source/URL to content for better RAG visibility
    content_footer = []
    if source and source != "unknown":
        content_footer.append(f"Source: {source}")
    if source_url:
        content_footer.append(f"URL: {source_url}")
    
    final_content = content
    if content_footer:
        final_content += f"\n\n[{' | '.join(content_footer)}]"

    timestamp = datetime.now().isoformat()
    doc_id = hashlib.md5((final_content + timestamp).encode()).hexdigest()
    
    metadata = {
        "timestamp": timestamp,
        "tags": ",".join(tags),
        "source": source
    }
    if source_url:
        metadata["source_url"] = source_url

    collection.add(
        documents=[final_content],
        metadatas=[metadata],
        ids=[doc_id]
    )
    return doc_id

def _internal_update_memory(memory_id: str, new_content: str):
    timestamp = datetime.now().isoformat()
    # We update timestamp on edit, but keep original source info if possible (limitation: chroma update overwrites metadata if provided)
    # For now, just update timestamp to show freshness.
    collection.update(
        ids=[memory_id],
        documents=[new_content],
        metadatas=[{"timestamp": timestamp}]
    )

# --- 核心 API ---

@app.get("/")
def read_root():
    return {"status": "running", "agent": "Gatekeeper (Gemini)", "count": collection.count()}

@app.post("/api/gatekeeper/ingest")
async def gatekeeper_ingest(req: IngestRequest):
    """
    智能摄入接口：让 Gatekeeper 决定如何处理输入
    """
    if not gatekeeper:
        raise HTTPException(status_code=503, detail="Gatekeeper is not ready (Check API Key).")
    
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
            if dist < 1.5:
                context_parts.append(f"[ID: {id_}] {doc}")
        context_str = "\n".join(context_parts)

    final_context = req.context or context_str
    
    # 调用 Gatekeeper (Pass source_url for context)
    decision = gatekeeper.process(req.text, final_context, force_save=req.force_save, source_url=req.source_url)
    
    print(f"🧐 Gatekeeper's Decision (ForceSave={req.force_save}): {decision.get('thought')}")
    
    tool = decision.get("tool")
    args = decision.get("args", {})
    
    result = {"decision": decision, "context_provided": bool(final_context)}
    
    if tool == "save_memory":
        # CRITICAL FIX: Ensure source and source_url from the request are used, 
        # unless the agent explicitly provides overrides (which is rare for these fields).
        doc_id = _internal_save_memory(
            content=args.get("content"), 
            tags=args.get("tags", []),
            source=req.source,         # Use the original source from request
            source_url=req.source_url  # Use the original URL from request
        )
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
    doc_id = _internal_save_memory(item.content, item.tags, item.source, item.source_url)
    return {"status": "success", "data": {"id": doc_id}}

@app.post("/api/update")
def update_memory_api(req: UpdateRequest):
    _internal_update_memory(req.memory_id, req.new_content)
    return {"status": "success", "message": "Updated"}

@app.post("/api/search")
def api_search(query: QueryRequest):
    num_results = query.n_results if query.n_results else 5
    results = collection.query(
        query_texts=[query.user_input],
        n_results=num_results
    )
    
    if not results['documents'] or not results['documents'][0]:
        return {"results": []}

    structured_results = []
    docs = results['documents'][0]
    ids = results['ids'][0]
    metadatas = results['metadatas'][0]
    distances = results['distances'][0]

    threshold = query.threshold if query.threshold is not None else 1.5
    
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
    try:
        collection.delete(ids=[req.memory_id])
        return {"status": "success", "message": f"Memory {req.memory_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
