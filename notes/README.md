# Notes Directory

This directory contains **study notes and supplementary materials** that will be processed separately from textbooks.

## 📁 Directory Structure

```
notes/
├── grade_10/              # Grade 10 notes
│   ├── computer_science_notes.pdf
│   ├── english_notes.pdf
│   ├── science_notes.pdf
│   └── [any other notes files]
└── README.md             # This file
```

## 📝 Naming Convention

You can name notes files however you like! The processing script will:
- Try to infer subject from filename
- Allow you to specify subject manually
- Process multiple files at once

### Recommended Names:
- `computer_science_notes.pdf`
- `cs_summary.pdf`
- `english_notes.pdf`
- `science_revision.pdf`

## 🚀 How to Process Notes

### Option 1: Process Everything (Textbooks + Notes) - RECOMMENDED
```bash
# Process all textbooks AND notes in one command
python scripts/rag_data_preparation/process_all.py
```

### Option 2: Process Notes Only
```bash
# Process only notes (skip textbooks)
python scripts/rag_data_preparation/process_all.py --notes-only
```

### Option 3: Process All Notes in Directory (Alternative)
```bash
# The unified script automatically processes all PDFs in notes/grade_10/
python scripts/rag_data_preparation/process_all.py --notes-only
```

## 📚 What Happens After Processing?

1. **Chunks Created**: Notes are split into optimized chunks
2. **Separate Collection**: Notes stored in `{subject}_notes_grade_10` collection
3. **Metadata Tagged**: Marked as `source_type: "notes"` (vs `"book"`)
4. **Searchable**: Can be searched together with or separately from books

## 🔍 Notes vs Books

### Books (Textbooks)
- **Location**: `textbooks/grade_10/`
- **Collection**: `{subject}_grade_10`
- **Content**: Comprehensive textbook content
- **Purpose**: Primary reference material

### Notes (This Directory)
- **Location**: `notes/grade_10/`
- **Collection**: `{subject}_notes_grade_10`
- **Content**: Summaries, quick references, study guides
- **Purpose**: Supplementary material

## 💡 Tips

- **Keep Both**: Books and notes complement each other
- **Organize by Subject**: Group related notes together
- **File Formats**: Supports PDF and text files
- **Multiple Files**: Can process multiple notes files per subject

## 🔍 Where Are Processed Notes Stored?

Processed notes chunks are saved to:
```
processed_data_new/
├── chunks/              # JSON files with note chunks
├── images/             # Extracted images from notes
└── reports/            # Processing reports
```

## 📊 ChromaDB Collections

After processing, notes are stored in separate collections:
- `computer_science_notes_grade_10`
- `english_notes_grade_10`
- `science_notes_grade_10`

These are searched **together** with book collections for comprehensive answers!

## 🔄 Updating Notes

To update notes:
1. Replace the notes file in this directory
2. Re-run the processing script
3. The new notes will be added to ChromaDB
4. Old notes remain unless you delete the collection

## 📖 Example Workflow

```bash
# 1. Add your notes PDFs to notes/grade_10/
#    Example: computer_science_notes.pdf

# 2. Process the notes
python scripts/rag_data_preparation/process_all.py --notes-only

# 3. Verify in ChromaDB
python -c "
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator
gen = EmbeddingGenerator()
info = gen.get_collection_info()
print(info.get('computer_science_notes_grade_10', {}))
"
```

