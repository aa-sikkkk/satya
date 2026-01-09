
import os
import sys
import glob
import logging
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from scripts.rag_data_preparation.enhanced_chunker import EnhancedChunker
except ImportError:
    # Handle if running from scripts/ dir directly
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
    from rag_data_preparation.enhanced_chunker import EnhancedChunker

import fitz # PyMuPDF

# Self-Diagnosis for PyMuPDF
if not hasattr(fitz, 'open'):
    logger.error("❌ CRITICAL ERROR: You have the WRONG 'fitz' package installed.")
    logger.error("   The 'fitz' package on PyPI is NOT PyMuPDF. It breaks everything.")
    logger.error("   👉 FIX: Run this command immediately:")
    logger.error("   pip uninstall -y fitz frontend && pip install --force-reinstall pymupdf")
    sys.exit(1)

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extracts text from a PDF file using PyMuPDF."""
    text_content = []
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text_content.append(page.get_text())
        return "\n".join(text_content)
    except Exception as e:
        logger.error(f"   ❌ PDF Read Error {pdf_path.name}: {e}")
        return ""

def ingest_directory(input_dir: str, db_path: str):
    """
    Ingests all .txt, .jsonl, .md, AND .pdf source files from a directory into ChromaDB.
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        logger.warning(f"⚠️ Input directory not found: {input_dir} (Skipping)")
        return

    logger.info(f"\n🚀 Ingesting Directory: {input_dir}")
    
    # Initialize Components (Lazy load model if needed, but here we assume it's loaded)
    # To save memory, we could load model inside here, or pass it in. 
    # For script simplicity, we'll reload or assume global. 
    # Let's clean up component init to be outside loop if possible, but for now specific per dir is fine or better yet moves to main.
    
    # We will instantiate components INSIDE main to avoid re-loading model per directory
    pass

def process_ingestion(inputs: List[str], db_path: str):
    logger.info(f"⚡ Loading Embedding Model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu') 
    
    logger.info("📚 Opening ChromaDB...")
    client = chromadb.PersistentClient(path=db_path)
    
    chunker = EnhancedChunker(chunk_size=512, overlap_ratio=0.1)
    
    for input_dir in inputs:
        input_path = Path(input_dir)
        if not input_path.exists():
            logger.warning(f"⚠️ Directory not found: {input_dir}")
            continue
            
        # Find Files (Recursive)
        files = list(input_path.rglob("*.txt")) + list(input_path.rglob("*.jsonl")) + list(input_path.rglob("*.md")) + list(input_path.rglob("*.pdf"))
        logger.info(f"📂 Scanning {input_dir}: Found {len(files)} files.")

        for file_path in files:
            logger.info(f"📄 Processing: {file_path.name}")
            
                # ---------------------------------------------------------
            # SMART METADATA EXTRACTION
            # ---------------------------------------------------------
            # 1. Detect Grade from Path (e.g. "grade_10", "class_10")
            grade = "unknown"
            for part in file_path.parts:
                if "grade_" in part.lower():
                    grade = part.lower().replace("grade_", "")
                    break
                if "class_" in part.lower():
                    grade = part.lower().replace("class_", "")
                    break
            
            # If not in path, try filename
            if grade == "unknown":
                if "grade_10" in file_path.name.lower(): grade = "10"
                elif "grade_11" in file_path.name.lower(): grade = "11"
                elif "grade_12" in file_path.name.lower(): grade = "12"

            # 2. Construct Collection Name (Ensure it has grade)
            clean_stem = "".join(c for c in file_path.stem if c.isalnum() or c == "_").lower()
            
            # If filename is just "science" but in "grade_10" folder -> "neb_science_grade_10"
            if grade != "unknown" and f"grade_{grade}" not in clean_stem:
                collection_name = f"neb_{clean_stem}_grade_{grade}"
            else:
                collection_name = clean_stem
                if not collection_name.startswith("neb_"):
                    collection_name = "neb_" + collection_name

            logger.info(f"   Target Collection: {collection_name}")

            # 3. Read Content
            content = ""
            try:
                if file_path.suffix.lower() == '.pdf':
                    content = extract_text_from_pdf(file_path)
                else:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
            except Exception as e:
                logger.error(f"   ❌ Failed to read file: {e}")
                continue
                
            if not content.strip():
                continue

            # 4. Chunk
            chunks = chunker.smart_chunk_with_overlap(content)
            logger.info(f"   Created {len(chunks)} chunks.")
            
            if not chunks:
                continue

            # 5. Embed & Store
            try:
                collection = client.get_or_create_collection(name=collection_name)
                
                texts = [c['text'] for c in chunks]
                embeddings = model.encode(texts, convert_to_numpy=True).tolist()
                
                ids = [f"{collection_name}_{i}" for i in range(len(chunks))]
                
                # ENHANCED METADATA
                metadatas = [{
                    'source': file_path.name,
                    'type': 'neb_curriculum',
                    'grade': grade,
                    'subject': clean_stem.replace(f"_grade_{grade}", "").replace("neb_", "") 
                } for _ in chunks]
                
                batch_size = 100
                for i in range(0, len(ids), batch_size):
                    end = min(i + batch_size, len(ids))
                    collection.upsert(
                        ids=ids[i:end],
                        embeddings=embeddings[i:end],
                        documents=texts[i:end],
                        metadatas=metadatas[i:end]
                    )
                logger.info("   ✅ Ingested successfully.")
                
            except Exception as e:
                logger.error(f"   ❌ DB Error: {e}")

    logger.info("\n✨ All Custom Data Ingested!")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest local books into RAG DB")
    parser.add_argument("--input", nargs='*', help="Folder(s) containing text/md/pdf files")
    
    # Auto-detect DB path
    auto_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "satya_data", "chroma_db")
    parser.add_argument("--db", default=auto_db_path, help="Path to ChromaDB")
    
    args = parser.parse_args()
    
    dirs_to_process = []
    if args.input:
        dirs_to_process = args.input
    else:
        # Default behavior: Search for standard 'textbooks' and 'notes' folders
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        defaults = ["textbooks", "notes"]
        for d in defaults:
            p = os.path.join(project_root, d)
            if os.path.exists(p):
                dirs_to_process.append(p)
        
        if not dirs_to_process:
            logger.warning("No input provided and no default 'textbooks'/'notes' folders found.")
            sys.exit(0)
    
    process_ingestion(dirs_to_process, args.db)
