
import chromadb
import os
import sys
from sentence_transformers import SentenceTransformer

def verify_db():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "satya_data")
    db_path = os.path.join(base_dir, "chroma_db")
    
    print(f"🔍 Verifying Database at: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ Database path does not exist!")
        return

    try:
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        
        if not collections:
            print("❌ Database exists but has NO collections (Empty).")
            return
            
        print(f"✅ Found {len(collections)} Collections:")
        
        total_docs = 0
        for col in collections:
            count = col.count()
            total_docs += count
            print(f"   - {col.name}: {count} docs")
            
        print(f"\n📊 Total Knowledge Base: {total_docs} Document Chunks")
        
        # Test Query
        print("\n🧠 Testing Knowledge Retrieval...")
        
        # We need the model to generate a query embedding
        print("   Loading embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        query_text = "What is the mitochondria?"
        print(f"   Query: '{query_text}'")
        query_vec = model.encode([query_text]).tolist()
        
        # Search the first collection with data
        target_col = None
        for col in collections:
            if col.count() > 0:
                target_col = col
                break
                
        if target_col:
            results = target_col.query(
                query_embeddings=query_vec,
                n_results=1
            )
            print(f"   Result from {target_col.name}:")
            print(f"   '{results['documents'][0][0][:100]}...'")
            print("✅ Retrieval Test Passed!")
        else:
            print("⚠️ No data to query.")

    except Exception as e:
        print(f"❌ Verification Failed: {e}")

if __name__ == "__main__":
    verify_db()
