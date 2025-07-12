# NEBedu - AI Learning Companion 🤖📚
<div align="center">
   <img height="180" width="180" src="https://github.com/user-attachments/assets/daa5d212-12b8-49e7-8d72-f8a57a7b0b46">
</div>

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Offline First](https://img.shields.io/badge/Offline-First-green)](https://github.com/aa-sikkkk/NEBedu)

An offline-first, community-editable AI learning companion for students, focusing on Computer Science, Science, and English subjects. Built with lightweight AI models and structured educational content, designed to work in low-resource environments.

## 📋 Table of Contents
- [Features](#-features)
- [Technical Architecture](#-technical-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [GUI Usage](#gui-usage)
- [AI Models](#-ai-models)
- [Content Management](#-content-management)
- [OpenAI Proxy Integration (Online Q&A)](#openai-proxy-integration-online-qa)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)
- [FAQ](#faq)

## ✨ Features

### For Students
- 📚 Comprehensive coverage of Grade 10 curriculum
- 🤖 AI-powered Q&A and hint generation
- 📊 Progress tracking and analytics
- 🔄 Offline-first functionality
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
1. **AI Engine**
   - DistilBERT for Q&A (optimized for 4GB RAM)
   - T5-small for hint generation
   - **Phi 2 for advanced reasoning and adaptive learning**
   - Offline model inference
   - Caching system for performance
   - **OpenAI Proxy Integration for online Q&A**
2. **CustomTkinter GUI**
   - Modern, aesthetic, and responsive interface
   - Sidebar navigation, NEBedu logo, loading spinner, and scrollable answer display
   - Threaded model inference for UI responsiveness
3. **Data Management**
   - JSON-based content structure
   - Schema validation
   - Version control for content
   - Data integrity checks
4. **Security Layer**
   - Input sanitization
   - File operation safety
   - Access control
   - Audit logging
   - **OpenAI API key never stored on client**

---

## 📁 Project Structure

```
NEBedu/
├── OpenAi_Proxy/openai_proxy # FastAPI-based OpenAI proxy server (for secure online Q&A) 
├── scripts/
│   └── data_collection/
│       └── data/
│           ├── raw_content/    # Raw, unprocessed data
│           ├── processed/      # Cleaned/intermediate data
│           └── content/        # Final, validated content JSONs
│
├── ai_model/
│   ├── training/               # Colab notebooks and training scripts
│   ├── exported_model/         # Trained models for offline use
│   └── model_utils/            # Model helper functions
│
├── student_app/
│   ├── gui_app/                # Modern GUI (customtkinter)
│   ├── interface/              # CLI interface components
│   ├── learning/               # Learning features
│   └── progress/               # Progress tracking
│
├── teacher_tools/
│   ├── content_editor/         # Content editing tools
│   └── analytics/              # Progress analytics
│
├── system/
│   ├── data_manager/           # Data handling
│   ├── performance/            # Performance monitoring
│   └── security/               # Security features
│
├── tests/                      # Test suite
├── docs/                       # Documentation

```

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- 4GB RAM minimum
- 500MB free disk space
- Offline environment support

### Step-by-Step Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/aa-sikkkk/NEBedu.git
   cd NEBedu
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

---

## 💻 Usage

### Student Mode (CLI)
```bash
python -m student_app.interface.cli_interface
```

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
- Enjoy a modern, responsive interface with sidebar navigation, NEBedu logo, loading spinner, and scrollable answer display.
- All features of the CLI are available in the GUI, including AI-powered Q&A, progress tracking, and adaptive learning.

  ![Screenshot (116)](https://github.com/user-attachments/assets/6c1e438e-2bf8-438b-a6bf-e81f55502dbc)
![Screenshot (118)](https://github.com/user-attachments/assets/9cb70ec8-a636-4f93-8d69-7a12c5eb61bf)


---


### Training Process
1. Data collection and preprocessing
2. Model fine-tuning on Google Colab
3. Model optimization and quantization
4. Export for offline use

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

NEBedu supports secure, online Q&A using [OpenAI](https://github.com/aa-sikkkk/NEBedu/wiki/OpenAI-Integration) models via a proxy server. This allows students to ask any question and get an answer from OpenAI, **without ever exposing the OpenAI API key to the user**.

### How It Works (for Students and Teachers)
- When you use the "Search with OpenAI (Online)" feature in NEBedu, your question is securely sent to a server.
- The server gets the answer from OpenAI and sends it back.
- **You do not need to set up or configure anything extra.**
- All server setup and security is handled by the responsible Stakeholders.

### What You Need to Do
- Just use NEBedu as normal.
- If online Q&A is enabled, you'll see the "Search with OpenAI (Online)" option in your menu.
- If it's not enabled, you can still use all offline features.

### Security & Privacy
- Your questions are sent securely to the server.
- The OpenAI API key is never stored on your computer or shared with you.
- Only the server communicates with OpenAI.

### Troubleshooting
- If you see a message like "[OpenAI Proxy Mock] ...", it means the online Q&A feature is not currently available. You can still use all offline features.

---

## 🛠️ Development

### Setting Up Development Environment
1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests
```bash
pytest tests/
```

### Code Style
- Follow PEP 8
- Use type hints
- Document all functions
- Write unit tests

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made with ❤️ for students
