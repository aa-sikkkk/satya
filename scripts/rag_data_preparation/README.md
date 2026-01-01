# RAG Data Preparation Pipeline

This pipeline prepares educational content for the Satya RAG (Retrieval-Augmented Generation) system. It processes Grade 10 textbooks, extracts text and images, creates overlapping chunks, and prepares data for Chroma database integration.

## 🎯 Overview

The pipeline handles:
- **PDF Processing**: Text extraction with OCR fallback
- **Content Chunking**: Overlapping chunks optimized for Phi 1.5
- **Image Processing**: Extraction and preparation for embedding
- **Metadata Generation**: Rich metadata for RAG retrieval
- **ChromaDB Integration**: Complete database setup and population
- **Quality Validation**: Ensures content quality and consistency

## 📁 Directory Structure

```
scripts/rag_data_preparation/
├── __init__.py                 # Package initialization
├── pdf_processor.py           # PDF processing + pipeline orchestration
├── embedding_generator.py     # AI models + ChromaDB integration
├── process_all.py             # Unified script to process textbooks + notes
├── QUICK_START.md             # Quick start guide
├── NOTES_GUIDE.md             # Notes vs Books strategy guide
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-nep tesseract-ocr-hin

# For Windows: Download Tesseract from https://github.com/UB-Mannheim/tesseract/wiki
# For macOS: brew install tesseract tesseract-lang
```

### 2. Prepare Your PDFs

Place your Grade 10 textbooks in a directory with the following naming convention:

```
textbooks/
├── computer_science_grade_10.pdf
├── english_grade_10.pdf
└── science_grade_10.pdf
```

### 3. Run the Pipeline

#### ⚡ Recommended: Use process_all.py (One Command)
```bash
# Process everything (textbooks + notes)
python scripts/rag_data_preparation/process_all.py

# Only textbooks
python scripts/rag_data_preparation/process_all.py --textbooks-only

# Only notes
python scripts/rag_data_preparation/process_all.py --notes-only
```

This single command will:
- ✅ Process all PDFs from `textbooks/grade_10/` and `notes/grade_10/`
- ✅ Create optimized chunks (400 words each)
- ✅ Extract images
- ✅ Generate embeddings
- ✅ Add everything to ChromaDB

#### 🔧 Advanced: Using Python API Directly

> **Note**: Use `process_all.py` for most cases. The Python API is for custom processing needs.

```bash
# Process PDFs to chunks
python -c "
from scripts.rag_data_preparation.pdf_processor import PDFProcessor
processor = PDFProcessor('processed_data_new')
results = processor.run_pipeline()
print('Pipeline completed!')
"

# Setup ChromaDB and populate
python -c "
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator
generator = EmbeddingGenerator()
generator.setup_database()
generator.populate_chromadb_with_content()
print('ChromaDB populated!')
"
```

## 🔧 Core Components

### PDFProcessor Class
- **`run_pipeline()`**: Complete pipeline orchestration
- **`process_pdf_to_chunks()`**: PDF to chunks conversion
- **`_extract_page_text()`**: Text extraction with OCR fallback
- **`_extract_page_images()`**: Image extraction and processing

### EmbeddingGenerator Class
- **`setup_database()`**: ChromaDB collection setup
- **`populate_chromadb_with_content()`**: Content population
- **`process_text_chunks()`**: Text chunk processing
- **`process_images()`**: Image processing
- **`generate_clip_text_embedding()`**: CLIP text embeddings

## 📊 Output Structure

After processing, you'll have:

```
processed_data_new/
├── chunks/                     # Processed text chunks
│   ├── computer_science_grade_10_chunks.json
│   ├── english_grade_10_chunks.json
│   └── science_grade_10_chunks.json
├── images/                     # Extracted images
│   ├── computer_science/
│   ├── english/
│   └── science/
├── reports/                    # Processing reports
│   └── pipeline_report.json
└── logs/                       # Processing logs

satya_data/
└── chroma_db/                 # Chroma vector database
    ├── computer_science_grade_10/
    ├── english_grade_10/
    ├── science_grade_10/
    └── config.json
```

## ⚡ Performance Features

- **Direct Processing**: No intermediate files, PDF to chunks in one pass
- **Batch Processing**: Efficient 8-chunk batches for ChromaDB
- **OCR Fallback**: Automatic OCR when text extraction fails
- **Image Optimization**: Base64 encoding for ChromaDB storage
- **Offline Models**: Lightweight GGUF models for local processing

## 🔍 Usage Examples

### Process New PDFs
```python
from scripts.rag_data_preparation.pdf_processor import PDFProcessor

# Initialize processor
processor = PDFProcessor('processed_data_new', language='en')

# Run complete pipeline
results = processor.run_pipeline(['computer_science', 'english'])
print(f"Created {results['total_chunks']} chunks")
```

### Setup and Populate ChromaDB
```python
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator

# Initialize generator
generator = EmbeddingGenerator()

# Setup database
generator.setup_database()

# Populate with content
generator.populate_chromadb_with_content()

# Get statistics
stats = generator.get_collection_info()
print(f"Collections: {stats}")
```

## 🎓 Supported Subjects

- **Computer Science**: Programming concepts, algorithms, databases
- **English**: Literature, grammar, writing skills
- **Science**: Biology, physics, chemistry, environmental science

## 🌟 Key Benefits

- **Consolidated Codebase**: Single file per major functionality
- **No Redundancy**: Eliminated duplicate code and overlapping features
- **Easy Maintenance**: Clear separation of concerns
- **Production Ready**: Robust error handling and logging
- **Offline First**: Works completely without internet
- **Scalable**: Easy to add new subjects or content types 