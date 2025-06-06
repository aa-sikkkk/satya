# NEBedu Teacher Guide

This guide provides instructions for teachers on how to use the NEBedu tools for content management and student progress analysis.

## 1. Introduction

The NEBedu system includes tools specifically designed for teachers to manage educational content and monitor student learning.

## 2. Installation

Refer to the main [Installation Guide](README.md#Installation) for detailed steps on setting up the NEBedu system. The teacher tools are included in the standard installation.

## 3. Content Management with the CLI Editor

The Community Editor (CLI JSON editor) allows you to view, edit, and validate the educational content.

To start the Content Editor, open your terminal in the project directory and run:

```bash
python -m teacher_tools.content_editor.content_editor_cli
```

Once started, you will see a menu with options:

- **Load Content File**: Load a specific subject JSON file from the `data/content/` directory.
- **List Topics**: View the main topics in the loaded content.
- **Add Topic/Concept/Question**: Add new elements to the content hierarchy.
- **Remove Topic/Concept/Question**: Remove existing elements from the content.
- **Save Content File**: Save your changes back to the JSON file. The editor will validate the content against the schema before saving.
- **Exit**: Close the editor.

Ensure you understand the [Content Structure and Management Guide](docs/content-explanation.md) and adhere to the defined [Project Standards](docs/PROJECT_STANDARDS.md) when editing content.

## 4. Student Progress Analytics

The analytics tools allow you to generate reports on student performance.

To use the analytics CLI, open your terminal in the project directory and run:

```bash
python -m teacher_tools.analytics.analytics_cli
```

This will launch an interactive command-line interface where you can select from the following options:

- **Generate Student Report**: Generate a performance report for a specific student. You will be prompted to enter the student's username.
- **Generate Class Report**: Generate an aggregated report for a group of students. You will be prompted to enter the usernames (comma-separated).

Reports can be displayed in the terminal and exported to **CSV** or **JSON** formats.

To access student progress data, you will need to collect the local log files from the student devices. The Logging Manager stores this data locally in the `student_app/progress/` directory (e.g., `progress_[username].json`).

## 5. Content Validation and Quality Control

The Content Editor automatically validates changes against the JSON schema when you save. For a more comprehensive check of content structure and other project standards (like code style and documentation), you can run the `validate_standards.py` script.

To run the standards validator, open your terminal in the project directory and execute:

```bash
python -m scripts.validation.validate_standards
```

This script will report any errors or warnings related to code quality, documentation, naming conventions, and content structure based on the rules defined in `docs/PROJECT_STANDARDS.md`.

Ensure the content also adheres to the [Content Quality Standards](docs/content-explanation.md#content-quality-standards) defined in the documentation.

## 6. Community Contribution

The NEBedu content is community-editable. You can contribute to improving the content by making changes using the Content Editor and submitting them via the version control system (Git).


## 7. Troubleshooting

If you encounter issues, refer to the main [Troubleshooting section](README.md#Support) in the README or the [Technical Implementation Guide](docs/TECHNICAL_IMPLEMENTATION.md#Troubleshooting) for common problems and solutions. 
