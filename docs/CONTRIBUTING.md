# Contributing to Satya: Join the Movement

> [!IMPORTANT]
> **This isn't just about technology. It's about educational justice.**

Thank you for your interest in contributing to **Satya** — an intelligent learning companion built to democratize AI-powered education. By contributing to this project, you're joining a movement to ensure that **every student**, regardless of their location, internet connectivity, or hardware resources, has access to intelligent, personalized learning assistance.

---

## Our Mission: Educational Justice Through Technology

### The Problem We're Solving

**2.9 billion people** worldwide lack reliable internet access. In Nepal alone, **60% of students** study in rural areas with limited connectivity and outdated hardware. While AI transforms learning in well-connected urban centers, millions of students remain excluded from this revolution.

**We believe education is a fundamental right, not a privilege.**

### Our Solution: Radical Accessibility

Satya breaks down barriers through:

- **Offline-First Architecture** - Complete functionality without internet
- **Low-Resource Optimization** - Runs on 4GB RAM with decade-old hardware
- **Intelligent RAG System** - Local AI tutoring without cloud dependencies
- **Community-Driven Content** - Teachers and educators control the curriculum
- **Zero Cost** - No subscriptions, no hidden fees, no barriers

**Your contribution helps bridge the digital divide in education.**

---

## Who Can Contribute?

**Everyone!** This project needs diverse skills and perspectives:

### Educators & Teachers
- Contribute curriculum materials and study notes
- Improve educational content quality
- Provide pedagogical feedback
- Test the system with real students

### Developers & Engineers
- Optimize performance for low-resource hardware
- Improve RAG retrieval accuracy
- Enhance user interfaces
- Fix bugs and add features

### Content Creators & Writers
- Create educational materials
- Write documentation and guides
- Translate content to local languages
- Improve explanations and examples

### Designers & UX Specialists
- Improve user interface design
- Enhance user experience
- Create visual assets
- Design intuitive workflows

### Testers & Students
- Test features and report bugs
- Provide feedback on usability
- Suggest improvements
- Share your learning experience

### Community Builders
- Spread awareness about the project
- Help onboard new contributors
- Build local communities
- Advocate for educational equity

> [!NOTE]
> **No contribution is too small.** Whether you fix a typo, report a bug, or contribute a major feature, you're making a difference.

---

## Code of Conduct

We are committed to creating a **welcoming, inclusive, and respectful environment** for all contributors. By participating in this project, you agree to:

- Be respectful and considerate in all interactions
- Welcome diverse perspectives and experiences
- Accept constructive feedback gracefully
- Focus on what's best for the community and students
- Show empathy towards other community members

**Zero tolerance for harassment, discrimination, or exclusionary behavior.**

---

## How to Contribute

### Quick Start Workflow

1. **Fork the repository** on GitHub
2. **Clone your fork** to your local machine
3. **Create a feature branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes** following our guidelines
5. **Commit with clear messages**: `git commit -m "Add feature: description"`
6. **Push to your fork**: `git push origin your-feature-name`
7. **Open a Pull Request** against the `main` branch

---

## Contribution Areas

### 1. Reporting Bugs

Found a bug? Help us fix it!

**What to include:**
- Clear description of the bug
- Steps to reproduce the issue
- Expected vs. actual behavior
- Your environment (OS, Python version, hardware specs)
- Screenshots or error messages if applicable

**Where to report:** Open an issue on our [issue tracker](https://github.com/aa-sikkkk/satya/issues)

### 2. Suggesting Features

Have an idea to improve Satya?

**What to include:**
- Clear description of the feature
- Problem it solves or benefit it provides
- How it aligns with our mission of accessibility
- Potential implementation approach (optional)

**Remember:** We prioritize features that enhance accessibility and work on low-resource hardware.

### 3. Contributing Code

#### Development Setup

**Prerequisites:**
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 5GB free disk space

**Setup Steps:**

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/satya.git
cd Satya

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download Phi 1.5 model (see README.md)
```

#### Code Standards

> [!IMPORTANT]
> All code must adhere to our quality standards to ensure maintainability and accessibility.

**Python Code Style:**
- Follow [PEP 8 standards](docs/PROJECT_STANDARDS.md#11-python-code-style) strictly
- Use **Black** for code formatting
- Include **type hints** for all functions
- Write **Google-style docstrings**
- Use linters: Flake8, Isort (included in `requirements.txt`)

**Testing Requirements:**
- Write unit tests for all new features
- Follow guidelines in [PROJECT_STANDARDS.md](docs/PROJECT_STANDARDS.md#6-testing-standards)
- Aim for high test coverage
- Run tests with `pytest` before submitting

**Directory Structure:**
- Place code in appropriate directories (see [TECHNICAL_IMPLEMENTATION.md](docs/TECHNICAL_IMPLEMENTATION.md#f-directory-structure))
- Keep related functionality together
- Follow existing patterns

**Commit Messages:**
- Use clear, descriptive commit messages
- Format: `<type>: <description>` (e.g., `feat: Add offline mode`, `fix: Resolve memory leak`)
- Reference issues when applicable

**Pull Requests:**
- Provide descriptive title and detailed description
- Explain what changed and why
- Link related issues
- Ensure all tests pass
- Request review from maintainers

### 4. Contributing Educational Content

**Content is the heart of Satya.** We need educators and subject matter experts to contribute high-quality educational materials.

#### Why Content Matters

Your content contributions directly impact students' learning experience. Quality educational materials make the difference between a tool and a true learning companion.

#### Content Guidelines

**Content Structure:**
- Follow the JSON schema in [PROJECT_STANDARDS.md](docs/PROJECT_STANDARDS.md#41-json-schema-standards)
- See detailed field descriptions in [content-explanation.md](docs/content-explanation.md#2-field-descriptions)

**Content Quality Standards:**
- **Language**: Clear, age-appropriate, culturally sensitive
- **Accuracy**: Factually correct and up-to-date
- **Progression**: Appropriate difficulty for grade level
- **Inclusivity**: Accessible to diverse learners

**Using the Content Editor:**

We **highly recommend** using the CLI Content Editor for content changes:

```bash
python teacher_tools/content_editor/main.py
```

The editor provides:
- Guided navigation through content
- Schema validation before saving
- Helpful prompts and suggestions
- Error prevention

See [TEACHER_GUIDE.md](docs/TEACHER_GUIDE.md#3-content-management-with-the-cli-editor) for detailed instructions.

#### Content Workflow

1. **Locate content files** in `data/content/`
2. **Edit using Content Editor** (recommended) or manually
3. **Validate your changes**: `python scripts/validation/validate_standards.py`
4. **Commit validated content** only
5. **Submit pull request** with description of changes

#### Adding New Materials

**Textbooks and Notes:**

Satya supports universal content ingestion for PDFs, scanned documents, and handwritten notes.

**Organization:**

```
textbooks/grade_10/
├── computer_science.pdf
├── english.pdf
└── science.pdf

notes/grade_10/
├── cs_notes.pdf
├── english_summary.md
└── science_revision.txt
```

**Ingestion:**

```bash
# Process all content
python scripts/ingest_content.py

# Process only textbooks
python scripts/ingest_content.py --input textbooks

# Process only notes
python scripts/ingest_content.py --input notes
```

See detailed guides:
- [RAG Data Preparation README](../scripts/rag_data_preparation/README.md)
- [Quick Start Guide](../scripts/rag_data_preparation/QUICK_START.md)
- [Notes Strategy Guide](../scripts/rag_data_preparation/NOTES_GUIDE.md)

### 5. Contributing Documentation

**Clear documentation is essential** for making Satya accessible to all users.

#### Documentation Types

- **Code Documentation**: Docstrings, inline comments
- **User Guides**: Student and teacher guides
- **Technical Documentation**: Implementation details, API references
- **README Files**: Project overview, setup instructions

#### Documentation Standards

Follow guidelines in [PROJECT_STANDARDS.md](docs/PROJECT_STANDARDS.md#7-documentation-standards):

- Use clear, simple language
- Include examples and use cases
- Keep formatting consistent
- Update documentation with code changes

#### How to Contribute Documentation

1. Identify documentation gaps or errors
2. Edit relevant Markdown or code files
3. Ensure clarity and accuracy
4. Commit changes with descriptive messages
5. Submit pull request

---

## Recognition & Community

### Contributors Are Valued

Every contributor is recognized in our project:
- Listed in project acknowledgments
- Credited in release notes
- Invited to community discussions
- Part of a global movement for educational equity

### Join Our Community

- **GitHub Discussions**: Share ideas and ask questions
- **Issue Tracker**: Report bugs and suggest features
- **Pull Requests**: Contribute code and content
- **Social Media**: Spread the word about Satya

---

## Getting Help

**Need assistance?** We're here to help!

- **Questions about contributing**: Open a discussion on GitHub
- **Technical issues**: Open an issue with details
- **General inquiries**: Reach out to project maintainers
- **Documentation**: Check our comprehensive guides in `docs/`

**Don't hesitate to ask!** We welcome questions from contributors at all experience levels.

---

## Impact of Your Contribution

### Every Contribution Matters

When you contribute to Satya, you're:

✅ **Empowering students** in rural areas with AI-powered learning  
✅ **Bridging the digital divide** in education  
✅ **Democratizing access** to intelligent tutoring  
✅ **Supporting teachers** with better tools  
✅ **Building sustainable** open-source education technology  
✅ **Creating educational equity** for underserved communities  

### Real-World Impact

- **500,000+ Grade 10 students** in Nepal can benefit
- **Rural schools** across South Asia gain access to AI tutoring
- **Teachers** can provide personalized learning at scale
- **Communities** build sustainable educational infrastructure

---

## Join the Movement

> [!TIP]
> **Ready to make a difference?** Start small, learn as you go, and grow with the community.

**Your first contribution could be:**
- Fixing a typo in documentation
- Reporting a bug you encountered
- Suggesting a feature improvement
- Adding a study note for students
- Translating content to your language
- Sharing Satya with educators you know

**Together, we can ensure that AI-powered education reaches every student, everywhere.**

---

## Thank You

Thank you for considering contributing to Satya. Your time, skills, and passion help us build a more equitable educational future.

**Let's make AI-powered learning accessible to all students, not just the privileged few.**

**Welcome to the movement. Welcome to Satya.** 
