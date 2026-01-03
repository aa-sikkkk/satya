# Textbooks Directory

This directory contains **textbook PDFs** that will be processed into comprehensive book chunks for the RAG system.

## 📁 Directory Structure

```
textbooks/
├── grade_10/              # Grade 10 textbooks
│   ├── computer_science_grade_10.pdf
│   ├── english_grade_10.pdf
│   └── science_grade_10.pdf
└── README.md             # This file
```

## 📝 Naming Convention

For automatic processing, name your PDF files using this format:

```
{subject}_grade_{grade}.pdf
```

### Examples:
- `computer_science_grade_10.pdf`
- `english_grade_10.pdf`
- `science_grade_10.pdf`

### Alternative Formats (also supported):
- `computer_science_grade10.pdf`
- `computer_science_10.pdf`
- `computer_science.pdf`

## 🚀 How to Process Textbooks

### Option 1: Process Everything (Textbooks + Notes) - RECOMMENDED
```bash
# Process all textbooks AND notes in one command
python scripts/rag_data_preparation/process_all.py
```

### Option 2: Process Textbooks Only
```bash
# Process only textbooks (skip notes)
python scripts/rag_data_preparation/process_all.py --textbooks-only
```

### Option 3: Process All Textbooks (Python API)
```bash
python -c "
from scripts.rag_data_preparation.pdf_processor import PDFProcessor
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator

processor = PDFProcessor('processed_data_new')
results = processor.run_pipeline()

generator = EmbeddingGenerator()
generator.populate_chromadb_with_content(include_notes=False)
print('✅ Textbooks processed!')
"
```

### Option 4: Process Single Subject
```bash
python -c "
from scripts.rag_data_preparation.pdf_processor import PDFProcessor
processor = PDFProcessor('processed_data_new')
result = processor.process_pdf_to_chunks(
    'textbooks/grade_10/computer_science_grade_10.pdf',
    'computer_science',
    '10'
)
print(f'✅ Processed {result[\"total_chunks\"]} chunks')
"
```

## 📚 What Happens After Processing?

1. **Chunks Created**: Text is split into optimized chunks (400 words each)
2. **Images Extracted**: All images are saved separately
3. **Metadata Generated**: Subject, page numbers, chapters tracked
4. **ChromaDB Ready**: Chunks are ready for embedding generation

## 💡 Tips

- **Quality Matters**: Use high-quality PDFs for better text extraction
- **OCR Support**: Scanned PDFs will use OCR automatically
- **File Size**: Large PDFs may take longer to process
- **Backup**: Keep original PDFs safe

## 🔍 Where Are Processed Chunks Stored?

Processed chunks are saved to:
```
processed_data_new/
├── chunks/              # JSON files with chunks
├── images/             # Extracted images
└── reports/            # Processing reports
```

## 📊 ChromaDB Collections

After processing and embedding generation, chunks are stored in:
- `computer_science_grade_10`
- `english_grade_10`
- `science_grade_10`

These collections contain comprehensive textbook content for RAG retrieval.

