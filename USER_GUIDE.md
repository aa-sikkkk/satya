# Satya Learning Companion - User Guide

## Introduction
Welcome to Satya, your offline AI learning companion. Satya is designed to assist students in understanding their textbooks and class notes without requiring an internet connection. It acts as a personalized tutor that reads your specific learning materials and answers your questions based strictly on that content.

## How Satya Works
Satya uses a technology called Retrieval-Augmented Generation (RAG). Here is the process:
1.  **Ingestion**: Satya scans your PDF textbooks and notes, breaking them down into small, searchable chunks of text.
2.  **Retrieval**: When you ask a question, Satya searches your personalized library for the most relevant paragraphs.
3.  **Generation**: The AI model reads these paragraphs and formulates a specific answer for you.

This means Satya does not "hallucinate" or make up facts as often as general AI; it tries to stick to what is written in your books.

---

## Optimizing Your Questions
To receive the most accurate and detailed answers, it is important to phrase your questions effectively. Since Satya matches your words against your textbooks, using the right keywords is essential.

### 1. Use Textbook Terminology
The system searches for exact keyword matches. Use the specific scientific or historical terms found in your curriculum.
*   **Effective**: "Define photosynthesis."
*   **Effective**: "What is the function of the mitochondria?"
*   **Effective**: "Explain the Treaty of Sugauli."
*   **Ineffective**: "How do plants make food?" (Unless your book specifically uses the phrase "make food", "photosynthesis" is a safer search term.)

### 2. Focus on "What" and "How"
Satya excels at defining concepts and explaining processes.
*   **Definitions**: "What is an isotope?"
*   **Processes**: "How does the digestive system work?"
*   **Key Figures**: "Who was Isaac Newton?"

### 3. Ask Specific Questions
Broad questions can overwhelm the system because it can only read a limited amount of text at once. Break complex topics into smaller questions.
*   **Too Broad**: "Tell me everything about World War II."
*   **Better**: "What were the causes of World War II?" followed by "What appeared in the Treaty of Versailles?"

---

## Understanding the AI's Limitations
Satya runs entirely on your local computer to ensure privacy and accessibility. This introduces some constraints compared to cloud-based AI like ChatGPT.

### 1. Context Window Limit
The AI reads approximately 300 characters (about 3-4 sentences) of context at a time. This optimization allows it to run smoothly on standard laptops.
*   **Implication**: If a topic is spread across multiple pages in your book, Satya might only see one part of it.
*   **Strategy**: If an answer seems incomplete, ask a follow-up question targeting the missing detail.

### 2. Strict Reliance on Provided Content
Satya relies entirely on the documents you have loaded.
*   If a concept is not in your notes, Satya likely will not know it.
*   If Satya replies "I don't know," it often means it could not find a high-confidence match in your text. This is a safety feature to prevent guessing.

### 3. Linguistic Ambiguity
The AI model (Phi 1.5) is lightweight. Occasionally, it may use pronouns like "it" or "they" ambiguously. Always read the answer in the context of your question.

---

## Study Strategies for Students
Satya is best used as a study aid, not just a homework solver.

### Self-Quizzing
Use Satya to verification your knowledge.
*   **Method**: Ask Satya "What is the definition of Force?"
*   **Action**: Try to recite the definition yourself before reading Satya's answer. Compare your recall with the textbook definition provided by the AI.

### Clarification of Complex Topics
If a paragraph in your textbook is dense or difficult to understand, ask Satya to define the specific terms within it.
*   **Example**: "What does 'permeable membrane' mean?"

### finding Connections
Use Satya to link concepts.
*   **Example**: "What is the relationship between current and voltage?" (This triggers a search for Ohm's Law in your physics text).

---

## Troubleshooting

### Issue: The answer is too short.
*   **Solution**: Try rephrasing with "Explain in detail..." or "Describe the process of..."
*   **Solution**: Ask for the definition specifically, e.g., "Define [Concept]."

### Issue: The answer seems generic.
*   **Solution**: Add more specific keywords from your chapter title or subject.
*   **Solution**: Ensure you have selected the correct Subject in the application menu.

### Issue: "I don't know" or irrelevant answers.
*   **Solution**: Check if the relevant chapter or PDF is actually loaded in the Content Manager.
*   **Solution**: Try using a synonym for the key term (e.g., try "cell division" instead of "mitosis" if the first yields no results).
