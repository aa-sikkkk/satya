# ASCII Diagram Generation Guide

## Overview

The Satya Learning System includes an intelligent ASCII diagram generation feature that automatically creates visual representations of concepts to enhance student learning. This feature analyzes questions and answers to determine when a diagram would be helpful and generates the appropriate type of diagram.

## Features

### Automatic Detection
- Analyzes question intent (what/how/explain patterns)
- Examines answer structure (steps, sequences, hierarchies)
- Detects conceptual patterns (processes, flows, structures)
- Scores content complexity to determine visualizability

### Diagram Types

#### 1. Process Diagrams
Shows step-by-step sequences in a linear flow.

**Best for:**
- Sequences of events
- Procedures and methods
- Linear transformations

**Example:** Photosynthesis stages, chemical reactions

#### 2. Cycle Diagrams
Shows repeating processes with loop-back indicators.

**Best for:**
- Continuous cycles
- Repeating processes
- Circular transformations

**Example:** Water cycle, rock cycle, life cycles

#### 3. Structure Diagrams
Shows hierarchical relationships between components.

**Best for:**
- Part-whole relationships
- Organizational structures
- Component hierarchies

**Example:** Cell structure, network components

#### 4. Flowcharts
Shows decision-based logic with conditional branches.

**Best for:**
- Algorithms
- Decision trees
- Conditional processes

**Example:** Binary search, sorting algorithms

## How It Works

### 1. Question Analysis
The system analyzes the question using semantic patterns:
```python
# Process/flow patterns
"How does X work?"
"What is the process of X?"
"Explain how X happens"

# Structure patterns
"What is the structure of X?"
"What are the components of X?"
"How is X organized?"

# Decision/flowchart patterns
"How does X decide?"
"What is the algorithm for X?"
```

### 2. Answer Parsing
Multiple extraction strategies are used:

**Strategy 1: Numbered Steps**
```
Step 1: Light absorption
Step 2: Water splitting
Step 3: Carbon fixation
```

**Strategy 2: Sequential Markers**
```
First, water evaporates.
Then, vapor rises.
Finally, precipitation falls.
```

**Strategy 3: Process Lists**
```
Photosynthesis involves light absorption,
water splitting, and carbon fixation.
```

### 3. Diagram Generation
Based on detected patterns, generates appropriate ASCII art:
```
┌──────────────────┐
│  Light absorption  │
└─────────┬─────────┘
         │
┌─────────▼─────────┐
│  Water splitting   │
└─────────┬─────────┘
         │
┌─────────▼─────────┐
│  Carbon fixation   │
└───────────────────┘
```

## Usage

### In Student Interface

Diagrams are automatically appended to answers when appropriate. No special commands needed!

**CLI Interface:**
```bash
python -m student_app.interface.cli_interface
> What is the water cycle?
[Answer with diagram is displayed]
```

**GUI Interface:**
```bash
python -m student_app.gui_app.main_window
[Type question and diagram appears with answer]
```

### Programmatic Usage

```python
from system.diagrams import generate_and_append_diagram

question = "What is photosynthesis?"
answer = """Photosynthesis converts sunlight to energy.
Stage 1: Light Absorption
Stage 2: Water Splitting
Stage 3: Carbon Fixation"""

result = generate_and_append_diagram(question, answer)
print(result)
```

### Demo Script

Run the demo to see examples:
```bash
python scripts/demo_diagrams.py
```

## Configuration

### Adaptive Thresholds

The system uses adaptive thresholds that adjust based on content:

- **Minimum question length:** 3+ characters
- **Minimum answer length:** 10+ characters (adaptive)
- **Detection threshold:** 2+ indicators
- **Maximum diagram width:** 30-80 characters (adaptive)
- **Step extraction limit:** 2-10 steps (adaptive)

### Customization

Edit `system/diagrams/diagram_detector.py` to adjust patterns:

```python
# Add custom patterns
process_patterns = [
    r'\b(your|custom|pattern)\b',
    # ... more patterns
]
```

## Subject Coverage

### Science
- ✅ Chemical processes
- ✅ Biological cycles
- ✅ Physical phenomena
- ✅ Scientific methods

### Mathematics
- ✅ Algorithms
- ✅ Problem-solving procedures
- ✅ Mathematical operations

### Computer Science
- ✅ Data structures
- ✅ Algorithms
- ✅ Network architecture
- ✅ Programming concepts

### English/Language
- ✅ Grammar structures
- ✅ Sentence analysis
- ✅ Writing processes

### Other Subjects
The system uses semantic analysis, so it works across ANY subject!

## Performance

### Speed
- Detection: < 50ms
- Generation: < 100ms
- Total overhead: < 150ms

### Resource Usage
- No external dependencies
- Pure Python implementation
- Minimal memory footprint
- Non-blocking operation

## Troubleshooting

### Diagram Not Generated

**Possible reasons:**
1. Question too simple (< 3 chars)
2. Answer too short (< 10 chars)
3. No clear pattern detected
4. Content not visualizable

**Solutions:**
- Provide more detailed answers
- Use sequential markers (First, Then, Finally)
- Number steps explicitly (Step 1, Step 2)
- Describe processes or structures

### Diagram Quality Issues

**Problem:** Steps not extracted correctly

**Solution:** Use explicit markers:
```
Stage 1: [name]
Stage 2: [name]
Stage 3: [name]
```

**Problem:** Diagram too cluttered

**Solution:** Limit steps to 3-6 for best readability

### Debug Mode

Enable logging to see diagram generation process:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Testing

Run the test suite:
```bash
python tests/test_diagram_generation.py
```

Tests cover:
- Step extraction (sequential, numbered, lists)
- Diagram detection (process, structure, flowchart)
- Diagram generation (various types)
- Validation (format, quality)

## Examples

### Example 1: Water Cycle (Cycle Diagram)
```python
Q: "What is the water cycle?"
A: "First, water evaporates. Then, vapor condenses. Finally, precipitation falls."

Result: Cycle diagram with 3 stages and loop-back
```

### Example 2: Photosynthesis (Process Diagram)
```python
Q: "How does photosynthesis work?"
A: "Stage 1: Light Absorption. Stage 2: Water Splitting. Stage 3: Carbon Fixation."

Result: Linear process diagram with 3 stages
```

### Example 3: Network Structure (Structure Diagram)
```python
Q: "What is a computer network structure?"
A: "A network consists of computers, routers, switches, and cables."

Result: Hierarchical structure diagram
```

## Best Practices

### For Students
1. Ask clear, specific questions
2. Use "How" or "What" for processes
3. Use "Structure" or "Components" for hierarchies

### For Teachers/Content Creators
1. Use explicit step markers (First, Then, Finally)
2. Number stages clearly (Stage 1, Stage 2)
3. List components explicitly
4. Keep steps concise (2-4 words)

### For Developers
1. Test with diverse question types
2. Validate diagram output format
3. Handle edge cases gracefully
4. Monitor performance overhead

## Future Enhancements

Planned improvements:
- [ ] More diagram types (timeline, comparison, cause-effect)
- [ ] Enhanced layout algorithms
- [ ] Color support (for terminals that support it)
- [ ] Export to image formats
- [ ] Interactive diagrams
- [ ] Diagram editing interface

## Contributing

To contribute to diagram generation:

1. Add new patterns to `diagram_detector.py`
2. Extend extraction strategies in `custom_generator.py`
3. Add new diagram types
4. Write tests for new features
5. Update documentation

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

Part of the Satya Learning System - MIT License

---

**Note:** This feature is designed to enhance learning, not replace it. Diagrams are generated automatically to supplement textual explanations and provide visual learners with additional support.
