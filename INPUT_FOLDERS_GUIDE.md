# 📁 Input Folders Guide

This guide explains the organized folder structure for PDFs and notes in the Satya RAG system.

## 📂 Folder Structure

```
Satya/
├── textbooks/                    # 📚 Textbook PDFs (Books)
│   ├── grade_10/                 # Grade 10 textbooks
│   │   ├── computer_science_grade_10.pdf
│   │   ├── english_grade_10.pdf
│   │   └── science_grade_10.pdf
│   └── README.md                 # Textbook processing guide
│
└── notes/                        # 📝 Study Notes & Supplementary Materials
    ├── grade_10/                 # Grade 10 notes
    │   ├── computer_science_notes.pdf
    │   ├── english_notes.pdf
    │   └── science_notes.pdf
    └── README.md                 # Notes processing guide
```

## 📚 Textbooks Folder (`textbooks/`)

### Purpose
Contains **comprehensive textbook PDFs** that serve as the primary reference material.

### Location
```
textbooks/grade_10/
```

### Naming Convention
```
{subject}_grade_{grade}.pdf
```

**Examples:**
- `computer_science_grade_10.pdf` ✅
- `english_grade_10.pdf` ✅
- `science_grade_10.pdf` ✅

### Processing
```bash
# Process all textbooks
python -c "
from scripts.rag_data_preparation.pdf_processor import PDFProcessor
processor = PDFProcessor('processed_data_new')
results = processor.run_pipeline()
"
```

### Result
Creates ChromaDB collections:
- `computer_science_grade_10`
- `english_grade_10`
- `science_grade_10`

## 📝 Notes Folder (`notes/`)

### Purpose
Contains **study notes, summaries, and supplementary materials** that complement textbooks.

### Location
```
notes/grade_10/
```

### Naming Convention
**Flexible!** Any name works. The script will:
- Try to infer subject from filename
- Allow manual subject specification
- Process multiple files at once

**Examples:**
- `computer_science_notes.pdf` ✅
- `cs_summary.pdf` ✅
- `english_revision.pdf` ✅
- `science_quick_ref.pdf` ✅

### Processing
```bash
# Process all notes in directory (recommended)
python scripts/rag_data_preparation/process_all.py --notes-only
```

### Result
Creates separate ChromaDB collections:
- `computer_science_notes_grade_10`
- `english_notes_grade_10`
- `science_notes_grade_10`

## 🔄 Key Differences

| Feature | Textbooks | Notes |
|---------|-----------|-------|
| **Purpose** | Primary reference | Supplementary material |
| **Content** | Comprehensive | Summaries, quick refs |
| **Collection** | `{subject}_grade_10` | `{subject}_notes_grade_10` |
| **Source Type** | `"book"` | `"notes"` |
| **Naming** | Strict convention | Flexible |
| **Processing** | `process_all.py --textbooks-only` | `process_all.py --notes-only` |

## 🚀 Quick Start

### 1. Add Your Textbooks
```bash
# Copy your textbook PDFs to:
textbooks/grade_10/computer_science_grade_10.pdf
textbooks/grade_10/english_grade_10.pdf
textbooks/grade_10/science_grade_10.pdf
```

### 2. Process Textbooks
```bash
python -c "
from scripts.rag_data_preparation.pdf_processor import PDFProcessor
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator

# Process PDFs to chunks
processor = PDFProcessor('processed_data_new')
results = processor.run_pipeline()

# Generate embeddings and add to ChromaDB
generator = EmbeddingGenerator()
for subject in ['computer_science', 'english', 'science']:
    chunks_file = f'processed_data_new/chunks/{subject}_grade_10_chunks.json'
    if os.path.exists(chunks_file):
        generator.process_text_chunks(chunks_file, subject, content_type='book')
"
```

### 3. Add Your Notes
```bash
# Copy your notes PDFs to:
notes/grade_10/computer_science_notes.pdf
notes/grade_10/english_notes.pdf
notes/grade_10/science_notes.pdf
```

### 4. Process Notes
```bash
python scripts/rag_data_preparation/process_all.py --notes-only
```

## 💡 Best Practices

### ✅ Do:
- **Keep both**: Books and notes complement each other
- **Organize by grade**: Use `grade_10/` subfolder
- **Use clear names**: Makes processing easier
- **Backup originals**: Keep your PDFs safe

### ❌ Don't:
- **Mix books and notes**: Keep them in separate folders
- **Use spaces in filenames**: Use underscores instead
- **Delete processed chunks**: They're needed for ChromaDB

## 🔍 Where Are Files Processed?

### Input (Your PDFs)
```
textbooks/grade_10/*.pdf    → Your textbook PDFs
notes/grade_10/*.pdf        → Your notes PDFs
```

### Output (Processed Data)
```
processed_data_new/
├── chunks/                 # JSON chunk files
│   ├── computer_science_grade_10_chunks.json
│   ├── computer_science_notes_grade_10_chunks.json
│   └── ...
├── images/                # Extracted images
│   ├── computer_science/
│   └── ...
└── reports/               # Processing reports
```

### ChromaDB (Vector Database)
```
satya_data/chroma_db/
├── computer_science_grade_10        # Book chunks
├── computer_science_notes_grade_10   # Notes chunks
├── english_grade_10                  # Book chunks
├── english_notes_grade_10            # Notes chunks
└── ...
```

## 📖 Example Workflow

```bash
# 1. Setup folders (already created)
#    textbooks/grade_10/
#    notes/grade_10/

# 2. Add your PDFs
#    Copy textbooks to textbooks/grade_10/
#    Copy notes to notes/grade_10/

# 3. Process textbooks
python -c "
from scripts.rag_data_preparation.pdf_processor import PDFProcessor
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator

processor = PDFProcessor('processed_data_new')
processor.run_pipeline()

generator = EmbeddingGenerator()
generator.populate_chromadb_with_content(include_notes=False)
"

# 4. Process notes
python scripts/rag_data_preparation/process_all.py --notes-only

# 5. Verify
python -c "
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator
gen = EmbeddingGenerator()
info = gen.get_collection_info()
for name, data in info.items():
    print(f'{name}: {data.get(\"count\", 0)} chunks')
"
```

## 🆘 Troubleshooting

### "PDF file not found"
- Check file is in correct folder: `textbooks/grade_10/` or `notes/grade_10/`
- Verify filename matches convention
- Check file extension is `.pdf`

### "Collection already exists"
- This is normal if re-processing
- Old chunks will be updated/added to
- Use `get_collection_info()` to check counts

### "No chunks created"
- Check PDF has extractable text
- Try OCR for scanned PDFs (automatic)
- Check processing logs in `processed_data_new/logs/`

## 📚 More Information

- **Textbooks Guide**: See `textbooks/README.md`
- **Notes Guide**: See `notes/README.md`
- **Processing Guide**: See `scripts/rag_data_preparation/README.md`
- **Notes vs Books**: See `scripts/rag_data_preparation/NOTES_GUIDE.md`

