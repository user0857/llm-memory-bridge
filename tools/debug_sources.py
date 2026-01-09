
import sys
import os

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import chromadb
from server.main import get_db_path

def inspect_sources():
    print("--- Inspecting Memory Sources ---")
    
    try:
        client = chromadb.PersistentClient(path=get_db_path())
        collection = client.get_or_create_collection("memories")
        
        # Get all items
        results = collection.get()
        
        ids = results['ids']
        metadatas = results['metadatas']
        documents = results['documents']
        
        unknown_count = 0
        total_count = len(ids)
        
        print(f"Total Memories: {total_count}\n")
        print(f"{ 'ID':<10} | { 'Source':<15} | {'Content (Snippet)'}")
        print("-" * 60)
        
        for i, meta in enumerate(metadatas):
            source = meta.get('source', 'MISSING')
            content = documents[i][:40].replace('\n', ' ') + "..."
            
            if source == 'MISSING' or source == 'unknown':
                unknown_count += 1
                # Highlight missing/unknown sources
                print(f"{ids[i][:8]:<10} | {str(source):<15} | {content}")
            else:
                # Optionally print correct ones too to verify legitimate ones
                # print(f"{ids[i][:8]:<10} | {source:<15} | {content}")
                pass

        print("-" * 60)
        print(f"Found {unknown_count} memories with missing or 'unknown' source.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_sources()
