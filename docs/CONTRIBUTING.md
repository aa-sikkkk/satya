# Contributing to Satya

Thank you for your interest in contributing to the Nepali Grade 10 AI Learning Companion (Satya)! Your contributions help us empower students in Nepal with accessible, offline AI-powered learning resources. This document outlines how you can get involved.

## Project Vision and Goals

Satya aims to provide an offline-first, AI-powered learning companion for Grade 10 students in Nepal, focusing on Computer Science, Science, and English. Our goals include maximizing accessibility on low-resource hardware, delivering high-quality educational content, empowering teachers, and fostering community collaboration. (See [PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) for more details).

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project, you agree to abide by its terms. We strive to create a welcoming and inclusive environment for all contributors.

## How to Contribute

There are many ways to contribute, from reporting bugs and suggesting features to writing documentation and contributing code or educational content.

1.  **Fork the repository.**
2.  **Clone your forked repository** to your local machine.
3.  **Create a new branch** for your contribution (`git checkout -b feature/your-feature-name` or `fix/your-bug-fix`).
4.  **Make your changes.**
5.  **Commit your changes** with clear and meaningful commit messages.
6.  **Push your changes** to your fork (`git push origin your-branch-name`).
7.  **Open a Pull Request** against the main repository's `main` branch.

### Reporting Bugs

If you find a bug, please report it by opening a new issue on the project's issue tracker. Provide a clear description of the bug, steps to reproduce it, expected behavior, and your environment (OS, Python version, etc.).

### Suggesting Features

Have an idea for a new feature? Open an issue on the issue tracker to suggest it. Describe the feature, its purpose, and how it would benefit the project and users.

### Contributing Code

We welcome code contributions! Before submitting code, please ensure it adheres to the project's standards.

*   **Setup**: Follow the installation steps outlined in the README or [TECHNICAL_IMPLEMENTATION.md](docs/TECHNICAL_IMPLEMENTATION.md) to set up your development environment and install dependencies (`pip install -r requirements.txt`).
*   **Code Style**: Adhere strictly to [PEP 8 standards](docs/PROJECT_STANDARDS.md#11-python-code-style). Use Black for formatting, type hints, and Google-style docstrings. We recommend using linters like Flake8 and Isort (included in `requirements.txt`). You can automate checks using `validate_standards.py`.
*   **Testing**: Write unit and integration tests for your code following the guidelines in [PROJECT_STANDARDS.md](docs/PROJECT_STANDARDS.md#6-testing-standards) and [TECHNICAL_IMPLEMENTATION.md](docs/TECHNICAL_IMPLEMENTATION.md#7-testing-strategy). Aim for high test coverage. Run tests using `pytest`.
*   **Directory Structure**: Place your code in the appropriate directories as described in [TECHNICAL_IMPLEMENTATION.md](docs/TECHNICAL_IMPLEMENTATION.md#f-directory-structure).
*   **Commit Messages**: Write clear, concise commit messages that explain the purpose of the change.
*   **Pull Requests**: Ensure your pull request has a descriptive title and explains the changes made.

### Contributing Content

The educational content is community-editable and a core part of Satya. We encourage subject matter experts and educators to contribute and improve the content.

*   **Content Structure**: All content must follow the JSON schema defined in [PROJECT_STANDARDS.md](docs/PROJECT_STANDARDS.md#41-json-schema-standards) and detailed in [content-explanation.md](docs/content-explanation.md#2-field-descriptions).
*   **Content Quality**: Adhere to the [Content Quality Standards](docs/content-explanation.md#2-content-quality-standards) regarding language, accuracy, cultural sensitivity, and progression.
*   **Using the Content Editor**: We highly recommend using the CLI Content Editor (`teacher_tools/content_editor/main.py`) to make content changes. It assists with navigation, editing, and automatically validates against the schema before saving. (See [TEACHER_GUIDE.md](docs/TEACHER_GUIDE.md#3-content-management-with-the-cli-editor)).
*   **Validation**: After editing, validate your content using the `validate_standards.py` script (`python scripts/validation/validate_standards.py`). Only validated content should be committed.
*   **Workflow**: Make changes to the JSON files located in `data/content/`. Use the Content Editor for a guided experience. Commit your changes and submit a pull request.

### Contributing Documentation

Clear and comprehensive documentation is vital for the project's success.

*   **Types of Documentation**: Contribute to docstrings, inline comments, README files, and the various guides in the `docs/` directory (e.g., [STUDENT_GUIDE.md](docs/STUDENT_GUIDE.md), [TEACHER_GUIDE.md](docs/TEACHER_GUIDE.md), [TECHNICAL_IMPLEMENTATION.md](docs/TECHNICAL_IMPLEMENTATION.md)). Refer to [PROJECT_STANDARDS.md](docs/PROJECT_STANDARDS.md#7-documentation-standards) for guidelines.
*   **How to Contribute**: Edit the relevant Markdown or code files, commit your changes, and open a pull request.

## Getting Help

If you have questions or need help contributing, feel free to open an issue on the issue tracker or reach out to the project maintainers.

We look forward to your contributions! 
