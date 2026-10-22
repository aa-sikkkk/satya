# Satya RAG System Design & Implementation Plan

## 🎯 Project Overview

**Satya** is an offline-first AI learning companion for Grade 10 students in Nepal. This document outlines the RAG (Retrieval-Augmented Generation) system architecture that will power the intelligent question-answering capabilities.

## 🏗️ Architecture Overview

### Core Design Principles
- **Offline-first**: All functionality works without internet
- **Lightweight**: Optimized for 4GB RAM systems
- **Multimodal**: Handles both text and image content
- **Pre-computed**: Embeddings generated once, used forever
- **Fast retrieval**: Sub-second response times

### System Components
```
Satya RAG System
├── Data Processing Layer
│   ├── PDF Processor (✅ Complete)
│   ├── Text Chunker (✅ Complete)
│   └── Image Processor (🔄 In Progress)
├── Embedding Generation Layer
│   ├── Text Embeddings (Phi 1.5)
│   ├── Image Embeddings (CLIP)
│   └── Base64 Image Processing
├── Vector Database Layer
│   └── Chroma DB (Local Storage)
├── Retrieval Layer
│   ├── Query Processing
│   ├── Vector Similarity Search
│   └── Result Ranking
└── Response Generation Layer
    ├── Answer Synthesis
    ├── Hint Generation
    └── Image References
```

## 📊 Current Status

### ✅ Completed Components
- PDF processing pipeline (`scripts/rag_data_preparation/`)
- Text chunking system
- Base directory structure
- Setup instructions and documentation

### 🔄 In Progress
- Image processing pipeline
- Base64 image handling
- Embedding generation setup

### 📋 Next Steps
- Set up Chroma vector database
- Implement embedding generation pipeline
- Pre-compute all embeddings
- Build retrieval system
- Test end-to-end functionality

## 🗂️ Data Flow Architecture

### 1. Setup Phase (One-time Processing)
```
Input PDFs → Text Chunks + Images → Embeddings → Chroma DB
    ↓              ↓                    ↓          ↓
PDF Processor → Chunking → Phi 1.5/CLIP → Vector Storage
```

### 2. Runtime Phase (Lightweight Operation)
```
Student Question → Query Embedding → Vector Search → Results
       ↓              ↓              ↓          ↓
   Text Input → Phi 1.5 → Chroma DB → Ranked Results
```

## 🎨 Content Types & Processing

### Text Content
- **Source**: PDF text chunks (500-800 words, 50-100 word overlap)
- **Processing**: Phi 1.5 model for embedding generation
- **Storage**: Chroma text collections with metadata
- **Metadata**: subject, grade, chapter, difficulty, language

### Image Content
- **Source**: Textbook illustrations, diagrams, charts
- **Processing**: CLIP model for embedding generation
- **Storage**: Chroma image collections with file references
- **Formats**: PNG/JPG files + Base64 encoded images

### Base64 Images
- **Source**: Embedded images in PDF content
- **Processing**: Decode → CLIP → Store embedding
- **Storage**: Chroma with base64 reference + embedding

## 🗄️ Vector Database Design

### Chroma Collections Structure
```
chroma_db/
├── text_collections/
│   ├── computer_science_grade_10/
│   ├── english_grade_10/
│   └── science_grade_10/
├── image_collections/
│   ├── computer_science_images/
│   ├── english_images/
│   └── science_images/
└── metadata/
    ├── cross_references.json
    ├── content_mapping.json
    └── system_config.json
```

### Metadata Schema
```json
{
  "chunk_id": "unique_identifier",
  "content_type": "text|image|base64",
  "subject": "computer_science|english|science",
  "grade": "10",
  "chapter": "chapter_name",
  "difficulty": "beginner|intermediate|advanced",
  "language": "en",
  "file_path": "path_to_original_content",
  "embedding_vector": "vector_data",
  "related_content": ["related_chunk_ids"],
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

## 🔧 Implementation Plan

### Phase 1: Foundation Setup (Week 1)
- [ ] Install Chroma and dependencies
- [ ] Set up Chroma database structure
- [ ] Create metadata schemas
- [ ] Test basic Chroma operations

### Phase 2: Embedding Pipeline (Week 2)
- [ ] Set up Phi 1.5 for text embeddings
- [ ] Set up CLIP for image embeddings
- [ ] Implement base64 image processing
- [ ] Create embedding generation pipeline

### Phase 3: Content Processing (Week 3)
- [ ] Process existing text chunks
- [ ] Process existing images
- [ ] Process base64 images
- [ ] Generate all embeddings
- [ ] Store in Chroma with metadata

### Phase 4: Retrieval System (Week 4)
- [ ] Implement query processing
- [ ] Build vector similarity search
- [ ] Create result ranking system
- [ ] Test retrieval accuracy

### Phase 5: Integration & Testing (Week 5)
- [ ] Integrate with existing Satya system
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] User interface updates

## 🚀 Technical Specifications

### Model Requirements
- **Phi 1.5**: Text embedding generation
- **CLIP**: Image embedding generation
- **Chroma**: Vector database and similarity search
- **All models**: Offline-capable, cached locally

### Performance Targets
- **Embedding Generation**: <5 seconds per chunk/image
- **Retrieval Response**: <1 second
- **Memory Usage**: <2GB during operation
- **Storage**: <5GB for complete system

### File Structure
```
satya_data/
├── models/
│   ├── phi15/             # Cached Phi 1.5 model
│   └── clip/              # Cached CLIP model
├── chroma_db/             # Vector database
├── processed_content/      # Original chunks and images
├── embeddings/            # Pre-computed embeddings
└── config.json            # System configuration
```

## 🔍 Retrieval Strategy

### Query Processing
1. **Text Input**: Student question in English
2. **Embedding**: Generate question embedding using Phi 1.5
3. **Search**: Query Chroma for similar text chunks
4. **Image Search**: Find related images using text-image similarity
5. **Ranking**: Combine text and image relevance scores

### Result Generation
1. **Top Matches**: Return 3-5 most relevant chunks
2. **Image References**: Include related images
3. **Context**: Provide chapter and subject context
4. **Hints**: Generate contextual learning hints

## 🧪 Testing Strategy

### Unit Testing
- Embedding generation accuracy
- Vector similarity calculations
- Metadata handling
- Chroma operations

### Integration Testing
- End-to-end retrieval pipeline
- Performance benchmarks
- Memory usage monitoring
- Response time validation

### User Testing
- Student question scenarios
- Teacher content validation
- Offline functionality verification
- Multi-subject coverage

## 📈 Success Metrics

### Technical Metrics
- **Retrieval Accuracy**: >85% relevant results
- **Response Time**: <1 second average
- **Memory Usage**: <2GB during operation
- **Storage Efficiency**: <5GB total size

### User Experience Metrics
- **Question Coverage**: >90% of curriculum topics
- **Answer Quality**: >80% user satisfaction
- **Offline Reliability**: 100% offline functionality
- **Learning Effectiveness**: Measured through student progress

## 🔮 Future Enhancements

### Phase 2 Features
- Multi-language support (Nepali, Hindi)
- Advanced hint generation
- Progress tracking integration
- Content recommendation system

### Phase 3 Features
- Mobile application
- Cloud sync capabilities
- Advanced analytics
- Content versioning

## 📚 References

### Architecture Documents
- `architecturenew.md` - New architecture overview
- `PROJECT_INDEX.md` - Project structure and components
- `setup_instructions.md` - PDF processing setup

### Technical Resources
- Chroma Vector Database documentation
- Phi 1.5 model specifications
- CLIP model documentation
- Offline AI deployment best practices

---

**Last Updated**: 2026-10-22
**Status**: Design Phase
**Next Review**: 2026-10-29
**Team**: Satya Development Team 