# Quick Start Guide

## Single Command Processing

Process all educational content with one command:

```bash
python scripts/ingest_content.py
```

This processes textbooks and notes from both `textbooks/` and `notes/` directories.

---

## Prerequisites

### Required Dependencies

```bash
pip install pymupdf sentence-transformers chromadb
```

### Optional OCR Dependencies

**For scanned PDFs:**
```bash
pip install pytesseract pillow
```

**For handwritten notes:**
```bash
pip install easyocr
```

---

## Step-by-Step Workflow

### Step 1: Organize Content

**Textbooks:**
```
textbooks/grade_10/
├── computer_science.pdf
├── english.pdf
└── science.pdf
```

**Notes:**
```
notes/grade_10/
├── cs_notes.pdf
├── english_summary.md
└── science_revision.txt
```

### Step 2: Run Ingestion

**Process everything:**
```bash
python scripts/ingest_content.py
```

**Process only textbooks:**
```bash
python scripts/ingest_content.py --input textbooks
```

**Process only notes:**
```bash
python scripts/ingest_content.py --input notes
```

### Step 3: Verify Results

```python
import chromadb

client = chromadb.PersistentClient(path='satya_data/chroma_db')
collections = client.list_collections()

for c in collections:
    print(f"{c.name}: {c.count()} chunks")
```

---

## Processing Options

### OCR Modes

**Auto-detect (recommended):**
```bash
python scripts/ingest_content.py --ocr-mode auto
```

**Force OCR on all PDFs:**
```bash
python scripts/ingest_content.py --ocr-mode force
```

**Never use OCR:**
```bash
python scripts/ingest_content.py --ocr-mode never
```

### Custom Database Path

```bash
python scripts/ingest_content.py --db /custom/path/chroma_db
```

---

## Output Structure

### ChromaDB Collections

**Textbooks:**
- `neb_computer_science_grade_10`
- `neb_english_grade_10`
- `neb_science_grade_10`

**Notes:**
- `neb_computer_science_notes_grade_10`
- `neb_english_notes_grade_10`
- `neb_science_notes_grade_10`

### Database Location

```
satya_data/
└── chroma_db/
    ├── neb_computer_science_grade_10/
    ├── neb_english_grade_10/
    └── [other collections]
```

---

## Common Use Cases

### Adding New Content

1. **Add files** to `textbooks/grade_10/` or `notes/grade_10/`
2. **Run ingestion:**
   ```bash
   python scripts/ingest_content.py
   ```
3. **Verify:** Check collection counts

### Updating Existing Content

1. **Replace files** in respective directories
2. **Re-run ingestion** (collections are additive)
3. **Optional:** Delete old collection first for clean rebuild

### Processing Multiple Grades

```bash
# Create grade_11 folders
mkdir -p textbooks/grade_11 notes/grade_11

# Add content
# ...

# Process
python scripts/ingest_content.py
```

---

## Troubleshooting

### Issue: "No files found"

**Check:**
- Files are in correct directories
- File extensions are supported (.pdf, .txt, .md)
- Files have read permissions

### Issue: "OCR failed"

**Solutions:**
- Install OCR dependencies
- Verify image quality (300 DPI recommended)
- Try `--ocr-mode force`

### Issue: "Slow processing"

**Optimization:**
- Use text PDFs instead of scanned
- Process in smaller batches
- Check CPU usage

### Issue: "Collection already exists"

**Note:** This is normal behavior. Collections are additive.

**To rebuild:**
```python
import chromadb

client = chromadb.PersistentClient(path='satya_data/chroma_db')
client.delete_collection('neb_computer_science_grade_10')

# Then re-run ingestion
```

---

## Testing the RAG System

### Query Test

```python
from system.rag.rag_retrieval_engine import RAGRetrievalEngine

rag = RAGRetrievalEngine()
result = rag.query(
    query_text="What is a variable?",
    subject="computer_science"
)

print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence']}")
print(f"Sources: {len(result['sources'])}")
```

### Collection Inspection

```python
import chromadb

client = chromadb.PersistentClient(path='satya_data/chroma_db')
collection = client.get_collection('neb_computer_science_grade_10')

# Get sample chunks
sample = collection.peek(limit=3)
print(f"Sample chunks: {sample}")

# Get statistics
print(f"Total chunks: {collection.count()}")
```

---

## Next Steps

1. **Process your content** using the commands above
2. **Verify collections** are created successfully
3. **Test RAG queries** to ensure retrieval works
4. **Integrate with GUI** for student use

---

## Additional Resources

- **Detailed guide:** `README.md`
- **Notes strategy:** `NOTES_GUIDE.md`
- **Textbooks README:** `../../textbooks/README.md`
- **Notes README:** `../../notes/README.md`
- **Ingestion script:** `../ingest_content.py`
