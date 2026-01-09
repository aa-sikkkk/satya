"""
Satya RAG Database Builder (Unified Pipeline)

Runs the complete data pipeline:
1. Download datasets (Grade 8-12 filtered) -> JSONL
2. Text Chunking (Math-aware) -> JSON
3. Generate semantic embeddings (all-MiniLM-L6-v2) -> JSON with embeddings
4. Build ChromaDB collections -> Vector DB
5. Clean up raw data to save space

Usage:
    python scripts/build_rag_db.py
"""

import os
import sys
import logging
import subprocess
import json
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
SCRIPTS_DIR = Path("scripts/rag_data_preparation")
RAW_DATA_DIR = Path("satya_data/raw_datasets")
PROCESSED_DIR = Path("satya_data/processed_chunks")

# Ensure paths match project structure
sys.path.append(os.getcwd())
try:
    from scripts.rag_data_preparation.enhanced_chunker import EnhancedChunker
except ImportError:
    try:
        from rag_data_preparation.enhanced_chunker import EnhancedChunker
    except ImportError:
        pass

def run_step(step_name, script_name, args=[]):
    """Run a pipeline step."""
    logger.info(f"\n{'='*60}")
    logger.info(f"Step: {step_name}")
    logger.info(f"{'='*60}")
    
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + args
    
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"✅ {step_name} complete!")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {step_name} failed with exit code {e.returncode}")
        # Don't exit immediately, let user see error
    except Exception as e:
        logger.error(f"❌ {step_name} failed: {e}")

def process_chunking():
    """
    Transform Step: JSONL -> Chunks JSON
    Uses EnhancedChunker to split text smartly.
    """
    logger.info("\n" + "="*60)
    logger.info("Step 2: Math-Aware Chunking")
    logger.info("="*60)
    
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize chunker
    try:
        from scripts.rag_data_preparation.enhanced_chunker import EnhancedChunker
    except ImportError:
        try:
            # Fallback if scripts is in path directly
            from rag_data_preparation.enhanced_chunker import EnhancedChunker
        except ImportError:
            # Fallback for direct execution context
            sys.path.append(str(SCRIPTS_DIR))
            from enhanced_chunker import EnhancedChunker

    chunker = EnhancedChunker(chunk_size=512, overlap_ratio=0.2)
    
    jsonl_files = list(RAW_DATA_DIR.glob("*.jsonl"))
    if not jsonl_files:
        logger.warning(f"No JSONL files found in {RAW_DATA_DIR}. Did download fail?")
        return

    for jsonl_file in jsonl_files:
        output_file = PROCESSED_DIR / f"{jsonl_file.stem}_chunks.json"
        if output_file.exists():
             logger.info(f"Skipping {jsonl_file.name}, already chunked.")
             continue
             
        logger.info(f"✂️ Chunking {jsonl_file.name}...")
        
        all_chunks = []
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        item = json.loads(line)
                        text = item.get('text') or item.get('content', '')
                        
                        # Prepare metadata
                        metadata = {
                            'source': item.get('source', 'unknown'),
                            'grade': item.get('grade'),
                            'subject': item.get('subject')
                        }
                        # Add any other metadata from item (excluding huge text fields)
                        for k, v in item.items():
                            if k not in ['text', 'content', 'chunks'] and isinstance(v, (str, int, float, bool)):
                                metadata[k] = v
                                
                        # Chunk it
                        chunks = chunker.smart_chunk_with_overlap(text, metadata)
                        all_chunks.extend(chunks)
                        
                    except json.JSONDecodeError:
                        continue
            
            # Save chunks
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({"chunks": all_chunks}, f, ensure_ascii=False)
                
            logger.info(f"✅ Saved {len(all_chunks)} chunks to {output_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to process {jsonl_file.name}: {e}")

def cleanup_raw_data():
    """Delete raw JSONL files to save space."""
    logger.info("\n🧹 Cleaning up raw data to save space (User Constraint <1.5GB)...")
    if RAW_DATA_DIR.exists():
        for file in RAW_DATA_DIR.glob("*.jsonl"):
            try:
                file.unlink()
                logger.info(f"Deleted {file.name}")
            except Exception as e:
                logger.warning(f"Could not delete {file.name}: {e}")
    logger.info("✅ Cleanup complete!")

def main():
    print("🚀 Starting Satya RAG Pipeline Build...")
    print("Target: Optimized for speed & accuracy on i3")
    
    # Step 1: Download
    run_step("1. Download Datasets", "dataset_downloader.py")
    
    # Step 2: Chunking (The Bridge)
    process_chunking()
    
    # Step 3: Embeddings
    # Iterate over processed chunks and run embedding generator
    logger.info("\n" + "="*60)
    logger.info("Step 3: Generate Embeddings")
    logger.info("="*60)
    # We pass the directory, embedding_generator handles globbing
    run_step("3. Generate Embeddings", "embedding_generator.py", [str(PROCESSED_DIR)])
    
    # Step 4: ChromaDB Build
    logger.info("\n" + "="*60)
    logger.info("Step 4: Build Vector DB")
    logger.info("="*60)
    
    # Initialize builder helper
    script_path = SCRIPTS_DIR / "chromadb_builder.py"
    
    # Iterate over embedded files
    files = list(PROCESSED_DIR.glob("*_chunks.json"))
    for f in files:
        # Check if it has embeddings (embedding_generator modifies in place or creates new? 
        # Looking at embedding_generator.py: "output_data = ... with open(output_file..." 
        # It overwrites input if no output specified? 
        # "generator.process_chunk_file(args.input, args.output)"
        # If output not specified, it likely overwrites or appends. 
        # In the main loop: "generator.process_chunk_file(str(f))" -> overwrites.
        # So we can just use the file.
        logger.info(f"database ingest: {f.name}")
        cmd = [sys.executable, str(script_path), str(f)]
        subprocess.run(cmd)

    # Step 5: Final Cleanup
    cleanup_raw_data()
    
    print("\n✨ Satya RAG Knowledge Base Built Successfully! ✨")

if __name__ == "__main__":
    main()
