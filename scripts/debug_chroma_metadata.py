
import chromadb
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MetaDataDebugger")

def check_metadata():
    db_path = "satya_data/chroma_db"
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        logger.info(f"✅ Connected to DB at {db_path}")
        
        target_cols = ["openstax_science", "neb_science_grade_10"]
        
        for name in target_cols:
            try:
                col = client.get_collection(name)
                count = col.count()
                logger.info(f"\n🔍 Inspecting Collection: {name} (Count: {count})")
                
                if count > 0:
                    res = col.peek(1)
                    meta = res['metadatas'][0]
                    logger.info(f"   Sample Metadata Keys: {list(meta.keys())}")
                    logger.info(f"   Sample Metadata Values: {meta}")
                else:
                    logger.warning("   ⚠️ Collection is empty!")
                    
            except Exception as e:
                logger.warning(f"   ❌ Could not access {name}: {e}")

    except Exception as e:
        logger.error(f"❌ DB Error: {e}")

if __name__ == "__main__":
    check_metadata()
