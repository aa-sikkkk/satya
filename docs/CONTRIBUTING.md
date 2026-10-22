# Contributing to Satya

## Purpose of Contributions

Thank you for considering contributing to **Satya**, an intelligent learning companion designed to democratize AI-powered education. Your involvement is critical to ensuring this project serves its mission effectively and efficiently.

---

## Mission Statement: Promoting Education Accessibility

The lack of internet access affects 2.9 billion people globally. In Nepal alone, 60% of students face challenges due to limited connectivity and outdated hardware. Satya aims to break down these barriers.

Satya focuses on:

- **Offline-First Functionality:** Ensuring usability without the need for internet
- **Low-Resource Optimization:** Operating on minimal hardware requirements
- **Intelligent RAG System:** Delivering AI tutoring without relying on cloud infrastructure
- **Community-Driven Content:** Allowing educators to define the curriculum
- **Cost-Free Accessibility:** Removing financial hurdles

---

## Contributor Categories and Areas of Focus

### Educators and Teachers
- Provide curriculum materials
- Improve educational content quality
- Offer pedagogical insights and test the system

### Developers
- Enhance performance for low-resource environments
- Optimize RAG retrieval accuracy
- Improve UI/UX
- Fix bugs and introduce features

### Content Creators and Writers
- Develop comprehensive educational materials
- Contribute to documentation
- Translate content for diverse audiences

### Designers
- Elevate interface and aesthetic design
- Simplify workflows

### Testers and Students
- Test software features
- Offer feedback to improve usability
- Suggest innovative ideas

### Community Advocates 
- Increase awareness of the project
- Facilitate onboarding for new contributors
- Advocate for equitable education solutions

---

## Code of Conduct

Participation in Satya requires:
- Respectful and constructive communication
- Acceptance of diverse ideas and feedback
- Empathy and community-focused practices

We maintain zero tolerance for any form of harassment or discrimination.

---

## Contribution Guide

### Key Steps:
1. **Fork the Repository**
2. **Clone Locally**
3. **Create a Feature Branch**: `git checkout -b feature/<branch-name>` (branch from `develop` for routine work, from `master` for hotfixes)
4. **Develop Based on Requirements**
5. **Write Clear Commit Messages**
6. **Push Changes**
7. **Open a Pull Request** — merge is PR-only: `master` and `develop` are
   protected on GitHub (no direct pushes, even for the maintainer). Required:
   green CI (`Lint & type check`, `Tests (py3.11)`, `Tests (py3.12)`,
   `Dependency audit`), all conversations resolved, linear history.

### Automated Code Review (CodeRabbit)

Every pull request is automatically reviewed by [CodeRabbit](https://coderabbit.ai),
an AI code-review bot that is **free for open-source repositories**:

- On each PR it posts a high-level summary, walk-through, and line-by-line
  comments (no API key or account required for public repos)
- It flags violations of our offline-first and low-resource constraints
  (new runtime network calls, GPU dependencies, unbounded caches)
- You can reply to its comments (`@coderabbitai ...`) to ask questions or
  request re-reviews; it never blocks merge on its own

Behavior is configured in `.coderabbit.yaml` at the repository root. Human
review per `docs/PROJECT_STANDARDS.md` Git-flow remains required for merge.

### Reporting Issues:
For issues, include:
- A clear problem description
- Reproduction steps
- Expected versus observed behavior
- Technical environment details

### Feature Proposals:
For feature proposals, outline:
- The problem the feature resolves
- The feature’s alignment with accessibility and low-resourced environments
- Potential implementation details (optional)

---

## Development Standards

### Coding Principles:
- Adhere to [PEP 8](docs/PROJECT_STANDARDS.md#11-python-code-style)
- Format code with Black
- Integrate type hints and write Google-style docstrings
- Use linters such as Flake8 and Isort

### Testing Standards:
- Implement unit tests for new code contributions
- Maintain coverage recommendations

---

## Content Contributions

### Quality Standards
Material submissions should prioritize:
- Clear language and cultural sensitivity
- Appropriate complexity and inclusivity
- Fact-checked accuracy

Use automated validation scripts to ensure schema adherence (`python scripts/validation/validate_standards.py`).

---

## How to Offer Documentation
All documentation should:
- Follow standards as specified in `PROJECT_STANDARDS.md`
- Use simple and explanatory language
- Include examples

---

## Benefits of Contributing

### Contributor Recognition:
- Acknowledged within project documentation
- Invited to community forums
- Highlighted in release notes

### Real-World Impact
Contributors shape educational opportunities for underserved communities while bridging technological gaps.

---

## Get Started
Start small and build momentum. Contribute by fixing write comments, codes, and reporting in a designated issue tracker or posting constructive inputs to relevant GitHub channels.