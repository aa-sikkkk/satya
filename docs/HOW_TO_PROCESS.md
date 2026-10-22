# Content Processing Guide

## Quick Start

**Process all content with one command:**

```bash
python scripts/ingest_content.py
```

This processes textbooks and notes from both `textbooks/` and `notes/` directories.

---

## Folder Structure

```
Satya/
├── textbooks/                    # Textbook PDFs
│   ├── grade_10/
│   │   ├── computer_science.pdf
│   │   ├── english.pdf
│   │   └── science.pdf
│   └── README.md
│
├── notes/                        # Teacher notes
│   ├── grade_10/
│   │   ├── cs_notes.pdf
│   │   ├── english_summary.md
│   │   └── science_revision.txt
│   └── README.md
│
└── satya_data/
    └── chroma_db/               # Generated ChromaDB collections
        ├── neb_computer_science_grade_10/
        ├── neb_english_grade_10/
        └── neb_science_grade_10/
```

---

## Textbooks vs Notes

| Aspect | Textbooks | Notes |
|--------|-----------|-------|
| **Location** | `textbooks/grade_10/` | `notes/grade_10/` |
| **Purpose** | Primary reference | Supplementary material |
| **Collection** | `neb_{subject}_grade_10` | `neb_{subject}_notes_grade_10` |
| **Naming** | Flexible | Flexible |
| **Formats** | PDF, TXT, MD | PDF, TXT, MD |

---

## Processing Options

### Process Everything (Recommended)

```bash
python scripts/ingest_content.py
```

### Process Only Textbooks

```bash
python scripts/ingest_content.py --input textbooks
```

### Process Only Notes

```bash
python scripts/ingest_content.py --input notes
```

### OCR Modes

**Auto-detect (recommended):**
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

---

## What Gets Processed

### Supported File Types

- **PDF** - Text-based or scanned (with OCR)
- **TXT** - Plain text files
- **MD** - Markdown files
- **JSONL** - Structured data

### Auto-Detection

The script automatically:
- Detects content type (text PDF, scanned PDF, handwritten)
- Extracts grade from folder structure (`grade_10/`)
- Infers subject from filename
- Applies appropriate processing (PyMuPDF, Tesseract OCR, or EasyOCR)

---

## Naming Conventions

**Flexible naming** - The system auto-detects subject and grade:

**Textbooks:**
- `computer_science.pdf` ✅
- `science_grade_10.pdf` ✅
- `english.pdf` ✅

**Notes:**
- `cs_notes.pdf` ✅
- `english_summary.md` ✅
- `science_revision.txt` ✅

> **Note:** Grade is extracted from folder name (`grade_10/`), not filename.

---

## Verification

Check what was created:

```python
import chromadb

client = chromadb.PersistentClient(path='satya_data/chroma_db')
collections = client.list_collections()

for c in collections:
    print(f"{c.name}: {c.count()} chunks")
```

**Expected output:**
```
neb_computer_science_grade_10: 1234 chunks
neb_computer_science_notes_grade_10: 567 chunks
neb_english_grade_10: 2345 chunks
neb_english_notes_grade_10: 890 chunks
neb_science_grade_10: 3456 chunks
neb_science_notes_grade_10: 1234 chunks
```

---

## Processing Details

### What Happens

1. **Content Detection** - Identifies file type and content
2. **Extraction** - Uses PyMuPDF for text, OCR for scanned/handwritten
3. **Chunking** - Creates 512-token chunks with 10% overlap
4. **Embedding** - Generates embeddings with all-MiniLM-L6-v2
5. **Storage** - Stores in ChromaDB with metadata

### Metadata

Each chunk includes:
```python
{
    "source": "filename.pdf",
    "type": "neb_curriculum",
    "grade": "10",
    "subject": "computer_science"
}
```

---

## Troubleshooting

### "No files found"

**Solutions:**
- Verify files are in `textbooks/grade_10/` or `notes/grade_10/`
- Check file extensions (.pdf, .txt, .md)
- Ensure files are readable

### "OCR failed"

**Solutions:**
- Install OCR dependencies:
  ```bash
  pip install pytesseract pillow easyocr
  ```
- Verify image quality (300 DPI recommended)
- Try `--ocr-mode force`

### "Collection already exists"

**Note:** This is normal - collections are additive.

**To rebuild:**
```python
import chromadb

client = chromadb.PersistentClient(path='satya_data/chroma_db')
client.delete_collection('neb_computer_science_grade_10')

# Then re-run ingestion
```

### "Slow processing"

**Optimization:**
- Use text PDFs instead of scanned
- Process in smaller batches
- Close other applications

---

## Best Practices

1. **Organize by grade** - Keep grade-specific content in respective folders
2. **Clear filenames** - Use descriptive names
3. **Consistent format** - Prefer PDF for compatibility
4. **Regular updates** - Re-ingest when content changes
5. **Verify ingestion** - Check collections after processing
6. **Backup database** - Periodically backup `chroma_db/`

---

## Additional Resources

- **Detailed pipeline docs:** `scripts/rag_data_preparation/README.md`
- **Quick start guide:** `scripts/rag_data_preparation/QUICK_START.md`
- **Notes strategy:** `scripts/rag_data_preparation/NOTES_GUIDE.md`
- **Textbooks README:** `textbooks/README.md`
- **Notes README:** `notes/README.md`

---

## Success Checklist

After running `ingest_content.py`, you should have:

- [ ] ChromaDB collections created
- [ ] Both textbooks and notes searchable
- [ ] Metadata properly tagged
- [ ] Collections verified with count check

**Your RAG system is now ready!**
