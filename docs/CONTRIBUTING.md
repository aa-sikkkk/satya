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
3. **Create a Feature Branch**: `git checkout -b feature/<branch-name>` (branch from `master`)
4. **Develop Based on Requirements**
5. **Write Clear Commit Messages** (Conventional Commits)
6. **Push Changes**
7. **Open a Pull Request** — merge is PR-only: `master` is
   protected on GitHub (no direct pushes, even for the maintainer). Required:
   green CI (`Lint`, `Tests (py3.12)`,
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

## Content Contribution Flow (knowledge base)

The vectordb is a **build artifact** - never committed. The repo owns the
source of truth (content files + pipeline), and releases carry the built DB
so teachers/students always get the newest version by downloading from
Releases.

### Adding or revising curriculum content

1. Edit or add a curriculum JSON in
   `scripts/data_collection/data/content/` - one file per subject/grade
   batch. Shape (see `English_Grammar.json`):
   `subject`, numeric `grade`, `topics[].subtopics[].concepts[]` with
   `name` + `summary` + optional `steps`.
2. Validate locally (fast, no model downloads):
   `python -m scripts.build_vectordb --check`
3. Rebuild locally to verify ingestion (needs `chromadb` +
   `sentence-transformers`; CPU-only):
   `python -m scripts.build_vectordb`
4. Open the PR with the content change. Review by a maintainer merges it
   into `master`.

### Revision semantics

Chunk ids are content hashes of
`subject|grade|topic|subtopic|concept` (`content_flattener.py`), and
`build_vectordb.py` prunes database entries whose ids are no longer
produced by the tracked files, so:

- re-ingesting after an edit **replaces** the old chunk - no duplicates;
- re-ingesting after a rename/delete **removes** the obsolete chunk;
- chunk generation is deterministic (covered by
  `test_flatten_produces_deterministic_items`).

### How updates reach students

- Each tag/release: `release-assets.yml` runs `build_vectordb.py` on the
  runner, attaches `Satya_Knowledge_Base.zip`, and bundles the same DB
  inside `Satya_Student_Offline_Win.zip` - fresh installs and KB updates
  both come from the release page.
- Teachers unpack the newest `Satya_Knowledge_Base.zip` and copy the
  `chroma_db` folder from inside `knowledge_base\` over
  `satya_data/chroma_db` on the students' machine (QUICKSTART documents
  the 60-second step). No internet required on student hardware.

### Content quality rules

- One file per subject/grade batch; keep `subject` stable (it keys the
  collection name `neb_{subject}_grade_{grade}`).
- Grade must be an integer in NEB range 8-12 (enforced by the flattener).
- Optionally run `python scripts/validation/validate_standards.py` for
  language standards checks.
- Cultural sensitivity and accuracy per the Content Contributions section
  above still apply.

---

## Release Process (maintainer-only, manual)

Releases are deliberately batched - **nothing publishes automatically** when
PRs are merged. The full protocol:

1. Merge feature/fix PRs into `master` (every merge is CI-gated, releases are
   not a side effect of merges).
2. When the maintainer decides it is release time, cut a release PR:
   `chore: release vX.Y.Z` - bumps the version in `pyproject.toml` and
   finalizes the `CHANGELOG.md` section for the batch. It goes through the
   same CI + review as every other PR.
3. Merge the release PR only when satisfied with the batch.
4. Push the tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.
   This is the only trigger for the release pipeline
   (`release-assets.yml`): it builds the wheel + sdist, assembles the fully
   offline Windows student installer, creates the GitHub Release with
   auto-generated notes, and attaches the artifacts.
5. Verify the release page lists the wheel, sdist, and
   `Satya_Student_Offline_Win.zip` + `Satya_Student_Installer_Win.zip`.

There is no automated release bot; old release-please config was removed on
purpose to keep the decision in maintainer hands.

---

## Attribution & Credits (policy)

Satya gives every contributor proper credit. Nothing publishes without the
attribution story being accurate.

### Commit authorship (the source of truth)

GitHub credits are derived from commit metadata, so authorship is preserved
mechanically:

- PRs merged **squash** set the squashed commit's author to the **PR author**
  by default - keep that intact when collapsing so the author line is not
  rewritten to a different account.
- GitHub does **not** automatically credit additional human commit authors.
  Co-authors are credited with one `Co-authored-by: Name <email>` trailer
  per human, using an email associated with that person's GitHub account
  (then GitHub renders a co-author panel under the commit). You can also
  set the commit author explicitly:
  `git commit --author="Name <email>"`.
- Reviewers, merge committers, and significant helpers go in the README
  [Contributors table](../readme.md#contributors). Update it in the PR that
  gives them credit (plain rows, one per line).

### Human work

- Original PR authors and co-authors get credit via squash-merge authorship
  and the Contributors table on meaningful participation.
- Non-code contributions (curriculum content, docs, translations, outreach,
  issue triage) are first-class: add the contributor to the README table
  with their area, and tag the domain labels on the PR for changelog
  grouping.

### AI-assisted contributions

- Changes made with AI coding agents MUST disclose it: commit messages carry
  `Co-authored-by: opencode <opencode@localhost>`. Note the `localhost`
  email is an **internal disclosure marker** only - GitHub creates a
  co-author panel exclusively for emails bound to a GitHub account, so this
  trailer is about honest documentation rather than a visible panel. If the
  agent's metadata later has an account-bound email, switch the trailer to
  it.
- The AI agent is never the "author" of a commit; the human who reviews,
  tests, and pushes is the author and is accountable for correctness.

### Bots

- Automated actors (Dependabot, CodeRabbit, release pipeline) are credited
  where they act: Dependabot PRs land under their own author credit,
  CodeRabbit review threads count as reviews by their findings, and the
  release pipeline shows asset phases in the release workflow run.
- Bot credits live in the README table as separate, clearly-labelled rows -
  do not list bot accounts together with humans, and do not list a bot as
  the maintainer.

### Release notes

Release notes are generated with `gh release create --generate-notes`
(step 4 of the release protocol above). Per GitHub release-notes behavior:

- the generated **Contributors** panel credits commit authors (incl.
  `Co-authored-by` trailers) of the commits described in the release;
- the generated **Pull requests** section lists the merged PRs of the
  batch.

Verify the release page shows the documented contributor information
(step 5 of the release protocol).

### Third-party content

Curriculum content, models, datasets, and libraries keep the licences
documented in the README Acknowledgments section - attribution stays with
the upstream source (`OpenStax`, `ScienceQA`, `Phi-1.5`, etc.). When a new
source is added to the knowledge base, its citation block goes into the
README and the dataset documentation.

### Citation

The `CITATION.cff` gives academic users a one-click citation export
(GitHub renders the "Cite this repository" panel from it). Update its
`version` and `date-released` fields as part of the release PR.

---

## Get Started
Start small and build momentum. Contribute by fixing write comments, codes, and reporting in a designated issue tracker or posting constructive inputs to relevant GitHub channels.