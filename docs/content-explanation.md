# Satya Content Structure and Management Guide

## Overview

Satya uses a flexible JSON-based content structure to organize educational materials for the students. The content system supports nested hierarchies of topics, subtopics, and concepts with associated questions, making it adaptable to various educational needs.

This guide explains the content structure, schema requirements, and best practices for contributing educational content to Satya.

---

## Content Structure

### 1. Basic Hierarchy

The content follows a hierarchical structure:

```
Subject
  └── Topics
        ├── Concepts (optional, can be at topic level)
        └── Subtopics (optional, can be nested)
              ├── Concepts
              └── Subtopics (recursive nesting supported)
```

### 2. Example Structure

```json
{
  "subject": "Computer Science",
  "grade": 10,
  "topics": [
    {
      "name": "Computer Network",
      "subtopics": [
        {
          "name": "Introduction to Networks",
          "concepts": [
            {
              "name": "What is a Computer Network?",
              "summary": "A computer network is a system of interconnected computers...",
              "steps": [
                "Understand basic networking concepts",
                "Learn about network types"
              ],
              "questions": [
                {
                  "question": "What is a computer network?",
                  "acceptable_answers": [
                    "A system of interconnected computers that can communicate and share resources"
                  ],
                  "hints": [
                    "Think about how computers communicate",
                    "Consider resource sharing"
                  ]
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

---

## Schema Requirements

### Required Fields

#### Subject Level (Root)
- **`subject`** (string): Subject name (e.g., "Computer Science", "Science", "English Grammar")
- **`grade`** (number or string): Grade level (e.g., 10)
- **`topics`** (array): Array of topic objects

#### Topic Level
- **`name`** (string): Topic name

#### Subtopic Level
- **`name`** (string): Subtopic name

#### Concept Level
- **`name`** (string): Concept name

### Optional Fields

#### Topic/Subtopic Level
- **`concepts`** (array): Array of concept objects
- **`subtopics`** (array): Array of nested subtopic objects

#### Concept Level
- **`summary`** (string): Brief description of the concept
- **`steps`** (array of strings): Learning steps or instructions
- **`questions`** (array): Array of question objects or strings

#### Question Object
- **`question`** (string): The question text
- **`acceptable_answers`** (array of strings): Valid answers
- **`hints`** (array of strings): Progressive hints to guide learning

### Flexible Schema

The schema is designed to be maximally flexible:
- Additional properties are allowed at all levels
- Questions can be objects (with structure) or simple strings
- Subtopics can be nested up to 3 levels deep
- Both `concepts` and `subtopics` can coexist at the same level

---

## Content Guidelines

### 1. Naming Conventions

**Subject Names:**
- Use clear, descriptive names
- Examples: "Computer Science", "Science", "English Grammar"

**Topic Names:**
- Broad categories within the subject
- Examples: "Computer Network", "Programming Fundamentals", "Physics"

**Subtopic Names:**
- More specific divisions of topics
- Examples: "Network Security", "QBASIC Programming", "Force"

**Concept Names:**
- Specific learning objectives
- Examples: "Introduction to Computer Networks", "Newton's First Law", "Active and Passive Voice"

### 2. Writing Questions

**Question Format:**
- Clear and concise
- Appropriate for Grade 10 level
- Include mark allocation when relevant (e.g., "[5 marks]")

**Acceptable Answers:**
- Provide multiple valid answer variations
- Include comprehensive explanations
- Use numbered points for multi-part answers

**Hints:**
- Start with general guidance
- Progress to more specific clues
- Avoid giving away the complete answer

**Example:**
```json
{
  "question": "What is a computer network? Explain its importance. [5 marks]",
  "acceptable_answers": [
    "A computer network is a system of interconnected computers and devices that can communicate and share resources. Importance: 1) Resource sharing, 2) Communication, 3) Cost reduction, 4) Centralized data management, 5) Remote access"
  ],
  "hints": [
    "Think about how networks help in sharing resources",
    "Consider both technical and practical benefits"
  ]
}
```

### 3. Writing Summaries

**Concept Summaries:**
- Comprehensive overview of the concept
- Include key points and definitions
- Explain practical applications
- Typically 3-5 sentences minimum

**Example:**
```
"A computer network is a system of interconnected computers and devices that can communicate and share resources. Networks enable data sharing, hardware sharing, and communication between devices. The basic components include nodes, transmission media, and network protocols. Networks can be classified as LAN, WAN, MAN based on geographical coverage. Understanding networks is crucial for modern computing and communication."
```

### 4. Learning Steps

**Purpose:**
- Guide students through the learning process
- Provide a structured approach to mastering concepts

**Format:**
- Action-oriented statements
- Logical progression from basic to advanced
- 3-7 steps per concept

**Example:**
```json
"steps": [
  "Understand basic networking concepts and terminology",
  "Learn about different types of networks and their applications",
  "Study network components and their functions",
  "Explore network protocols and standards",
  "Practice network configuration and troubleshooting"
]
```

---

## Content Quality Standards

### Language and Style

**Clarity:**
- Use simple, clear language
- Avoid unnecessary jargon
- Define technical terms when first used

**Age-Appropriateness:**
- Suitable for Grade 10 students
- Balance between simplicity and technical accuracy

**Cultural Sensitivity:**
- Use examples relevant to Nepali context when appropriate
- Avoid culturally insensitive content

### Accuracy

**Factual Correctness:**
- Ensure all information is accurate
- Verify technical details
- Use reliable sources

**Up-to-Date Information:**
- Keep content current
- Update outdated examples or technologies

### Structure and Organization

**Logical Progression:**
- Organize content from simple to complex
- Build on previously introduced concepts
- Maintain clear hierarchical relationships

**Consistency:**
- Use consistent terminology throughout
- Follow the same format for similar content types
- Maintain uniform question and answer styles

---

## Content Management

### 1. File Organization

**Directory Structure:**
```
scripts/data_collection/data/content/
├── computer_science.json
├── English_Grammar.json
├── science.json
└── [other_subjects].json
```

**File Naming:**
- Use descriptive names
- Lowercase with underscores for multi-word names
- `.json` extension

### 2. Version Control

**Best Practices:**
- Commit content changes with clear messages
- Use meaningful commit descriptions
- Track changes systematically

**Backup:**
- Content Manager automatically creates backups
- Backups stored in `backups/` subdirectory with timestamps
- Format: `content_YYYYMMDD_HHMMSS.json`

### 3. Validation

**Schema Validation:**
The Content Manager validates all content against the schema:
- Required fields must be present
- Data types must match specifications
- Nested structures must follow hierarchy rules

**Validation Process:**
```python
# Content is automatically validated when loaded
content_manager = ContentManager()

# Manual validation for new content
content_manager._validate_content(new_content)
```

**Common Validation Errors:**
- Missing required fields (`subject`, `grade`, `topics`, `name`)
- Incorrect data types (e.g., string instead of array)
- Invalid nested structure

---

## Working with Content

### 1. Adding New Content

**Steps:**
1. Create or open the appropriate subject JSON file
2. Follow the schema structure
3. Add topics, subtopics, and concepts
4. Include questions with answers and hints
5. Validate the content
6. Test with the Content Manager

**Example - Adding a New Concept:**
```json
{
  "name": "New Concept Name",
  "summary": "Comprehensive explanation of the concept...",
  "steps": [
    "Step 1: Introduction",
    "Step 2: Core concepts",
    "Step 3: Practice"
  ],
  "questions": [
    {
      "question": "Sample question?",
      "acceptable_answers": ["Answer 1", "Answer 2"],
      "hints": ["Hint 1", "Hint 2"]
    }
  ]
}
```

### 2. Updating Existing Content

**Programmatic Update:**
```python
from system.data_manager.content_manager import ContentManager

# Load content manager
cm = ContentManager()

# Get existing content
content = cm.get_subject("Computer Science")

# Modify content
# ... make changes ...

# Update with validation and backup
cm.update_content("Computer Science", content)
```

**Manual Update:**
1. Open the JSON file
2. Make necessary changes
3. Ensure JSON syntax is valid
4. Test with Content Manager
5. Commit changes

### 3. Content Suggestions

**Community Contributions:**
```python
# Submit a content suggestion
cm.suggest_content_update(
    subject="Computer Science",
    suggestion={"topic": "...", "changes": "..."},
    username="contributor_name"
)
```

**Suggestions are saved in:**
```
scripts/data_collection/data/content/[subject]/suggestions/
suggestion_[username]_[timestamp].json
```

---

## Content Retrieval

### 1. Accessing Content

**Get All Subjects:**
```python
subjects = cm.get_all_subjects()
# Returns: ['Computer Science', 'Science', 'English Grammar']
```

**Get Topics:**
```python
topics = cm.get_all_topics("Computer Science")
# Returns: ['Computer Network', 'Programming Fundamentals']
```

**Get Concepts:**
```python
concepts = cm.get_all_concepts("Computer Science", "Computer Network")
# Returns: [concept1, concept2, ...]
```

**Get Specific Concept:**
```python
concept = cm.get_concept("Computer Science", "Computer Network", "Introduction to Networks")
```

### 2. Browseable Topics

**For UI Navigation:**
```python
# Get flattened list of browseable topics
entries = cm.list_browseable_topics("Computer Science")
# Returns entries with labels like "Topic > Subtopic > Nested"
```

**Get Concepts at Specific Path:**
```python
# Get concepts at a nested path
concepts = cm.get_concepts_at_path(
    subject="Computer Science",
    topic_name="Computer Network",
    subtopic_path=["Network Security"]
)
```

### 3. Content Search

**Search Across All Content:**
```python
results = cm.search_content(query="network security", max_results=3)
# Returns: [
#   {
#     "subject": "Computer Science",
#     "topic": "Computer Network",
#     "concept": "Network Security",
#     "summary": "..."
#   }
# ]
```

---

## Best Practices

### 1. Content Creation

**Do:**
- Use clear, descriptive names
- Provide comprehensive summaries
- Include multiple acceptable answers
- Add progressive hints
- Use real-world examples
- Test content with students

**Don't:**
- Use ambiguous terminology
- Provide incomplete answers
- Give away answers in hints
- Include culturally insensitive content
- Duplicate content unnecessarily

### 2. Question Design

**Effective Questions:**
- Test understanding, not memorization
- Include mark allocation for exam-style questions
- Provide context when needed
- Use varied question types

**Question Types:**
- Conceptual: "What is...?", "Define..."
- Application: "How would you...?", "Apply..."
- Analysis: "Compare...", "Explain why..."
- Evaluation: "Which is better...?", "Justify..."

### 3. Maintenance

**Regular Reviews:**
- Check for outdated information
- Update examples and references
- Improve clarity based on feedback
- Fix errors and inconsistencies

**Quality Checks:**
- Validate JSON syntax
- Test with Content Manager
- Review for completeness
- Check for typos and grammar

---

## Technical Implementation

### 1. Content Manager

**Location:** `system/data_manager/content_manager.py`

**Key Features:**
- Automatic schema validation
- Flexible content structure support
- Recursive subtopic handling
- Content search with fuzzy matching
- Backup and versioning
- Community suggestions

### 2. Schema Definition

**Concept Schema:**
```python
CONCEPT_SCHEMA = {
    "type": "object",
    "required": ["name"],
    "properties": {
        "name": {"type": "string"},
        "summary": {"type": "string"},
        "steps": {"type": "array", "items": {"type": "string"}},
        "questions": {"type": "array", "items": {}}
    },
    "additionalProperties": True
}
```

**Subtopic Schema:**
- Supports recursive nesting up to 3 levels
- Can contain both `concepts` and `subtopics`
- Additional properties allowed for flexibility

### 3. Loading Content

**Supported Structures:**
1. **Flat files:** `content/subject_name.json`
2. **Subdirectories:** `content/subject_name/content.json` (legacy)

**Auto-detection:**
- Content Manager automatically detects and loads both structures
- Subject name derived from filename or `subject` field

---

## Examples

### Complete Concept Example

```json
{
  "name": "Newton's First Law of Motion",
  "summary": "Newton's First Law states that an object remains at rest or in uniform motion in a straight line unless acted upon by an external force. This property is called inertia. Understanding this law helps explain everyday phenomena like why passengers lurch forward when a bus stops suddenly.",
  "steps": [
    "State the law in words",
    "Define inertia and give examples",
    "Explain the importance of seat belts in vehicles",
    "Relate the law to real-life situations"
  ],
  "questions": [
    {
      "question": "State Newton's First Law of Motion.",
      "acceptable_answers": [
        "An object remains at rest or in uniform motion unless acted upon by an external force."
      ],
      "hints": [
        "Law of inertia."
      ]
    },
    {
      "question": "Why do passengers move forward when a moving bus stops suddenly?",
      "acceptable_answers": [
        "Due to inertia, their bodies tend to remain in motion even when the bus stops."
      ],
      "hints": [
        "Inertia of motion."
      ]
    }
  ]
}
```

### Nested Structure Example

```json
{
  "subject": "Science",
  "grade": 10,
  "topics": [
    {
      "name": "Physics",
      "subtopics": [
        {
          "name": "Force",
          "concepts": [
            {
              "name": "Definition and Effects of Force",
              "summary": "...",
              "questions": [...]
            }
          ]
        },
        {
          "name": "Work, Energy, and Power",
          "subtopics": [
            {
              "name": "Work and Energy",
              "concepts": [...]
            },
            {
              "name": "Power and Efficiency",
              "concepts": [...]
            }
          ]
        }
      ]
    }
  ]
}
```

---

## Contributing Content

### For Educators

**You can contribute by:**
1. Adding new concepts and questions
2. Improving existing explanations
3. Providing culturally relevant examples
4. Suggesting corrections and updates
5. Creating practice questions

**Contribution Process:**
1. Review existing content structure
2. Prepare your content following the schema
3. Validate JSON syntax
4. Submit via pull request or suggestion system
5. Respond to feedback and reviews

### For Developers

**Integration Points:**
- Content Manager API for programmatic access
- Schema validation for quality assurance
- Search functionality for content discovery
- Progress tracking integration
- RAG system integration for AI responses

**Testing:**
```python
# Test content loading
cm = ContentManager()
assert "Computer Science" in cm.get_all_subjects()

# Test content retrieval
concept = cm.get_concept("Computer Science", "Computer Network", "Introduction to Networks")
assert concept is not None

# Test search
results = cm.search_content("network")
assert len(results) > 0
```

---

## Troubleshooting

### Common Issues

**Validation Errors:**
- **Missing required field:** Add the required field (`subject`, `grade`, `topics`, or `name`)
- **Invalid JSON:** Check for syntax errors (missing commas, brackets)
- **Wrong data type:** Ensure arrays are `[]` and objects are `{}`

**Loading Errors:**
- **File not found:** Check file path and name
- **Permission denied:** Verify file permissions
- **Encoding issues:** Ensure UTF-8 encoding

**Content Not Appearing:**
- **Schema validation failed:** Check logs for validation errors
- **Incorrect nesting:** Verify topic/subtopic/concept hierarchy
- **Missing name field:** Ensure all levels have `name` field

### Debugging

**Enable Debug Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check Content Structure:**
```python
cm = ContentManager()
cm.debug_content_structure("Computer Science")
```

**Validate Manually:**
```python
from jsonschema import validate, ValidationError
try:
    cm._validate_content(content)
    print("Content is valid")
except ValidationError as e:
    print(f"Validation error: {e}")
```

---

## Future Enhancements

### Planned Features

**Content Types:**
- Interactive exercises
- Multimedia content (images, videos)
- Adaptive learning paths
- Gamification elements

**Technical Features:**
- Advanced analytics
- AI-powered content generation
- Mobile app support
- Cloud synchronization (optional)

**Community Features:**
- Collaborative editing
- Peer review system
- Content rating and feedback
- Translation support

---

## Support and Resources

### Documentation
- [Content Manager Source](../system/data_manager/content_manager.py)
- [Example Content Files](../scripts/data_collection/data/content/)
- [Project Standards](PROJECT_STANDARDS.md)
- [Technical Implementation](TECHNICAL_IMPLEMENTATION.md)

### Getting Help
- Open an issue on GitHub
- Contact project maintainers
- Review existing content for examples
- Check validation logs for errors

---

## Summary

Satya's content system provides a flexible, hierarchical structure for organizing educational materials. The schema balances structure with flexibility, allowing for diverse content types while maintaining consistency and quality.

**Key Takeaways:**
- Only `name` is required at each level
- Flexible nesting supports various content organizations
- Questions can be objects or strings
- Automatic validation ensures quality
- Community contributions are encouraged

By following these guidelines, you can create high-quality educational content that helps students learn effectively and contributes to Satya's mission of democratizing AI-powered education.
