# NEBedu - AI Learning Companion 🤖📚
<div align="center">
   <img height="180" width="180" src="https://github.com/user-attachments/assets/daa5d212-12b8-49e7-8d72-f8a57a7b0b46">
</div>

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Offline First](https://img.shields.io/badge/Offline-First-green)](https://github.com/yourusername/NEBedu)





An offline-first, community-editable AI learning companion for Grade 10 students in Nepal, focusing on Computer Science, Science, and English subjects. Built with lightweight AI models and structured educational content, designed to work in low-resource environments.

## 📋 Table of Contents
- [Features](#-features)
- [Technical Architecture](#-technical-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [AI Models](#-ai-models)
- [Content Management](#-content-management)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### For Students
- 📚 Comprehensive coverage of Grade 10 curriculum
- 🤖 AI-powered Q&A and hint generation
- 📊 Progress tracking and analytics
- 🔄 Offline-first functionality
- 🎯 Adaptive learning paths

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

2. **Data Management**
   - JSON-based content structure
   - Schema validation
   - Version control for content
   - Data integrity checks

3. **Security Layer**
   - Input sanitization
   - File operation safety
   - Access control
   - Audit logging

---

## 📁 Project Structure

```
NEBedu/
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


## 💻 Usage

### Student Mode
```bash
python -m student_app.interface.cli_interface
```

### Teacher Mode
```bash
python -m teacher_tools.content_editor.content_editor_cli
```

## 🧠 AI Models

### Model Specifications
- **DistilBERT (Q&A)**
  - Size: ~507MB
  - RAM Usage: ~1.0GB
  - Inference Time: ~5.2 seconds

- **T5-small (Hints)**
  - Size: ~462MB
  - RAM Usage: ~500MB
  - Inference Time: ~5.3 seconds

- **Phi 2 (Advanced Reasoning and Adaptive Learning)**
  - Size: ~1.66GB
  - RAM Usage: ~2.3GB
  - Inference Time: ~16.56–30.51 seconds (depending on complexity)

### Training Process
1. Data collection and preprocessing
2. Model fine-tuning on Google Colab
3. Model optimization and quantization
4. Export for offline use

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

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Hugging Face](https://huggingface.co/) for DistilBERT and T5-small models
- [Google Colab](https://colab.research.google.com/) for training infrastructure
- [Curriculum Development Centre](http://lib.moecdc.gov.np/elibrary/pages/view.php?ref=3726&k=) and [ReadersNepal](Readersnepal.com) for Providing the necessary resources for this project.
- All contributors and teachers who have helped shape this project

## Support

For support, please:
1. Check the [documentation](docs/)
2. Open an issue
3. Contact the maintainers

---

Made with ❤️ for Nepali students
