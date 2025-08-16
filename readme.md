# Satyá: Learning Companion 
<div align="center">
   <img height="180" width="180" src="https://github.com/user-attachments/assets/4faf37b4-bb01-47c7-b443-d58b6c3eff62">
   
   [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
   [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
   [![Offline First](https://img.shields.io/badge/Offline-First-green)](https://github.com/aa-sikkkk/Satya)
   [![RAG Powered](https://img.shields.io/badge/RAG-Powered-purple)](https://github.com/aa-sikkkk/Satya)

</div>


An **offline-first, RAG-powered** learning companion for students. Built with intelligent content discovery and a lightweight Phi 1.5 AI model, designed to work with **low-end hardware**.

## 📋 Table of Contents
- [Features](#-features)
- [Technical Architecture](#-technical-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [GUI Usage](#gui-usage)
- [AI Models](#-ai-models)
- [RAG System](#rag-system)
- [Content Management](#content-management)
- [OpenAI Proxy Integration (Online Q&A)](#openai-proxy-integration-online-qa)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)
- [FAQ](#faq)

## ✨ Features

### For Students
- 📚 **RAG-Enhanced Content Discovery**: Intelligent search through study materials
- 🤖 **Single AI Model**: Phi 1.5 handles Q&A, hints, and content generation
- 🎯 **Answer Length Control**: Choose from 5 different detail levels (very short to very long)
- 📊 Progress tracking and analytics
- 🔄 **100% Offline**: No internet required for core functionality
- 🎯 Adaptive learning paths
- 🌐 **Search with OpenAI (Online):** Ask any question and get an answer from OpenAI (if enabled by your school/teacher)
- 🖥️ **Modern, responsive GUI:** Beautiful customtkinter interface and improved answer display (scrollable, word-wrapped, responsive to long answers)

https://github.com/user-attachments/assets/7d6d42e0-c1ee-4f3b-9bbc-692cbabe46ec

### For Teachers
- 📝 Content management and editing
- 📊 Student progress analytics
- 🔍 Content validation and quality control
- 📈 Performance monitoring

## 🏗️ Technical Architecture

### Core Components
1. **RAG (Retrieval-Augmented Generation) Engine**
   - **ChromaDB**: Local vector database for intelligent content search
   - **Phi 1.5 Embeddings**: Lightweight text embeddings for content discovery
   - **Smart Content Retrieval**: Finds most relevant study materials for any question
   - **Offline Vector Search**: No internet required for content discovery

2. **AI Engine**
   - **Single Phi 1.5 Model**: Handles all AI tasks (Q&A, hints, content generation)
   - **Lightweight GGUF Format**: Optimized for low-end hardware (2GB RAM minimum)
   - **Answer Length Control**: 5 different detail levels for varied learning needs
   - **Offline Model Inference**: No internet required for AI responses

3. **CustomTkinter GUI**
   - Modern, aesthetic, and responsive interface
   - Sidebar navigation, NEBedu logo, loading spinner, and scrollable answer display
   - Threaded model inference for UI responsiveness

4. **Data Management**
   - JSON-based content structure
   - Schema validation
   - Version control for content
   - Data integrity checks

5. **Security Layer**
   - Input sanitization
   - File operation safety
   - Access control
   - Audit logging
   - **OpenAI API key never stored on client**

---

## 📁 Project Structure

```
Satya/
├── satya_data/                 # Data and models directory
│   ├── models/
│   │   └── phi_1_5/           # Phi 1.5 GGUF model
│   ├── chroma_db/              # RAG vector database
│   └── content/                # Educational content
│
├── scripts/
│   ├── rag_data_preparation/   # RAG content processing
│   │   ├── embedding_generator.py  # Generate embeddings for RAG
│   │   └── pdf_processor.py    # Process PDFs to chunks
│   └── data_collection/        # Content collection tools
│
├── system/
│   ├── rag/                    # RAG system components
│   │   └── rag_retrieval_engine.py  # Intelligent content retrieval
│   ├── data_manager/           # Data handling
│   ├── performance/            # Performance monitoring
│   └── security/               # Security features
│
├── ai_model/
│   ├── model_utils/            # Model helper functions
│   │   ├── phi15_handler.py    # Phi 1.5 model handler
│   │   └── model_handler.py    # Main model manager
│
├── student_app/
│   ├── gui_app/                # Modern GUI (customtkinter)
│   ├── interface/              # CLI interface components
│   ├── learning/               # Learning features
│   └── progress/               # Progress tracking
│
├── teacher_tools/               # Teacher utilities
├── tests/                      # Test suite
└── docs/                       # Documentation
```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- **llama-cpp-python** for Phi 1.5 model support

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/aa-sikkkk/satya.git
   cd Satya
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   .\venv\Scripts\activate   # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download Phi 1.5 Model**
   - Place the Phi 1.5 GGUF model in `satya_data/models/phi_1_5/`
   - Recommended: `phi-1_5-Q5_K_S.gguf` (lightweight, ~1GB)

---

## 💻 Usage

### Student Mode (CLI)
```bash
python -m student_app.interface.cli_interface
```

**New Features:**
- **Answer Length Selection**: Choose from 5 detail levels
- **RAG-Enhanced Q&A**: Intelligent content discovery
- **Smart Fallbacks**: Always get meaningful answers

### Teacher Mode
```bash
python -m teacher_tools.content_editor.content_editor_cli
```

---

## 🖥️ GUI Usage

### Student Mode (GUI)
```bash
python -m student_app.gui_app.main_window
```
- Enjoy a modern, responsive interface with sidebar navigation, Satyá logo, loading spinner, and scrollable answer display.
- All features of the CLI are available in the GUI, including **RAG-enhanced Q&A**, progress tracking, and adaptive learning.

  ![Screenshot (116)](https://github.com/user-attachments/assets/6faf37b4-bb01-47c7-b443-d58b6c3eff62)
![Screenshot (118)](https://github.com/user-attachments/assets/9cb70ec8-a636-4f93-8d69-7a12c5eb61bf)

---

## 🤖 AI Models

### Phi 1.5 Model
- **Single Model Architecture**: One model for all tasks (Q&A, hints, content generation)
- **Lightweight**: GGUF format optimized for low-end hardware
- **Offline**: 100% local, no internet required
- **Smart**: Handles text normalization, case sensitivity, and answer validation

### Answer Length Control
1. **Very Short** (10-20 words): Quick facts and definitions
2. **Short** (30-50 words): Basic explanations with key points
3. **Medium** (80-120 words): Detailed explanations with examples - **Recommended**
4. **Long** (150-250 words): Comprehensive coverage with step-by-step breakdown
5. **Very Long** (300-500 words): Extensive coverage with multiple perspectives

---

## 🔍 RAG System

### What is RAG?
**Retrieval-Augmented Generation** combines intelligent content search with AI-powered answer generation.

### How It Works
1. **Content Processing**: PDFs and documents are chunked and embedded
2. **Vector Storage**: ChromaDB stores text and image embeddings
3. **Smart Retrieval**: Finds most relevant content for any question
4. **AI Enhancement**: Phi 1.5 generates answers using retrieved context
5. **Fallback System**: Multiple fallback levels ensure students always get help

### Benefits
- **Intelligent Search**: Finds relevant content even with vague questions
- **Context-Aware**: AI understands the context before answering
- **Offline**: No internet required for content discovery
- **Scalable**: Easy to add new subjects and content

---

## 📚 Content Management

### Content Structure
```json
{
  "type": "object",
  "required": ["subject", "grade", "topics"],
  "properties": {
    "subject": {
      "type": "string",
      "enum": ["Computer Science", "Science", "English"]
    },
    "grade": {
      "type": "integer",
      "minimum": 1,
      "maximum": 12
    },
    "topics": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "subtopics"],
        "properties": {
          "name": {"type": "string"},
          "subtopics": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["name", "concepts"],
              "properties": {
                "name": {"type": "string"},
                "concepts": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "required": ["name", "summary", "steps", "questions"],
                    "properties": {
                      "name": {"type": "string"},
                      "summary": {"type": "string"},
                      "steps": {
                        "type": "array",
                        "items": {"type": "string"}
                      },
                      "questions": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "required": ["question", "acceptable_answers", "hints"],
                          "properties": {
                            "question": {"type": "string"},
                            "acceptable_answers": {
                              "type": "array",
                              "items": {"type": "string"}
                            },
                            "hints": {
                              "type": "array",
                              "items": {"type": "string"}
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### Content Validation
- Schema validation
- Content quality checks
- Duplicate detection
- Reference validation

---

## 🛰️ OpenAI Proxy Integration (Online Q&A)

Satyá supports secure, online Q&A using [OpenAI](https://github.com/aa-sikkkk/satya/wiki/OpenAI-Integration) models via a proxy server. This allows students to ask any question and get an answer from OpenAI, **without ever exposing the OpenAI API key to the user**.

### How It Works (for Students and Teachers)
- When you use the "Search with OpenAI (Online)" feature in Satyá, your question is securely sent to a server.
- The server gets the answer from OpenAI and sends it back.
- **You do not need to set up or configure anything extra.**
- All server setup and security is handled by the responsible Stakeholders.

### What You Need to Do
- Just use Satyá as normal.
- If online Q&A is enabled, you'll see the "Search with OpenAI (Online)" option in your menu.
- If it's not enabled, you can still use all offline features.

### Security & Privacy
- Your questions are sent securely to the server.
- The OpenAI API key is never stored on your computer or shared with you.
- Only the server communicates with OpenAI.

### Troubleshooting
- If you see a message like "[OpenAI Proxy Mock] ...", it means the online Q&A feature is not currently available. You can still use all offline features.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/new_feature`)
3. Commit your changes (`git commit -m 'Add some new_feature'`)
4. Push to the branch (`git push origin feature/new_feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆕 What's New in This Version

### 🚀 **Major Architecture Changes**
- **Single AI Model**: Replaced multiple models with one efficient Phi 1.5
- **RAG System**: Added intelligent content discovery and retrieval
- **Lightweight**: Optimized for low-end hardware (2GB RAM minimum)

### 🎯 **New Features**
- **Answer Length Control**: 5 different detail levels for varied learning needs
- **Smart Text Normalization**: Handles uppercase, lowercase, and mixed case input
- **RAG-Enhanced Q&A**: Intelligent content discovery for better answers
- **Robust Fallbacks**: Multiple fallback levels ensure students always get help

### 🔧 **Technical Improvements**
- **Offline-First**: 100% local operation, no internet required
- **Performance**: Faster inference with optimized Phi 1.5 parameters
- **Reliability**: Better error handling and confidence scoring
- **Scalability**: Easy to add new subjects and content

---

Made with ❤️ for students
