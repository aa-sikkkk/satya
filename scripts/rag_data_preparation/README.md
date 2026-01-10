# RAG Data Preparation Pipeline

## Overview

The Satya RAG data preparation pipeline processes educational content (textbooks, notes, handwritten materials) into a vector database for retrieval-augmented generation. The system supports multiple content types with automatic detection and appropriate processing.

---

## Quick Start

### Single Command Processing

Process all content (textbooks and notes):

```bash
python scripts/ingest_content.py
```

This command will:
1. Scan `textbooks/` and `notes/` directories
2. Auto-detect content type for each file
3. Apply appropriate extraction method
4. Generate embeddings
5. Store in ChromaDB

---

## System Architecture

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **ingest_content.py** | Universal ingestion script | `scripts/` |
| **enhanced_chunker.py** | Smart text chunking | `scripts/rag_data_preparation/` |
| **embedding_generator.py** | Embedding generation | `scripts/rag_data_preparation/` |

### Content Processing Flow

```
Input Files (PDF/TXT/MD)
    ↓
Content Type Detection
    ↓
Extraction (PyMuPDF/Tesseract/EasyOCR)
    ↓
Smart Chunking (512 tokens, 10% overlap)
    ↓
Embedding Generation (all-MiniLM-L6-v2)
    ↓
ChromaDB Storage
```

---

## Supported Content Types

### Text-Based PDFs

**Detection:** Automatic text extraction succeeds  
**Processing:** PyMuPDF direct extraction  
**Use case:** Digital textbooks, typed notes

### Scanned PDFs

**Detection:** Minimal text extraction  
**Processing:** Tesseract OCR  
**Use case:** Scanned textbooks, photocopied materials

### Handwritten Notes

**Detection:** Manual flag or poor OCR quality  
**Processing:** EasyOCR (better handwriting recognition)  
**Use case:** Teacher handwritten notes, student annotations

### Text Files

**Formats:** .txt, .md, .jsonl  
**Processing:** Direct reading  
**Use case:** Markdown notes, structured data

---

## Installation

### Required Dependencies

```bash
pip install pymupdf sentence-transformers chromadb
```

### Optional OCR Dependencies

**For scanned PDFs:**
```bash
pip install pytesseract pillow

# System dependency (Windows)
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

# System dependency (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

**For handwritten notes:**
```bash
pip install easyocr
```

---

## Usage

### Basic Usage

**Process everything:**
```bash
python scripts/ingest_content.py
```

**Process specific folders:**
```bash
python scripts/ingest_content.py --input textbooks notes
```

### OCR Modes

**Auto-detect (default):**
```bash
python scripts/ingest_content.py --ocr-mode auto
```

**Force OCR on all PDFs:**
```bash
python scripts/ingest_content.py --ocr-mode force
```

**Never use OCR (text-only):**
```bash
python scripts/ingest_content.py --ocr-mode never
```

### Custom Database Path

```bash
python scripts/ingest_content.py --db /path/to/chroma_db
```

---

## Directory Structure

### Input Structure

```
Satya/
├── textbooks/
│   └── grade_10/
│       ├── computer_science.pdf
│       ├── english.pdf
│       └── science.pdf
├── notes/
│   └── grade_10/
│       ├── cs_notes.pdf
│       ├── english_summary.md
│       └── science_revision.txt
└── scripts/
    └── ingest_content.py
```

### Output Structure

```
satya_data/
└── chroma_db/
    ├── neb_computer_science_grade_10/
    ├── neb_english_grade_10/
    ├── neb_science_grade_10/
    ├── neb_computer_science_notes_grade_10/
    ├── neb_english_notes_grade_10/
    └── neb_science_notes_grade_10/
```

---

## Chunking Strategy

### Parameters

- **Chunk size:** 512 tokens
- **Overlap:** 10% (51 tokens)
- **Strategy:** Sentence-boundary aware

### Rationale

**512 tokens:**
- Optimal for Phi 1.5 context window
- Balances detail vs. retrieval precision
- Fits within embedding model limits

**10% overlap:**
- Prevents context loss at boundaries
- Improves retrieval recall
- Minimal storage overhead

---

## Metadata Schema

Each chunk includes:

```python
{
    "source": "filename.pdf",
    "type": "neb_curriculum",
    "grade": "10",
    "subject": "computer_science"
}
```

### Metadata Extraction

**Grade detection:**
- From folder name: `grade_10/` → `"10"`
- From filename: `science_grade_10.pdf` → `"10"`
- Fallback: `"unknown"`

**Subject detection:**
- From filename: `computer_science_notes.pdf` → `"computer_science"`
- Cleaned and normalized automatically

---

## ChromaDB Collections

### Naming Convention

**Textbooks:**
```
neb_{subject}_grade_{grade}
```

**Notes:**
```
neb_{subject}_notes_grade_{grade}
```

### Collection Management

**List all collections:**
```python
import chromadb

client = chromadb.PersistentClient(path='satya_data/chroma_db')
collections = client.list_collections()

for c in collections:
    print(f"{c.name}: {c.count()} chunks")
```

**Query a collection:**
```python
collection = client.get_collection('neb_computer_science_grade_10')
results = collection.query(
    query_texts=["What is a variable?"],
    n_results=5
)
```

---

## Performance Considerations

### Processing Speed

**Text PDFs:** ~1-2 pages/second  
**Scanned PDFs (Tesseract):** ~2-5 seconds/page  
**Handwritten (EasyOCR):** ~5-10 seconds/page

### Optimization Tips

1. **Use text PDFs when possible** - Significantly faster
2. **Batch processing** - Process multiple files in one run
3. **CPU threads** - Adjust based on available cores
4. **Skip re-processing** - Collections are additive

---

## Troubleshooting

### Common Issues

**Issue:** "No files found"

**Solution:**
- Verify files are in correct directories
- Check file extensions (.pdf, .txt, .md)
- Ensure read permissions

---

**Issue:** "OCR failed"

**Solution:**
- Install OCR dependencies
- Check image quality (300 DPI recommended)
- Try different OCR mode

---

**Issue:** "Embedding generation slow"

**Solution:**
- Use CPU-optimized sentence-transformers
- Process in smaller batches
- Consider GPU if available

---

**Issue:** "Collection already exists"

**Solution:**
- This is normal - collections are additive
- Use `collection.count()` to verify chunks added
- Delete collection if full rebuild needed

---

## Advanced Usage

### Python API

```python
from scripts.ingest_content import UniversalContentIngester

# Initialize
ingester = UniversalContentIngester(
    db_path='satya_data/chroma_db',
    ocr_mode='auto'
)

# Process directory
ingester.ingest_directory('notes/grade_10')

# Verify
import chromadb
client = chromadb.PersistentClient(path='satya_data/chroma_db')
print(client.list_collections())
```

### Custom Chunking

```python
from scripts.rag_data_preparation.enhanced_chunker import EnhancedChunker

chunker = EnhancedChunker(
    chunk_size=512,
    overlap_ratio=0.1
)

chunks = chunker.smart_chunk_with_overlap(
    text="Your content here",
    metadata={"subject": "science", "grade": "10"}
)
```

---

## Best Practices

1. **Organize by grade** - Maintain grade-specific folders
2. **Consistent naming** - Use clear, descriptive filenames
3. **Quality PDFs** - Prefer text PDFs over scanned
4. **Regular updates** - Re-ingest when content changes
5. **Verify ingestion** - Check collections after processing
6. **Backup database** - Periodically backup `chroma_db/`

---

## Additional Resources

- **Quick start:** `QUICK_START.md`
- **Notes guide:** `NOTES_GUIDE.md`
- **Textbooks README:** `../../textbooks/README.md`
- **Notes README:** `../../notes/README.md`