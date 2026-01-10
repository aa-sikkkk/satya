# Notes vs Textbooks: Content Strategy

## Overview

The Satya RAG system supports two types of educational content:
1. **Textbooks** - Comprehensive curriculum materials
2. **Notes** - Teacher-created summaries and supplementary materials

Both are processed separately and stored in dedicated ChromaDB collections for flexible retrieval.

---

## Content Comparison

| Aspect | Textbooks | Notes |
|--------|-----------|-------|
| **Source** | Official curriculum PDFs | Teacher-created materials |
| **Location** | `textbooks/grade_10/` | `notes/grade_10/` |
| **Collection** | `neb_{subject}_grade_10` | `neb_{subject}_notes_grade_10` |
| **Content Type** | Comprehensive, structured | Summaries, quick references |
| **Processing** | Standard extraction | Same as textbooks |
| **Metadata** | `type: "neb_curriculum"` | `type: "neb_curriculum"` |
| **Search** | Always included | Always included |

---

## Why Keep Both

### Textbooks Provide

1. **Comprehensive coverage** - Complete curriculum content
2. **Structured learning** - Organized by topics and chapters
3. **Authoritative source** - Official reference material
4. **Detailed explanations** - In-depth concept coverage

### Notes Provide

1. **Concise summaries** - Quick concept reviews
2. **Key highlights** - Important points emphasized
3. **Alternative explanations** - Different teaching perspectives
4. **Mnemonics and tips** - Memory aids and shortcuts

### Combined Benefits

- **Comprehensive answers** from textbooks
- **Quick references** from notes
- **Multiple perspectives** on same concepts
- **Flexible search** across both sources

---

## Collection Structure

### Current Setup

**Textbooks only:**
```
neb_computer_science_grade_10
neb_english_grade_10
neb_science_grade_10
```

**With notes added:**
```
neb_computer_science_grade_10        (textbooks)
neb_computer_science_notes_grade_10  (notes)
neb_english_grade_10                 (textbooks)
neb_english_notes_grade_10           (notes)
neb_science_grade_10                 (textbooks)
neb_science_notes_grade_10           (notes)
```

---

## Processing Strategy

### Recommended Approach

**Keep both textbooks and notes** for maximum educational value.

**Process together:**
```bash
python scripts/ingest_content.py
```

**Process separately:**
```bash
# Textbooks only
python scripts/ingest_content.py --input textbooks

# Notes only
python scripts/ingest_content.py --input notes
```

---

## Search Behavior

### Automatic Inclusion

The RAG system automatically searches both textbooks and notes:

```python
from system.rag.rag_retrieval_engine import RAGRetrievalEngine

rag = RAGRetrievalEngine()
result = rag.query(
    query_text="What is a variable?",
    subject="computer_science"
)

# Results include chunks from:
# - neb_computer_science_grade_10 (textbooks)
# - neb_computer_science_notes_grade_10 (notes)
```

### Filtering by Source

While not typically needed, you can filter by source type:

```python
# Get all results
results = rag.query(query_text="...", subject="...")

# Filter to textbooks only
textbook_sources = [
    s for s in results['sources']
    if 'notes' not in s['metadata'].get('collection', '')
]

# Filter to notes only
notes_sources = [
    s for s in results['sources']
    if 'notes' in s['metadata'].get('collection', '')
]
```

---

## When to Rebuild

### Keep Existing Collections If

- Content is current and accurate
- Collections are functioning properly
- You want to add supplementary notes
- No major curriculum changes

### Rebuild Collections If

- Curriculum has been updated
- Existing content contains errors
- Switching to different textbooks
- Major structural changes needed

### Rebuild Process

```python
import chromadb

client = chromadb.PersistentClient(path='satya_data/chroma_db')

# Delete old collections
client.delete_collection('neb_computer_science_grade_10')
client.delete_collection('neb_computer_science_notes_grade_10')

# Re-run ingestion
# python scripts/ingest_content.py
```

---

## Best Practices

### Content Organization

1. **Separate directories** - Keep textbooks and notes in respective folders
2. **Clear naming** - Use descriptive filenames
3. **Grade structure** - Maintain grade-specific organization
4. **Consistent format** - Prefer PDF for compatibility

### Processing Workflow

1. **Process textbooks first** - Establish baseline content
2. **Add notes incrementally** - Supplement with teacher materials
3. **Verify collections** - Check counts and sample content
4. **Test retrieval** - Ensure both sources are searchable

### Maintenance

1. **Regular updates** - Re-ingest when content changes
2. **Version control** - Track content versions
3. **Backup database** - Periodically backup ChromaDB
4. **Monitor quality** - Review retrieval results

---

## Example Workflow

### Initial Setup

```bash
# 1. Add textbooks
# Place PDFs in textbooks/grade_10/

# 2. Process textbooks
python scripts/ingest_content.py --input textbooks

# 3. Verify
python -c "
import chromadb
client = chromadb.PersistentClient(path='satya_data/chroma_db')
print([c.name for c in client.list_collections()])
"
```

### Adding Notes

```bash
# 1. Add notes
# Place PDFs in notes/grade_10/

# 2. Process notes
python scripts/ingest_content.py --input notes

# 3. Verify both exist
python -c "
import chromadb
client = chromadb.PersistentClient(path='satya_data/chroma_db')
for c in client.list_collections():
    print(f'{c.name}: {c.count()} chunks')
"
```

### Testing Combined Search

```python
from system.rag.rag_retrieval_engine import RAGRetrievalEngine

rag = RAGRetrievalEngine()
result = rag.query(
    query_text="Explain variables in programming",
    subject="computer_science"
)

print(f"Answer: {result['answer']}")
print(f"\nSources ({len(result['sources'])}):")
for source in result['sources']:
    collection = source['metadata'].get('collection', 'unknown')
    print(f"  - {collection}")
```

---

## Metadata Schema

### Textbook Chunks

```python
{
    "source": "computer_science.pdf",
    "type": "neb_curriculum",
    "grade": "10",
    "subject": "computer_science",
    "collection": "neb_computer_science_grade_10"
}
```

### Notes Chunks

```python
{
    "source": "cs_notes.pdf",
    "type": "neb_curriculum",
    "grade": "10",
    "subject": "computer_science",
    "collection": "neb_computer_science_notes_grade_10"
}
```

---

## Summary

**Recommendation:** Keep both textbooks and notes for comprehensive educational coverage.

**Benefits:**
- Authoritative textbook content
- Supplementary teacher notes
- Multiple explanation styles
- Flexible search capabilities

**Implementation:** Use `scripts/ingest_content.py` to process both content types into separate collections.

---

## Additional Resources

- **Quick start:** `QUICK_START.md`
- **Detailed guide:** `README.md`
- **Textbooks README:** `../../textbooks/README.md`
- **Notes README:** `../../notes/README.md`
