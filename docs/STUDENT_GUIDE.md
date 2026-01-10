# Satya Student Guide

Welcome to the Satya Learning Companion! This guide will help you get started with the application and make the most of its features.

## 1. What is Satya?

Satya is an offline AI learning companion for Grade 10 students in Nepal. It helps you study Computer Science, Science, and English using interactive content and AI assistance, even without internet access.

## 2. Installation

Your teacher or system administrator will likely install Satya for you. If you need to install it yourself, please refer to the detailed [Installation Guide](https://github.com/aa-sikkkk/satya/blob/master/readme.md#installation).

## 3. Starting the Application

You can start Satya using the provided application file (recommended) or via command line.

### Method 1: Using the Application (Recommended)

1. Locate the **`SatyaGUI.exe`** file (usually provided by your teacher or in the `dist` folder).
2. Double-click the file to launch the application.
3. The graphical interface will open, ready for use.

### Method 2: Running from Source (Advanced)

If you are using the source code directly, open your terminal or command prompt in the `Satya` directory and run:

**For Graphical Interface (GUI):**
```bash
python -m student_app.gui_app.main_window
```

**For Command Line Interface (CLI):**
```bash
python -m student_app.interface.cli_interface
```

https://github.com/user-attachments/assets/7d6d42e0-c1ee-4f3b-9bbc-692cbabe46ec

The application will load and present you with the main menu or the available subjects.

## 4. Navigating Content

The content is organized by Subject, Topic, Subtopic, and Concept.

- Use the on-screen prompts and commands to navigate through the different levels.
- You will be able to select a subject, then a topic, then a subtopic, and finally a concept.
- Each concept will have explanations and associated questions.

## 5. Learning with Questions and AI Assistance

Once you are viewing a concept, you can interact with the questions related to it.

- **Answering Questions**: Type your answer when prompted and press Enter.
- **Getting Hints**: If you are stuck, you can ask for a hint. The AI will provide progressive hints to guide you without giving away the answer immediately.
- **Viewing Explanations**: After attempting a question (or if available), you can view the explanation to understand the concept better.
- **Asking the AI (Q&A)**: You can ask the AI questions about the loaded content. The AI will use its knowledge to provide relevant answers.

Remember, all of this works offline!

## 6. Tracking Your Progress

Satya tracks your learning progress locally on your device using your username.

- The application records your answers, the time taken, and the hints used.
- You can access progress-related features from the main menu of the application:
    - **View Progress**: See a summary of your performance and areas for improvement.
    - **Export Progress**: Save your progress data to a file.
    - **Import Progress**: Load previously saved progress data.
    - **Reset Progress**: Clear your current progress data.

This data helps you and your teacher understand which concepts you have mastered and which areas might need more focus.

## 7. Offline Functionality

One of the key features of Satya is that it works entirely offline. Once installed, you do not need an internet connection to access the content or use the AI assistance.

## 8. Troubleshooting

If you encounter any issues while using the application, inform your teacher or the system administrator. They can refer to the [Technical Implementation Guide](docs/TECHNICAL_IMPLEMENTATION.md#Troubleshooting) or the project documentation for solutions. 
