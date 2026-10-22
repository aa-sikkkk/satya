# ChromaDB Metadata Schema Analysis

## Backup Collections (HuggingFace datasets)

### Current Metadata Structure:
```python
# fineweb_edu
{
    'score': '3.375',
    'id': '<urn:uuid:...>',
    'file_path': 's3://...',
    'language_score': '0.92',
    'url': 'http://...',
    'dump': 'CC-MAIN-2013-20',
    'token_count': '755',
    'source': 'unknown',
    'language': 'en'
}

# khanacademy_pedagogy
{
    'audience': 'general',
    'prompt': '...',
    'seed_data': 'khanacademy',
    'source': 'unknown',
    'text_token_length': '975',
    'format': 'textbook_narrative_tone'
}

# scienceqa
{
    'question': '...',
    'source': 'unknown',
    'category': 'Geography',
    'solution': '...',
    'skill': '...',
    'subject': 'social science',
    'hint': '',
    'task': 'closed choice',
    'lecture': '...',
    'topic': 'geography',
    'answer': '0',
    'grade': 'grade2'  # ← HAS GRADE!
}

# gsm8k
{
    'source': 'unknown',
    'question': '...',
    'answer': '...'
}
```

## Expected Metadata (from ingest_content.py)

```python
# NEB collections
{
    'source': 'filename.pdf',
    'type': 'neb_curriculum',
    'grade': '10',
    'subject': 'biology'
}
```

## Issues:

1. **No consistent grade field** - Only `scienceqa` has it
2. **Different field names** - `subject` vs `topic` vs `category`
3. **No `type` field** - Can't distinguish NEB from HuggingFace
4. **Source is always 'unknown'** - No file tracking

## Solution: Hybrid Metadata Handler

Need to update:
1. `rag_retrieval_engine.py` - Handle both schemas
2. `rag_helper.py` - Flexible metadata parsing
3. `ingest_content.py` - Add `type` field for new content
4. Keep backup as-is (don't modify)
