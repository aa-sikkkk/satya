# 🚀 How to Process Textbooks & Notes

## ⚡ Quick Answer: One Command

```bash
python scripts/rag_data_preparation/process_all.py
```

**That's it!** This processes both textbooks and notes, generates embeddings, and adds everything to ChromaDB.

---

## 📋 Detailed Instructions

### Prerequisites

1. **Add your PDFs:**
   - Textbooks → `textbooks/grade_10/`
   - Notes → `notes/grade_10/` (optional)

2. **Run the processing:**
   ```bash
   python scripts/rag_data_preparation/process_all.py
   ```

### What Happens

1. ✅ Processes all textbooks from `textbooks/grade_10/`
2. ✅ Processes all notes from `notes/grade_10/`
3. ✅ Creates optimized chunks (400 words each)
4. ✅ Extracts images
5. ✅ Generates embeddings
6. ✅ Adds to ChromaDB collections

### Processing Options

```bash
# Process everything (default)
python scripts/rag_data_preparation/process_all.py

# Only textbooks
python scripts/rag_data_preparation/process_all.py --textbooks-only

# Only notes
python scripts/rag_data_preparation/process_all.py --notes-only

# Process but skip embeddings (for testing)
python scripts/rag_data_preparation/process_all.py --skip-embeddings
```

---

## 📊 Verify Results

After processing, check what was created:

```bash
python -c "
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator
gen = EmbeddingGenerator()
info = gen.get_collection_info()
print('\n📊 ChromaDB Collections:')
for name, data in sorted(info.items()):
    count = data.get('count', 0)
    print(f'  {name}: {count} chunks')
"
```

Expected output:
```
📊 ChromaDB Collections:
  computer_science_grade_10: 1234 chunks
  computer_science_notes_grade_10: 567 chunks
  english_grade_10: 2345 chunks
  english_notes_grade_10: 890 chunks
  science_grade_10: 3456 chunks
  science_notes_grade_10: 1234 chunks
```

---

## 🔄 Alternative: Process Separately

If you prefer to process books and notes separately:

### Textbooks Only
```bash
python scripts/rag_data_preparation/process_all.py --textbooks-only
```

### Notes Only
```bash
python scripts/rag_data_preparation/process_all.py --notes-only
```

---

## 🔧 Advanced: Using Python API Directly

> **Note**: The `process_all.py` script is recommended for most users. Use the Python API only if you need custom processing logic.

If you need more control, you can use the Python API directly:

```python
from scripts.rag_data_preparation.pdf_processor import PDFProcessor
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator

# Process textbooks
processor = PDFProcessor('processed_data_new')
processor.run_pipeline()

# Generate embeddings
generator = EmbeddingGenerator()
generator.populate_chromadb_with_content(include_notes=False)
```

---

## 📁 File Structure

```
Satya/
├── textbooks/grade_10/          # Your textbook PDFs here
│   ├── computer_science_grade_10.pdf
│   ├── english_grade_10.pdf
│   └── science_grade_10.pdf
│
├── notes/grade_10/               # Your notes PDFs here (optional)
│   ├── computer_science_notes.pdf
│   ├── english_notes.pdf
│   └── science_notes.pdf
│
└── processed_data_new/          # Generated after processing
    ├── chunks/                   # JSON chunk files
    ├── images/                   # Extracted images
    └── reports/                  # Processing reports
```

---

## 🆘 Troubleshooting

### "No PDF files found"
- ✅ Check files are in correct folders: `textbooks/grade_10/` or `notes/grade_10/`
- ✅ Verify file extensions are `.pdf` (not `.PDF` or `.Pdf`)
- ✅ Check file permissions (readable)

### "Collection already exists"
- ✅ This is normal if re-processing
- ✅ Old chunks will be updated/added to
- ✅ Not an error - your data is safe

### "Failed to process PDF"
- ✅ Check PDF has extractable text (not just images)
- ✅ Scanned PDFs will use OCR automatically
- ✅ Check processing logs in `processed_data_new/logs/`
- ✅ Try a different PDF to test

### "ChromaDB not available"
- ✅ Install: `pip install chromadb`
- ✅ Check ChromaDB path: `satya_data/chroma_db/`

---

## 📚 More Help

- **Quick Start**: `scripts/rag_data_preparation/QUICK_START.md`
- **Input Folders Guide**: `INPUT_FOLDERS_GUIDE.md`
- **Textbooks Guide**: `textbooks/README.md`
- **Notes Guide**: `notes/README.md`
- **Notes vs Books**: `scripts/rag_data_preparation/NOTES_GUIDE.md`

---

## ✅ Success Checklist

After running `process_all.py`, you should have:

- [ ] Processed chunks in `processed_data_new/chunks/`
- [ ] Extracted images in `processed_data_new/images/`
- [ ] ChromaDB collections created (check with `get_collection_info()`)
- [ ] Both books and notes searchable in RAG system

---

**That's it!** Your RAG system is now ready to use. 🎉

