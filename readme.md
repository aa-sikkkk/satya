# NEBedu - AI Learning Companion 🤖📚

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
└── tools/                      # Utility scripts
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

4. **Run Setup Script**
   ```bash
   python tools/setup.py
   ```

## 💻 Usage

### Student Mode
```bash
python student_app/main.py
```

### Teacher Mode
```bash
python teacher_tools/content_editor/main.py
```

## 🧠 AI Models

### Model Specifications
- **DistilBERT (Q&A)**
  - Size: ~260MB
  - RAM Usage: ~1GB
  - Inference Time: <100ms
  - Accuracy: 85% on test set

- **T5-small (Hints)**
  - Size: ~150MB
  - RAM Usage: ~500MB
  - Inference Time: <200ms

### Training Process
1. Data collection and preprocessing
2. Model fine-tuning on Google Colab
3. Model optimization and quantization
4. Export for offline use

## 📚 Content Management

### Content Structure
```json
{
  "subject": "Computer Science",
  "topics": [
    {
      "name": "Programming",
      "subtopics": [
        {
          "name": "Python Basics",
          "concepts": [
            {
              "name": "Variables",
              "questions": [
                {
                  "text": "What is a variable?",
                  "answer": "A variable is a container for storing data values.",
                  "hints": ["Think about storage", "Like a box"]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
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
- All contributors and teachers who have helped shape this project

## 📞 Support

For support, please:
1. Check the [documentation](docs/)
2. Open an issue
3. Contact the maintainers

---

Made with ❤️ for Nepali students
