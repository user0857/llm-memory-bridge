
import sys
import os
import chromadb

# Hardcode the DB path for inspection
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_PATH = os.path.join(BASE_DIR, "server", "chroma_db")

def inspect_chroma():
    print(f"Inspecting ChromaDB at: {CHROMA_PATH}")
    
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        # Note: server/main.py uses "gemini_memory"
        collection = client.get_collection("gemini_memory") 
        
        # Get all items
        results = collection.get() 
        
        ids = results['ids']
        metadatas = results['metadatas']
        documents = results['documents']
        
        print(f"\nTotal Memories: {len(ids)}\n")
        print(f"{ 'ID':<10} | { 'Source':<15} | {'Content (Snippet)'}")
        print("-" * 80)
        
        # Look for the IDs we just added
        target_ids = ["134af19bd04374ad37b573cfad14a30b"] 
        
        for i, meta in enumerate(metadatas):
            doc_id = ids[i]
            source = meta.get('source', 'MISSING')
            content = documents[i][:40].replace('\n', ' ') + "..."
            
            # Print if it's one of our targets OR if source is weird
            if doc_id in target_ids:
                print(f"✅ {doc_id[:8]:<8} | {str(source):<15} | {content}")
                print(f"   Full Metadata: {meta}")
            elif source == 'unknown' or source == 'MISSING':
                 # Limit output of old unknown items
                 pass 
                 # print(f"❌ {doc_id[:8]:<8} | {str(source):<15} | {content}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_chroma()
