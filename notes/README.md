# Notes Directory

## Purpose

This directory contains **teacher-created study notes and supplementary materials** for the Satya RAG system. Notes are processed separately from textbooks and stored in dedicated ChromaDB collections for flexible retrieval.

---

## Directory Structure

```
notes/
├── grade_10/
│   ├── computer_science_notes.pdf
│   ├── english_notes.pdf
│   ├── science_notes.pdf
│   └── [additional notes files]
├── grade_11/              # Future expansion
└── README.md              # This file
```

---

## File Organization

### Naming Convention

Files can be named flexibly. The ingestion script will:
- Auto-detect subject from filename
- Extract grade from folder structure
- Support multiple files per subject

**Recommended naming patterns:**
- `{subject}_notes.pdf`
- `{subject}_summary.pdf`
- `{subject}_revision.pdf`

**Examples:**
- `computer_science_notes.pdf`
- `english_grammar_summary.pdf`
- `science_revision.pdf`

### Supported Formats

- **PDF** (text-based or scanned)
- **Text files** (.txt, .md)
- **JSONL** (structured data)

---

## Processing Notes

### Quick Start

Process all notes with a single command:

```bash
python scripts/ingest_content.py --input notes
```

This will:
1. Scan all files in `notes/grade_10/`
2. Auto-detect content type (text PDF, scanned PDF, handwritten)
3. Apply appropriate extraction (PyMuPDF, Tesseract OCR, or EasyOCR)
4. Create optimized chunks (512 tokens, 10% overlap)
5. Generate embeddings
6. Store in ChromaDB collections

### Processing Options

**Process notes and textbooks together:**
```bash
python scripts/ingest_content.py
```

**Force OCR on all PDFs:**
```bash
python scripts/ingest_content.py --input notes --ocr-mode force
```

**Skip OCR (text-only PDFs):**
```bash
python scripts/ingest_content.py --input notes --ocr-mode never
```

---

## ChromaDB Collections

Notes are stored in separate collections from textbooks:

**Textbook collections:**
- `neb_computer_science_grade_10`
- `neb_english_grade_10`
- `neb_science_grade_10`

**Notes collections:**
- `neb_computer_science_notes_grade_10`
- `neb_english_notes_grade_10`
- `neb_science_notes_grade_10`

### Collection Metadata

Each chunk includes:
- `source`: Original filename
- `type`: `"neb_curriculum"`
- `grade`: Extracted from folder structure
- `subject`: Detected from filename

---

## Notes vs Textbooks

| Aspect | Textbooks | Notes |
|--------|-----------|-------|
| **Location** | `textbooks/grade_10/` | `notes/grade_10/` |
| **Collection** | `neb_{subject}_grade_10` | `neb_{subject}_notes_grade_10` |
| **Content** | Comprehensive curriculum | Summaries, quick references |
| **Purpose** | Primary reference | Supplementary material |
| **Search** | Included in all queries | Included in all queries |

**Both are searched together** by the RAG system for comprehensive answers.

---

## Updating Notes

To add or update notes:

1. **Add/replace files** in `notes/grade_10/`
2. **Run ingestion:**
   ```bash
   python scripts/ingest_content.py --input notes
   ```
3. **Verify results:**
   ```bash
   python -c "
   import chromadb
   client = chromadb.PersistentClient(path='satya_data/chroma_db')
   collections = client.list_collections()
   for c in collections:
       print(f'{c.name}: {c.count()} chunks')
   "
   ```

**Note:** Re-running ingestion will add new content without deleting existing chunks.

---

## Verification

### Check Collection Contents

```python
import chromadb

client = chromadb.PersistentClient(path='satya_data/chroma_db')
collection = client.get_collection('neb_computer_science_notes_grade_10')

print(f"Total chunks: {collection.count()}")
print(f"Sample: {collection.peek(limit=1)}")
```

### Test Search

```python
from system.rag.rag_retrieval_engine import RAGRetrievalEngine

rag = RAGRetrievalEngine()
results = rag.query(
    query_text="What is a variable?",
    subject="computer_science"
)

print(f"Answer: {results['answer']}")
print(f"Sources: {len(results['sources'])}")
```

---

## Best Practices

1. **Organize by grade** - Keep grade-specific notes in respective folders
2. **Clear filenames** - Use descriptive names that indicate subject
3. **Consistent format** - Prefer PDF for compatibility
4. **Regular updates** - Re-ingest when notes are updated
5. **Verify ingestion** - Check ChromaDB collections after processing

---

## Troubleshooting

### Issue: "No files found"

**Solution:**
- Verify files are in `notes/grade_10/`
- Check file extensions (.pdf, .txt, .md)
- Ensure files are readable

### Issue: "OCR failed"

**Solution:**
- Install Tesseract: `pip install pytesseract pillow`
- For handwritten notes: `pip install easyocr`
- Use `--ocr-mode force` to retry

### Issue: "Collection not found"

**Solution:**
- Verify ingestion completed successfully
- Check ChromaDB path: `satya_data/chroma_db`
- List collections to confirm creation

---

## Additional Resources

- **Ingestion script:** `scripts/ingest_content.py`
- **RAG documentation:** `scripts/rag_data_preparation/README.md`
- **Quick start guide:** `scripts/rag_data_preparation/QUICK_START.md`
