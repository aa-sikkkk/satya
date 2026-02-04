# Satya Diagram Library

The Satya Diagram Library is a curated repository of structured educational diagram data designed for the NEB (Nepal Education Board) curriculum. This component provides the underlying data model for the application's runtime ASCII diagram generation system.

## Overview

The library functionality moves away from non-deterministic generation methods to a static, verified data source. This architectural choice prioritizes:

*   **Accuracy**: Every diagram is manually reviewed to ensure pedagogical correctness.
*   **Consistency**: Identical queries strictly yield identical, standardized visualizations.
*   **Performance**: Elimination of runtime inference latency.
*   **Availability**: Full functionality in offline environments with no external dependencies.

## Directory Structure

The database is organized by subject matter, with individual files segmented by grade level or specific chapters.

```
Diagramsdb/
├── README.md                    # Documentation and specification
├── _schema_template.yaml        # Reference schema definition
│
├── science/                     # Biology, Physics, and Chemistry data
│   ├── _index.yaml              # Subject-level metadata
│   ├── grade_10.yaml            # Consolidated grade-level data
│   └── ...
│
├── computer_science/            # Computing and ICT data
│   ├── _index.yaml
│   ├── grade_11.yaml
│   └── ...
│
├── mathematics/                 # Algebraic and Geometric data
│   ├── _index.yaml
│   └── ...
│
└── english/                     # Grammar structures and Literature
    ├── _index.yaml
    └── ...
```

## Data Specification

Diagrams are stored as structured YAML data. The application's rendering engine interprets this data at runtime to construct the visual representation.

### Schema Definition

Each entry requires specific fields to ensure correct indexing and rendering.

**Required Fields:**
*   `concept_name`: Unique identifier (snake_case).
*   `type`: The visualization category (process, comparison, hierarchy, structure, or timeline).
*   `title`: The human-readable display title.
*   `keywords`: An array of search terms used for retrieval matching.

**File Metadata:**
Subject files must contain a header defining the context:

```yaml
metadata:
  subject: "Science"
  grade: 10
  version: 1.0
  last_updated: "2026-02-03"

diagrams:
  # Diagram definitions follow
```

## Diagram Categories

The system supports five distinct visualization types, each with specific schema requirements.

### 1. Process Diagrams

Used for sequential workflows, cycles, or algorithms.

**Schema:**
```yaml
photosynthesis_mechanism:
  type: process
  title: "Photosynthesis Process"
  keywords: ["photosynthesis", "chlorophyll", "energy conversion"]
  steps:
    - Light absorption
    - Water splitting
    - Electron transport
    - ATP formation
    - Carbon fixation
  cyclic: false  # Set to true for closed-loop systems
```

### 2. Comparison Diagrams

Used for side-by-side analysis of two distinct entities.

**Schema:**
```yaml
mitosis_vs_meiosis:
  type: comparison
  title: "Mitosis vs Meiosis"
  keywords: ["cell division", "mitosis", "meiosis"]
  item_a: "Mitosis"
  item_b: "Meiosis"
  similarities:
    - "Fundamental cell division process"
    - "Preceded by DNA replication"
  differences:
    divisions: ["Single division", "Double division"]
    daughter_cells: ["Two identical diploid", "Four unique haploid"]
    function: ["Somatic growth", "Gamete production"]
```

### 3. Hierarchy Diagrams

Used for taxonomies, organizational charts, and classification trees.

**Schema:**
```yaml
biological_classification:
  type: hierarchy
  title: "Animal Kingdom Classification"
  keywords: ["taxonomy", "vertebrates", "invertebrates"]
  root: "Animal Kingdom"
  children:
    - name: "Vertebrates"
      children: ["Mammals", "Birds", "Reptiles", "Amphibians", "Fish"]
    - name: "Invertebrates"
      children: ["Arthropods", "Mollusks", "Annelids"]
```

### 4. Structure Diagrams

Used to detail the components or anatomy of a system.

**Schema:**
```yaml
plant_cell_anatomy:
  type: structure
  title: "Plant Cell Structure"
  keywords: ["cytology", "plant cell", "organelles"]
  main: "Plant Cell"
  components:
    - name: "Cell Wall"
      description: "Structural support layer"
    - name: "Chloroplast"
      description: "Site of photosynthesis"
    - name: "Vacuole"
      description: "Turgor pressure regulation"
```

### 5. Timeline Diagrams

Used for chronological series and historical sequences.

**Schema:**
```yaml
computing_history:
  type: timeline
  title: "Evolution of Computing"
  keywords: ["history", "generations", "hardware"]
  events:
    - period: "1940-1956"
      name: "First Generation"
      detail: "Vacuum Tube technology"
    - period: "1956-1963"
      name: "Second Generation"
      detail: "Transistor adoption"
```

## Contribution Standards

To maintain library integrity, contributors must adhere to the following guidelines:

1.  **Subject Placement**: Ensure data is located in the appropriate subject directory and grade-level file.
2.  **Keyword Optimization**:
    *   Include the precise educational term.
    *   Include standard variations and synonyms.
    *   All keywords must be lowercase.
3.  **Content Clarity**:
    *   Labels should be concise (2-5 words).
    *   Use standard academic terminology compliant with NEB textbooks.
    *   Use active verbs for process steps.

## System Integration

The retrieval mechanism operates on a deterministic logic flow:

1.  **Extraction**: The system parses the user query to identify key educational concepts.
2.  **Matching**: Extracted terms are matched against the diagram index using a fuzzy scoring algorithm.
3.  **Selection**: The candidate with the highest confidence score (exceeding the 0.3 threshold) is selected.
4.  **Rendering**: The schema is serialized into the specific ASCII format required by the relevant renderer.

## Validation

Data integrity is enforced through automated validation scripts.

**Run Validation:**
```bash
python scripts/validate_diagrams.py
```

**Coverage Analysis:**
```bash
python scripts/diagram_coverage.py
```

## Support

For technical inquiries regarding the data schema or rendering pipeline, please file an issue in the project repository with the `diagram-library` tag.
