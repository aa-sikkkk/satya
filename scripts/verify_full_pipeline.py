
import os
import sys
import logging
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from system.rag.rag_retrieval_engine import RAGRetrievalEngine

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')
logger = logging.getLogger("SystemVerifier")

def verify_full_system():
    print("🚀 Starting Satya End-to-End System Verification...")
    print("-------------------------------------------------")
    
    try:
        # 1. Initialize Engine
        t0 = time.time()
        print("⚡ Initializing RAG Engine (Models + DB)...")
        rag_engine = RAGRetrievalEngine()
        print(f"✅ Initialization Complete in {time.time() - t0:.2f}s")
        
        # 2. Define Query
        # Using a topic likely in Grade 10 Science (NEB)
        query = "What is acceleration?" 
        subject = "science"
        grade = "10"
        
        print(f"\n❓ Query: '{query}'")
        print(f"   Context: Subject={subject}, Grade={grade}")
        
        # 3. Execute Query
        print("\n🧠 Processing Request...")
        t1 = time.time()
        response = rag_engine.query(query, subject, grade)
        t2 = time.time()
        
        # 4. Analyze Results
        print("\n✨ Response Received!")
        print(f"⏱️ Total Latency: {t2 - t1:.2f}s")
        
        print(f"\n📝 Answer:\n{response['answer']}")
        
        print("\n📚 Sources Used:")
        if response['sources']:
            for s in response['sources']:
                print(f"   - {s.get('source', 'Unknown')} (Type: {s.get('type', 'Unknown')})")
                
            # Verification Logic
            neb_found = any('neb_curriculum' in s.get('type', '') for s in response['sources'])
            if neb_found:
                print("\n✅ PASSED: Retrieved from NEB Curriculum!")
            else:
                print("\n⚠️ WARNING: NEB Curriculum NOT found in sources.")
        else:
            print("   (No sources found - Model answered from memory or failed)")
            
        if response['answer'] and len(response['answer']) > 20 and "placeholder" not in response['answer']:
            print("✅ PASSED: Satya AI generated a valid answer.")
        else:
            print("❌ FAILED: Satya AI did not generate a valid answer.")

    except Exception as e:
        print(f"\n❌ System Failure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_full_system()
