# Technical Implementation Guide

## System Architecture Overview

This document provides a detailed technical overview of the NEBedu project's system architecture, elucidating the structure, function, and interaction of its core components. The architecture is designed to support an offline-first, AI-enhanced learning experience with efficient data processing and community-driven content management, optimized for low-resource computing environments.

```mermaid
graph TD
    A[Web Crawler Module] --> B(Content Processing and Cleaning Pipeline)
    B --> C(Structured JSON Dataset Generator)
    C --> D[Dataset JSON (Cleaned and Structured)]
    D --> E[NLP Training Module (Google Colab + Huggingface)]
    E --> F[Export Model (PyTorch/ONX) For Offline Use]
    F --> G[CLI Learning Application (Offline Use)]
    G --> H[Students Interacts with questions, hints, answers, etc]
    H --> I[Local Logging of Response, time, hints used]
    I --> J[Logging Manager (Local Storage)]
    J --> G
    C --> K[JSON Content Repository]
    K --> L[Community Editor (CLI JSON editor, Validation, Version Control)]
    L --> K
    F --> G
    K --> G
```

![architecture](https://github.com/user-attachments/assets/37d57fde-2f5e-4800-9769-31b61e684e1a)

*Figure 1: NEBedu System Architecture Diagram*

### 1. Data Acquisition and Processing Pipeline

This pipeline is the initial stage of the NEBedu system, responsible for the systematic collection, refinement, and structuring of educational content from diverse sources into a format compatible with the project's requirements.

#### 1.1 Web Crawler Module

*   **Purpose:** To programmatically navigate and extract raw educational content from designated public online resources (URLs) relevant to the Nepali Grade 10 curriculum. This includes lecture notes, articles, exercises, and other educational materials that can serve as the foundation for the structured content database.
*   **Inputs:** A predefined list of URLs targeting educational websites or online resources.
*   **Outputs:** Raw, unstructured or semi-structured text data and associated metadata extracted from the source URLs.
*   **Key Processes:**
    *   URL management and scheduling.
    *   Fetching web page content (handling dynamic content via headless browser if necessary, as implied by Selenium usage in `FILE_REQUIREMENTS.md`).
    *   Initial parsing of HTML/XML structure.
    *   Extraction of main content blocks, potentially including text, tables, and other relevant elements.
    *   Storage of raw extracted data for subsequent processing stages.
*   **Technology/Implementation Notes:** Likely implemented using libraries such as `requests` or `Selenium` for fetching and `BeautifulSoup` for parsing, located within the `scripts/data_collection/` directory.

#### 1.2 Content Processing and Cleaning Pipeline

*   **Purpose:** To transform the heterogeneous raw data into a clean, standardized, and more structured intermediate format by eliminating noise and applying initial organizational rules.
*   **Inputs:** Raw content data received from the Web Crawler Module.
*   **Outputs:** Cleaned and partially structured content data, free from irrelevant elements and inconsistencies.
*   **Key Processes:**
    *   Noise reduction (removing advertisements, navigation links, headers, footers, etc.).
    *   Text normalization (handling character encoding issues, standardizing formatting, correcting common errors).
    *   Application of extraction rules to identify potential questions, answers, hints, and explanations within the text based on patterns or heuristics derived from the source material.
    *   Structuring the cleaned content into a more consistent intermediate representation.
*   **Technology/Implementation Notes:** This would involve custom Python scripts and potentially text processing libraries, residing within the `scripts/data_collection/` directory.

#### 1.3 Structured JSON Dataset Generator

*   **Purpose:** To convert the cleaned and processed content into the definitive, hierarchical JSON format specified by the project, making it ready for both model training and direct use by the application.
*   **Inputs:** Cleaned and partially structured data from the Content Processing and Cleaning Pipeline.
*   **Outputs:** `Dataset JSON (Cleaned and Structured)` files adhering to the project's JSON schema, containing educational content organized by subject, topic, subtopic, concept, questions, acceptable answers, and hints. These files also populate the `JSON Content Repository`.
*   **Key Processes:**
    *   Parsing the intermediate structured data.
    *   Mapping identified content elements (questions, hints, etc.) to the fields defined in the target JSON schema.
    *   Organizing content into the subject-topic-subtopic-concept hierarchy.
    *   Assigning unique identifiers (`id`) to concepts and questions as per the defined standard.
    *   Validating the generated JSON against the project's schema to ensure structural integrity and data correctness.
*   **Technology/Implementation Notes:** Custom Python scripts responsible for data transformation and validation, likely using Python's built-in `json` library and potentially a JSON schema validation library. Located in the `scripts/data_collection/` directory.

#### 1.4 Dataset JSON (Cleaned and Structured)

*   **Purpose:** Serves as the standardized data format that is the direct output of the generation process and the primary input for training the AI models.
*   **Content:** Contains educational content structured hierarchically in JSON format, validated against the project schema.
*   **Role:** Acts as a bridge between the data processing pipeline and the AI model training phase.

#### 1.5 JSON Content Repository

*   **Purpose:** The central, version-controlled repository for all validated and finalized educational content in the project's structured JSON format.
*   **Content:** Stores the `Dataset JSON` files that have been generated and potentially further refined by the Community Editor.
*   **Role:** Provides the definitive source of educational content for the CLI Learning Application and serves as the base for community contributions and updates.
*   **Management:** Implemented using a Git repository, allowing for tracking changes, collaboration, and maintaining content history.

### 2. AI Model Development and Integration

This segment covers the training, optimization, and integration of the natural language processing models that provide the AI capabilities within the learning companion.

#### 2.1 NLP Training Module (Google Colab + Huggingface)

*   **Purpose:** To fine-tune pre-trained, lightweight Hugging Face transformer models on the project's structured educational dataset to specialize them for the tasks of subject-specific Question Answering (Q&A) and hint generation relevant to the Nepali Grade 10 curriculum.
*   **Inputs:** `Dataset JSON (Cleaned and Structured)` files.
*   **Outputs:** Fine-tuned AI models (DistilBERT, T5-small, or similar lightweight architectures) ready for export.
*   **Key Processes:**
    *   Loading the structured dataset and preparing it into the format required by the Hugging Face `transformers` library (e.g., tokenization, creating datasets and dataloaders).
    *   Loading pre-trained models (e.g., `distilbert-base-uncased`, `t5-small`).
    *   Defining training objectives and loss functions for Q&A and hint generation tasks.
    *   Executing the fine-tuning process, typically using optimizers and learning rate schedulers.
    *   Evaluating model performance on validation data.
*   **Technology/Implementation Notes:** Scripts (`ai_model/training/train_model_colab.py`) designed to run efficiently on Google Colab, leveraging its GPU/TPU resources. Uses `transformers` and potentially `PyTorch` or `TensorFlow`.

#### 2.2 Export Model (PyTorch/ONX) For Offline Use

*   **Purpose:** To convert the fine-tuned models into a highly optimized format that minimizes size and maximizes inference speed, making them suitable for deployment and execution on low-resource student devices without internet connectivity.
*   **Inputs:** Fine-tuned AI models from the NLP Training Module (typically in PyTorch or TensorFlow format).
*   **Outputs:** Optimized model files, likely in ONNX format, along with associated configuration and vocabulary files.
*   **Key Processes:**
    *   Loading the trained model.
    *   Converting the model graph to the target format (e.g., PyTorch to ONNX).
    *   Applying optimization techniques such as model quantization (converting weights to lower precision like INT8) and graph optimizations.
    *   Saving the optimized model and tokenizer files.
*   **Technology/Implementation Notes:** Utilizes tools and libraries provided by PyTorch, TensorFlow, and ONNX Runtime for model conversion and optimization. Files are stored in `ai_model/exported_model/`.

### 3. Offline Learning Application and Logging

This represents the student-facing part of the system and the mechanism for recording student interactions and progress.

#### 3.1 CLI Learning Application (Offline Use)

*   **Purpose:** The primary interface through which students interact with the NEBedu system. It delivers educational content and provides AI-powered assistance in an offline environment.
*   **Inputs:** Structured content from the `JSON Content Repository` and the `Exported Model`.
*   **Outputs:** Student learning interactions and requests.
*   **Key Processes:**
    *   Loading and presenting educational content (topics, concepts, questions) to the student via the command line.
    *   Receiving and processing student inputs (answers, hint requests, navigation commands).
    *   Invoking the loaded AI models to generate responses or hints based on student input and context.
    *   Providing feedback and explanations to the student.
    *   Interfacing with the Logging Manager to record interaction data.
*   **Technology/Implementation Notes:** A Python CLI application (`student_app/` directory) likely using libraries like `rich` and `prompt_toolkit` for enhanced command-line user experience. Must efficiently load content and models into memory.

#### 3.2 Students Interacts with questions, hints, answers, etc

*   **Purpose:** Represents the actual engagement of students with the educational content and AI features provided by the CLI application.
*   **Interaction Points:** Answering questions, requesting hints, reviewing explanations, navigating content hierarchy, potentially tracking personal progress indicators displayed by the application.
*   **Data Generated:** Student responses, time taken per question, hints requested, navigation paths.

#### 3.3 Local Logging of Response, time, hints used

*   **Purpose:** To capture granular details of each student interaction locally on their device.
*   **Content:** Records timestamps, the specific question or prompt, the student's input, the AI response (if applicable), which hints were accessed, and potentially other relevant metrics like attempt count.
*   **Storage:** Data is stored in a persistent format (e.g., flat files, local database) within the student's device storage.

#### 3.4 Logging Manager (Local Storage)

*   **Purpose:** To manage the storage, retrieval, and initial processing of the locally logged student interaction data.
*   **Inputs:** Interaction data streams from the CLI Learning Application.
*   **Outputs:** Stored log files/database; potentially aggregated or summarized data for display within the CLI app.
*   **Key Processes:**
    *   Writing interaction data to local storage efficiently.
    *   Ensuring data integrity and handling potential storage issues.
    *   Providing an interface for the CLI app to query and display student progress based on the logged data.
    *   Potentially preparing data for export or synchronization (though synchronization is not explicitly shown in this diagram).
*   **Technology/Implementation Notes:** A dedicated module (`system/logging/` or within `system/data_manager/`) managing file I/O or a local database (e.g., SQLite).

### 4. Community Content Management

This loop describes the process by which the educational content is maintained, validated, and improved collaboratively.

#### 4.1 Community Editor (CLI JSON editor, Validation, Version Control)

*   **Purpose:** A tool designed primarily for teachers and authorized community members to directly edit, enhance, and validate the structured educational content within the `JSON Content Repository`.
*   **Inputs:** Content files from the `JSON Content Repository`.
*   **Outputs:** Updated and validated content files to be committed back to the `JSON Content Repository`.
*   **Key Processes:**
    *   Loading and presenting content in an editable format via a command-line interface.
    *   Allowing users to add, modify, or remove subjects, topics, subtopics, concepts, questions, answers, and hints.
    *   Crucially, performing rigorous JSON schema validation on all changes before they can be saved.
    *   Integrating with Git commands to commit and manage content updates within the repository, facilitating version control and collaboration.
*   **Technology/Implementation Notes:** A dedicated CLI application (`teacher_tools/content_editor/main.py`) using libraries like `rich` and `prompt_toolkit`, incorporating JSON schema validation logic and potentially Python's `subprocess` module or a Git library to interact with the version control system.

This detailed breakdown illustrates the complete operational flow of the NEBedu system, from initial data acquisition and AI model preparation to student interaction, local logging, and the continuous improvement cycle facilitated by the community content editor. The architecture prioritizes offline functionality and resource efficiency to meet the project's goals.

## 📦 Dependencies

### Core Dependencies
```python
transformers==4.30.2
torch==2.0.1
numpy==1.24.3
tqdm==4.65.0
```

### CLI/UI Dependencies
```python
rich==13.3.5
prompt_toolkit==3.0.38
typer==0.9.0
```

### Data Collection Dependencies
```python
selenium==4.10.0
beautifulsoup4==4.12.2
webdriver_manager==3.8.6
```

### Testing Dependencies
```python
pytest==7.3.1
pytest-cov==4.1.0
```

## 📁 Directory Structure
```
NEBedu/
├── scripts/
│   ├── data_collection/
│   │   └── data/
│   │       ├── raw_content/    # Raw, unprocessed data
│   │       ├── processed/      # Cleaned/intermediate data
│   │       └── content/        # Final, validated content JSONs
│   └── validation/
│       └── validate_standards.py # Script to validate code and content standards
│
├── ai_model/
│   ├── training/               # Colab notebooks and training scripts
│   ├── exported_model/         # Trained models for offline use
│   └── model_utils/
│       └── model_handler.py    # Model helper functions
│
├── student_app/
│   ├── interface/
│   │   └── cli_interface.py    # CLI interface components
│   ├── learning/               # Learning features (e.g., question handling)
│   └── progress/               # Progress tracking
│
├── teacher_tools/
│   ├── content_editor/
│   │   └── content_editor_utils.py # Content editing utilities
│   └── analytics/
│       └── analytics_utils.py    # Progress analytics utilities
│
├── system/
│   ├── data_manager/
│   │   └── content_manager.py    # Data handling and validation
│   ├── performance/
│   │   └── performance_utils.py  # Performance monitoring utilities
│   └── security/
│       └── security_utils.py     # Security features
│
├── tests/                      # Test suite
├── docs/
│   ├── TECHNICAL_IMPLEMENTATION.md
│   ├── content-explanation.md
│   ├── FILE_REQUIREMENTS.md
│   ├── PROJECT_OVERVIEW.md
│   ├── PROJECT_STANDARDS.md
│   ├── architecture.drawio.png
│   ├── PROJECT_MEMORY.md
│   ├── ACCOUNT_SWITCH_CHECKLIST.md
│   └── PROJECT_CONTINUATION.md
│
├── data/                       # Root for data content
│   ├── content/
│   └── raw_content/
│
├── tools/                      # Utility scripts (e.g., setup.py, download_model.py)
├── requirements.txt            # Project dependencies
├── requirements-dev.txt        # Development dependencies
├── .gitignore                  # Git ignore file
└── README.md                   # Project README
```

## 🔧 Implementation Details

### 1. AI Model Handler
```python
class ModelHandler:
    def __init__(self):
        self.qna_model = DistilBertForQuestionAnswering.from_pretrained("distilbert-base-uncased")
        self.qna_tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
        self.hint_model = T5ForConditionalGeneration.from_pretrained("t5-small")
        self.hint_tokenizer = T5Tokenizer.from_pretrained("t5-small")
        # Future: Add step recommendation, adaptive learning heads
    def generate_answer(self, question: str, context: str) -> str:
        # QnA implementation
        pass
    def generate_hint(self, question: str, context: str) -> str:
        # Hint generation implementation
        pass
```

```python
from typing import Dict, Any

class JSONSchemaValidator:
    def validate(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        # Schema validation implementation
        pass
```

### 3. Data Collection Process
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from typing import Dict

class ContentCrawler:
    def __init__(self):
        # Selenium setup
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=chrome_options)
    def extract_raw_content(self, soup: BeautifulSoup) -> Dict:
        # Raw content extraction
        pass
    def extract_content(self, soup: BeautifulSoup, subject: str) -> Dict:
        # Content processing
        pass
```

### 4. Model Training Script
- Located at `ai_model/training/train_model_colab.py`
- Trains both DistilBERT (QnA) and T5-small (hint generation) on curriculum-aligned data
- Modular, multi-task structure for future extensibility

## 🔍 Critical Implementation Notes

### 1. Model Training
- Use Google Colab for training
- Export models in Hugging Face format for efficiency
- Modular training for QnA and hint generation
- Cache model responses

### 2. Content Processing
- Preserve raw content before processing
- Handle Nepali characters properly
- Remove ads and navigation
- Validate content structure

### 3. Performance Optimization
- Lazy loading of content
- Content caching
- Memory monitoring
- Raw content compression

### 4. Error Handling
- Graceful degradation
- Content validation
- Error logging
- Recovery mechanisms

## 🧪 Testing Strategy

### 1. Unit Tests
```python
def test_model_handler():
    handler = ModelHandler()
    answer = handler.generate_answer("What is...?", "Context...")
    assert isinstance(answer, str)
    assert len(answer) > 0
    hint = handler.generate_hint("What is...?", "Context...")
    assert isinstance(hint, str)
    assert len(hint) > 0
```

### 2. Integration Tests
- End-to-end content processing
- Model inference pipeline (QnA + hint)
- CLI interaction flow

### 3. Performance Tests
- Memory usage monitoring
- Response time measurement
- Content processing speed

## 🔒 Security Measures

### 1. Content Security
- Input validation
- Content sanitization
- Safe file operations
- Rate limiting

### 2. Data Protection
- Content encryption
- Backup system
- Access control
- Source validation

## 📈 Future Enhancements

### 1. Short-term
- Progress tracking
- Multi-language support
- Enhanced hints
- Image support

### 2. Long-term
- Community features
- Content versioning
- AI-powered generation
- Adaptive learning

## 🚀 Deployment Guide

### 1. Prerequisites
- Python 3.8+
- Chrome browser
- Sufficient disk space
- Memory requirements

### 2. Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
# Install dependencies
pip install -r requirements.txt
# Download models
python scripts/download_model.py
```

### 3. Configuration
```python
# config.py
MODEL_PATH = "models/neb_edu"
CONTENT_DIR = "data/content"
RAW_CONTENT_DIR = "data/raw_content"
```

### 4. Running
```bash
# Start the application
python main.py
# Run tests
pytest tests/
# Collect content
python scripts/data_collection/crawler.py
```

## 🔄 Maintenance

### 1. Regular Tasks
- Content updates
- Model retraining
- Performance monitoring
- Error log review

### 2. Backup Strategy
- Daily content backups
- Model versioning
- Configuration backups
- User data protection

## 📚 Additional Resources

### 1. Documentation
- API documentation
- User guides
- Architecture docs
- Content structure docs

### 2. External Links
- DistilBERT model documentation
- T5 model documentation
- Selenium documentation
- Rich documentation
- Hugging Face guides

## ⚠️ Known Limitations

### 1. Technical
- Memory usage with large content
- Processing speed with complex content
- Model accuracy limitations
- Browser compatibility

### 2. Content
- Language support limitations
- Content format restrictions
- Image handling constraints
- Update frequency

## 🔧 Troubleshooting

### 1. Common Issues
- Memory errors
- Content extraction failures
- Model loading issues
- Browser compatibility

### 2. Solutions
- Memory optimization
- Content validation
- Model fallback
- Browser configuration

## [2024-06-XX] Reverse Engineering Workflow for Data Processing

1. Define or obtain a gold standard output JSON for the target schema.
2. Compare raw input and gold standard output to deduce transformation rules.
3. Update processor.py (or equivalent) to implement these rules.
4. Validate the processor output against the gold standard using scripts or tools.
5. Iterate until the output matches the gold standard exactly.
6. Use validation scripts and regression tests for future updates.

Account switch: technical documentation continuity maintained.

This document serves as a comprehensive reference for the NEBedu project implementation. It should be updated as the project evolves and new features are added.

## System Architecture (Updated)
- **CLI App**: Student-facing, uses Hugging Face models for Q&A, tracks progress, and adapts learning.
- **Performance Module**: Provides @timeit decorator, resource usage logging, and performance metric logging. Used in critical paths (model inference, file I/O).
- **Security Module**: Validates usernames, file paths, and content input. Logs security events and ensures safe file operations.
- **Teacher Tools**:
  - **Analytics**: Generates student/class reports, exports to CSV/JSON.
  - **Content Editor**: Loads, edits, validates, and saves content JSONs. Uses ContentManager schema for validation.

## Data Pipeline
1. **raw_content/**: Raw, unprocessed data (scraped, OCR, etc.).
2. **processed/**: Cleaned, normalized, or partially structured data.
3. **content/**: Final, validated JSON files. Only these are used by the app and teacher tools.

## Content Editor Utilities
- Functions to add/remove topics, concepts, questions.
- Validates content against schema before saving.
- Only operates on files in `content/`.

## Analytics Utilities
- Generates detailed student progress reports.
- Identifies weak concepts and exports analytics.

## Security & Performance Synergy
- Security validation always precedes performance logging.
- All suspicious/failed validations are logged as security events.
- Critical operations are both profiled and secured.

## Folder Structure
- `scripts/data_collection/data/raw_content/`
- `scripts/data_collection/data/processed/`
- `scripts/data_collection/data/content/`
- `teacher_tools/analytics/`
- `teacher_tools/content_editor/`
- `system/performance/`
- `system/security/`

## See also
- [Project Overview](PROJECT_OVERVIEW.md)
- [Project Standards](PROJECT_STANDARDS.md)

## Teacher Content Editor CLI

The Teacher Content Editor CLI is a command-line interface designed for teachers to manage educational content JSON files for NEBedu. It provides a user-friendly menu-driven experience, allowing teachers to perform the following actions:

- **Load Content File**: Load a JSON file containing educational content.
- **List Topics**: Display a list of topics available in the loaded content.
- **Add Topic**: Add a new topic to the content.
- **Add Concept**: Add a new concept to a specified topic and subtopic.
- **Add Question**: Add a new question to a specified concept.
- **Remove Topic**: Remove a topic from the content.
- **Remove Concept**: Remove a concept from a specified topic and subtopic.
- **Remove Question**: Remove a question from a specified concept.
- **Save Content File**: Save the current content to a JSON file.
- **Exit**: Exit the CLI with a goodbye message.

The CLI uses the `rich` library for display and `prompt_toolkit` for input, ensuring a consistent and intuitive user experience. All operations are performed using utility functions from `content_editor_utils.py`, which handle the underlying logic for content management.

This CLI is designed to be robust and user-friendly, allowing teachers to manage content without needing to write code. It includes clear prompts and confirmations, ensuring that users can easily navigate and perform actions without confusion. 
