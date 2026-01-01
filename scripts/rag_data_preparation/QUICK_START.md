# 🚀 Quick Start: Process Textbooks & Notes

## One Command to Process Everything

```bash
python scripts/rag_data_preparation/process_all.py
```

This single command will:
1. ✅ Process all textbooks from `textbooks/grade_10/`
2. ✅ Process all notes from `notes/grade_10/`
3. ✅ Generate embeddings for both
4. ✅ Add everything to ChromaDB

## 📋 Step-by-Step Guide

### 1. Prepare Your Files

**Textbooks:**
```
textbooks/grade_10/
├── computer_science_grade_10.pdf
├── english_grade_10.pdf
└── science_grade_10.pdf
```

**Notes:**
```
notes/grade_10/
├── computer_science_notes.pdf  (optional)
├── english_notes.pdf          (optional)
└── science_notes.pdf          (optional)
```

### 2. Run Processing

```bash
# Process everything
python scripts/rag_data_preparation/process_all.py
```

### 3. Verify Results

```bash
python -c "
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator
gen = EmbeddingGenerator()
info = gen.get_collection_info()
for name, data in info.items():
    print(f'{name}: {data.get(\"count\", 0)} chunks')
"
```

## 🎯 Processing Options

### Process Only Textbooks
```bash
python scripts/rag_data_preparation/process_all.py --textbooks-only
```

### Process Only Notes
```bash
python scripts/rag_data_preparation/process_all.py --notes-only
```

### Process Without Embeddings (Testing)
```bash
python scripts/rag_data_preparation/process_all.py --skip-embeddings
```

## 📊 What Gets Created

### Processed Chunks
```
processed_data_new/
├── chunks/              # JSON files with chunks
│   ├── computer_science_grade_10_chunks.json
│   ├── computer_science_notes_grade_10_chunks.json
│   └── ...
├── images/             # Extracted images
└── reports/            # Processing reports
```

### ChromaDB Collections
```
Books:
├── computer_science_grade_10
├── english_grade_10
└── science_grade_10

Notes:
├── computer_science_notes_grade_10
├── english_notes_grade_10
└── science_notes_grade_10
```

## ⚡ Alternative: Process Separately

If you prefer to process books and notes separately:

### Textbooks Only
```bash
# Process PDFs to chunks
python -c "
from scripts.rag_data_preparation.pdf_processor import PDFProcessor
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator

processor = PDFProcessor('processed_data_new')
processor.run_pipeline()

generator = EmbeddingGenerator()
generator.populate_chromadb_with_content(include_notes=False)
"
```

### Notes Only
```bash
python scripts/rag_data_preparation/process_all.py --notes-only
```

## 🔍 Troubleshooting

### "No PDF files found"
- Check files are in `textbooks/grade_10/` or `notes/grade_10/`
- Verify file extensions are `.pdf`
- Check file permissions

### "Collection already exists"
- This is normal if re-processing
- Old chunks will be updated/added to
- Use `get_collection_info()` to check counts

### "Failed to process"
- Check PDF has extractable text
- Try OCR for scanned PDFs (automatic)
- Check processing logs in `processed_data_new/logs/`

## 📚 More Information

- **Full Guide**: See `INPUT_FOLDERS_GUIDE.md` in project root
- **Textbooks Guide**: See `textbooks/README.md`
- **Notes Guide**: See `notes/README.md`
- **Notes vs Books**: See `NOTES_GUIDE.md`

