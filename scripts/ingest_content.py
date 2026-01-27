# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Satya Universal Content Ingestion Script

Handles ALL content types:
- Regular PDFs (text-based)
- Scanned PDFs (OCR with Tesseract)
- Handwritten notes (OCR with EasyOCR)
- Text files (TXT, MD, JSONL)

Auto-detects content type and applies appropriate processing.

Usage:
    python scripts/ingest_content.py
    python scripts/ingest_content.py --input notes textbooks
    python scripts/ingest_content.py --ocr-mode auto  # auto-detect OCR need
    python scripts/ingest_content.py --ocr-mode force # force OCR on all PDFs
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import fitz  # PyMuPDF


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.rag_data_preparation.enhanced_chunker import EnhancedChunker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TESSERACT_AVAILABLE = False
EASYOCR_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    logger.warning("Tesseract not available. Install: pip install pytesseract pillow")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    logger.warning("EasyOCR not available. Install: pip install easyocr")


class UniversalContentIngester:
    """Handles all content types with auto-detection."""
    
    def __init__(self, db_path: str, ocr_mode: str = "auto"):
        """
        Args:
            db_path: Path to ChromaDB
            ocr_mode: "auto" (detect), "force" (always OCR), "never" (text only)
        """
        self.db_path = db_path
        self.ocr_mode = ocr_mode
        
        logger.info("Loading Embedding Model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        
        logger.info("Opening ChromaDB...")
        self.client = chromadb.PersistentClient(path=db_path)
        
        self.chunker = EnhancedChunker(chunk_size=512, overlap_ratio=0.1)
        
        # Initialize OCR readers (lazy)
        self.easyocr_reader = None
        if EASYOCR_AVAILABLE and ocr_mode != "never":
            logger.info("Loading EasyOCR (for handwritten notes)...")
            self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
    
    def detect_pdf_type(self, pdf_path: Path) -> str:
        """
        Detect if PDF is text-based or scanned.
        Returns: "text", "scanned", or "handwritten"
        """
        try:
            with fitz.open(pdf_path) as doc:
                # Sample first 3 pages
                text_chars = 0
                for page_num in range(min(3, len(doc))):
                    page = doc[page_num]
                    text = page.get_text()
                    text_chars += len(text.strip())
                
                # If very little text, likely scanned
                if text_chars < 100:
                    return "scanned"
                return "text"
        except Exception as e:
            logger.error(f"PDF detection error: {e}")
            return "text"  # Fallback
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from regular PDF."""
        try:
            with fitz.open(pdf_path) as doc:
                return "\n".join(page.get_text() for page in doc)
        except Exception as e:
            logger.error(f"PDF read error: {e}")
            return ""
    
    def extract_text_with_tesseract(self, pdf_path: Path) -> str:
        """Extract text from scanned PDF using Tesseract OCR."""
        if not TESSERACT_AVAILABLE:
            logger.error("Tesseract not available!")
            return ""
        
        try:
            text_parts = []
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc):
                    # Convert page to image
                    pix = page.get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # OCR
                    text = pytesseract.image_to_string(img, lang='eng')
                    text_parts.append(text)
                    
                    logger.info(f"   OCR page {page_num + 1}/{len(doc)}")
            
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return ""
    
    def extract_text_with_easyocr(self, pdf_path: Path) -> str:
        """Extract text from handwritten notes using EasyOCR."""
        if not self.easyocr_reader:
            logger.error("EasyOCR not available!")
            return ""
        
        try:
            text_parts = []
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc):
                    # Convert page to image
                    pix = page.get_pixmap(dpi=300)
                    img_bytes = pix.tobytes("png")
                    
                    # Save temp image
                    temp_img = f"temp_page_{page_num}.png"
                    with open(temp_img, 'wb') as f:
                        f.write(img_bytes)
                    
                    # OCR
                    results = self.easyocr_reader.readtext(temp_img)
                    text = "\n".join([r[1] for r in results])
                    text_parts.append(text)
                    
                    # Cleanup
                    os.remove(temp_img)
                    
                    logger.info(f"   EasyOCR page {page_num + 1}/{len(doc)}")
            
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return ""
    
    def process_file(self, file_path: Path) -> Optional[str]:
        """
        Process any file type and return extracted text.
        Auto-detects best extraction method.
        """
        logger.info(f"📄 Processing: {file_path.name}")
        
        # Text files
        if file_path.suffix.lower() in ['.txt', '.md', '.jsonl']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Text file error: {e}")
                return None
        
        # PDFs
        if file_path.suffix.lower() == '.pdf':
            # Auto-detect or force OCR
            if self.ocr_mode == "force":
                pdf_type = "scanned"
            elif self.ocr_mode == "never":
                pdf_type = "text"
            else:  # auto
                pdf_type = self.detect_pdf_type(file_path)
            
            logger.info(f"   Detected type: {pdf_type}")
            
            if pdf_type == "text":
                return self.extract_text_from_pdf(file_path)
            elif pdf_type == "scanned":
                # Try EasyOCR first (better for handwritten), fallback to Tesseract
                if self.easyocr_reader:
                    return self.extract_text_with_easyocr(file_path)
                elif TESSERACT_AVAILABLE:
                    return self.extract_text_with_tesseract(file_path)
                else:
                    logger.error("No OCR engine available!")
                    return None
        
        logger.warning(f"Unsupported file type: {file_path.suffix}")
        return None
    
    def extract_metadata(self, file_path: Path) -> Dict[str, str]:
        """Extract grade and subject from file path."""
        # Detect grade
        grade = "unknown"
        for part in file_path.parts:
            if "grade_" in part.lower():
                grade = part.lower().replace("grade_", "")
                break
            if "class_" in part.lower():
                grade = part.lower().replace("class_", "")
                break
        
        # Detect subject from filename
        clean_stem = "".join(c for c in file_path.stem if c.isalnum() or c == "_").lower()
        subject = clean_stem.replace(f"_grade_{grade}", "").replace("neb_", "")
        
        # Collection name
        if grade != "unknown" and f"grade_{grade}" not in clean_stem:
            collection_name = f"neb_{subject}_grade_{grade}"
        else:
            collection_name = clean_stem if clean_stem.startswith("neb_") else f"neb_{clean_stem}"
        
        return {
            "grade": grade,
            "subject": subject,
            "collection_name": collection_name
        }
    
    def ingest_directory(self, input_dir: str):
        """Ingest all supported files from a directory."""
        input_path = Path(input_dir)
        if not input_path.exists():
            logger.warning(f"Directory not found: {input_dir}")
            return
        
        logger.info(f"\n Ingesting: {input_dir}")
        
        # Find all supported files
        files = (
            list(input_path.rglob("*.pdf")) +
            list(input_path.rglob("*.txt")) +
            list(input_path.rglob("*.md")) +
            list(input_path.rglob("*.jsonl"))
        )
        
        logger.info(f"Found {len(files)} files")
        
        for file_path in tqdm(files, desc="Processing files"):
            # Extract content
            content = self.process_file(file_path)
            if not content or not content.strip():
                continue
            
            # Extract metadata
            metadata = self.extract_metadata(file_path)
            collection_name = metadata["collection_name"]
            
            logger.info(f"   → Collection: {collection_name}")
            
            # Chunk
            chunks = self.chunker.smart_chunk_with_overlap(content)
            if not chunks:
                continue
            
            # Embed & Store
            try:
                collection = self.client.get_or_create_collection(name=collection_name)
                
                texts = [c['text'] for c in chunks]
                embeddings = self.model.encode(texts, convert_to_numpy=True).tolist()
                
                ids = [f"{collection_name}_{i}" for i in range(len(chunks))]
                metadatas = [{
                    'source': file_path.name,
                    'type': 'neb_curriculum',
                    'grade': metadata['grade'],
                    'subject': metadata['subject']
                } for _ in chunks]
                
                # Batch upsert
                batch_size = 100
                for i in range(0, len(ids), batch_size):
                    end = min(i + batch_size, len(ids))
                    collection.upsert(
                        ids=ids[i:end],
                        embeddings=embeddings[i:end],
                        documents=texts[i:end],
                        metadatas=metadatas[i:end]
                    )
                
                logger.info(f"Ingested {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f" DB error: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Universal Content Ingestion")
    parser.add_argument("--input", nargs='*', help="Folders to ingest")
    parser.add_argument("--ocr-mode", choices=['auto', 'force', 'never'], default='auto',
                        help="OCR mode: auto (detect), force (always), never (text only)")
    
    # Auto-detect DB path
    auto_db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "satya_data", "chroma_db"
    )
    parser.add_argument("--db", default=auto_db_path, help="ChromaDB path")
    
    args = parser.parse_args()
    
    # Determine input directories
    dirs_to_process = []
    if args.input:
        dirs_to_process = args.input
    else:
        # Default: notes and textbooks
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for d in ["textbooks", "notes"]:
            p = os.path.join(project_root, d)
            if os.path.exists(p):
                dirs_to_process.append(p)
        
        if not dirs_to_process:
            logger.warning("No input provided and no default folders found.")
            sys.exit(0)
    
    # Run ingestion
    ingester = UniversalContentIngester(args.db, args.ocr_mode)
    for dir_path in dirs_to_process:
        ingester.ingest_directory(dir_path)
    
    logger.info("\n All content ingested successfully!")


if __name__ == "__main__":
    main()
