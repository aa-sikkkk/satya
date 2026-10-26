# Changelog

All notable changes to the Satya Learning System are documented here.
Format follows the same spirit as [Keep a Changelog](https://keepachangelog.com/); project uses calendar-agnostic semantic-ish release numbering.

## Unreleased

- Student offline packaging — `feat:` wheel+sdist build, fully offline Windows installer bundle (`Satya_Student_Offline_Win.zip`), `satya`/`satya-gui` console commands, release-assets workflow driven by release-please

## [2.3.0](https://github.com/aa-sikkkk/satya/compare/v2.2.0...v2.3.0) (2026-10-26)


### Features

* Add Input Normalization System with adaptive learning ([d23cca8](https://github.com/aa-sikkkk/satya/commit/d23cca86196e4e4fefb0665ad1c6f67f9e9ca349))
* Add model and RAG warm-up to reduce initialization overhead ([177289f](https://github.com/aa-sikkkk/satya/commit/177289fada82684212559f242a3189cddff1b18d))
* Diagram enhancement ([139bbfc](https://github.com/aa-sikkkk/satya/commit/139bbfc99bd9daca0a89e9efc50a190e96766230))
* **Diagrams:** foundation for ASCII digrams. ([aef90c1](https://github.com/aa-sikkkk/satya/commit/aef90c1c4c710534b54d6a25f94eed1b3f689cc6))
* **Diagram:** updated the ASCII diagram modules to better fit the answers. ([a00a5f0](https://github.com/aa-sikkkk/satya/commit/a00a5f004c6c8b622a05aba7d1c002fec16220ea))
* enforce strict JSON validation and refactor standards script ([87e2137](https://github.com/aa-sikkkk/satya/commit/87e2137d23f3229fc8b209f80b6f8c3b63a7f4c8))
* implementation of  RAG + Phi 1.5 architecture with answer length control ([5c9302c](https://github.com/aa-sikkkk/satya/commit/5c9302c5768cb30013ca996d54c8025e7aec84bc))
* optimize RAG pipeline and simplify Phi 1.5 integration for old processors. ([23641e5](https://github.com/aa-sikkkk/satya/commit/23641e5c207565d4ed4e8dac811001b094e3b739))
* optimize RAG pipeline and simplify Phi 1.5 integration for old processors. ([f6b2349](https://github.com/aa-sikkkk/satya/commit/f6b2349e022c8bf2264bac04ccb8a8a3a7ae63a2))
* **RAG:** single script for both Notes and PDF ([11756ec](https://github.com/aa-sikkkk/satya/commit/11756ecda0bd644664f3aff454d13128185ffd81))
* student offline packaging + automated release assets ([#34](https://github.com/aa-sikkkk/satya/issues/34)) ([0510d3f](https://github.com/aa-sikkkk/satya/commit/0510d3f8dd4a439c9ecf692073a78fd9fcf85b8a))
* **teacher-tools:** integrate Content Manager with Content Editor CLI ([6c1ced8](https://github.com/aa-sikkkk/satya/commit/6c1ced82880da7d6e5886901805a921d490a7e30))
* **ui:** Added Answering streaming foundational UI. ([e823e3d](https://github.com/aa-sikkkk/satya/commit/e823e3dd786aa5c0c378eaddbb9998c5b1e63685))
* **ui:** GUI Redesigned for responsive layout. ([cc21d06](https://github.com/aa-sikkkk/satya/commit/cc21d06d7bb4f35fca9846dcca031a2fc5f061f0))
* Update license to AGPLv3, refactor diagram system, and fix UI layout. ([b17c489](https://github.com/aa-sikkkk/satya/commit/b17c489f299ef480ab00c0cc27bf79746f71463f))


### Bug Fixes

* cli answer streaming layout and hotkey bugs ([377b1ab](https://github.com/aa-sikkkk/satya/commit/377b1abdc1632c92504212544b39e165612b22c9))


### Performance Improvements

* Add conditional spell-checking and caching to Input Normalization ([7bced09](https://github.com/aa-sikkkk/satya/commit/7bced09096c6bb5cf359b1621e00ef17014fc7db))


### Documentation

* Refine prompting advice and code cleanup ([29d9299](https://github.com/aa-sikkkk/satya/commit/29d929994f9deca3d74964f202687aaf3bffd123))

## [2.2.0] — 2026-02

- Diagram System Overhaul — modular `system/diagrams` package with grade-aware library (Grades 8–12) and natural triggering logic
- CLI/GUI parity — reconciled AI grading logic, robust fallback for missing `correct_answer` fields
- Input Normalization System — rule-based 4-layer noise removal, pattern mining from production logs
- Enhanced RAG architecture — 7 HuggingFace datasets, subject/grade-based collection routing, semantic cache
- Single Phi 1.5 model runtime (Q4_K_M GGUF, CPU-only)
- Universal content ingestion (`scripts/ingest_content.py`) with OCR support
- Progressive UX status updates during retrieval

## [2.3.0-unreleased] — in progress

### automation
- Installed free-for-OSS bot stack: CodeRabbit PR review (`.coderabbit.yaml`), Dependabot version updates for pip + GitHub Actions (`.github/dependabot.yml`), release-please (Conventional-Commits-driven version/CHANGELOG/GitHub-release automation, `release-please-config.json`), PR auto-labeler, stale bot (issues close after grace; PRs never auto-closed), Conventional-Commits PR title lint
- Enabled Dependabot vulnerability alerts + automated security fixes in repo settings
- Added Conventional-Commits as the merge convention bots depend on (PR titles, `feat:`/`fix:`/`chore:`/etc.; next version derives automatically — `feat:` → 2.3.0)
- Created the 11 path labels the labeler configuration expects (rag/gui/cli/model/ingestion/diagrams/teacher-tools/tests/docs/ci/dependencies)
- Master-only branch policy: `master` is the sole integration branch; feature branches PR directly into it; workflow triggers trimmed to push/PR on master plus a weekly compatibility run

### CI efficiency & correctness
- CI now passes: 2,137 mechanical violations auto-fixed repo-wide (whitespace/imports/format via ruff+black+isort) plus 16 genuine bugs repaired, including the `except Exception as e:` closure bug (`NameError` when error popups triggered — 6 GUI paths crashed on any load failure), missing `csv`/`os`/`ImageTk` imports, dead locals, unschema'd test fixtures (`steps` required by the concept schema), and stale assertions superseded by the improved politeness-stripping order
- `AdaptiveNormalizer` spell checking is now an explicit opt-in (`SATYA_SPELL_CHECK=1` env or `enable_spell_check` kwarg) — it transitively launched a network root process (LanguageTool jar fetch / hosted-API fallback), violating offline-first; cache accounting now works without the tool loaded
- `requires_model` markers applied to RAG/benchmarks/integration suites; CI (and local runs without binaries) deselects them — full run finishes in ~84 s instead of hanging
- Local proven bugs: pytest-timeout added (300 s hang guard), coverage `source` scoped to `system`, RAG internals omitted with rationale, gate set to measured model-free baseline 55% (goal remains 80% incl. model tests locally per standards)
- pip-audit: 5 ignored advisory IDs with per-item justification comments (chromadb 1.5.9 = latest, unfixable server-side tenancy paths irrelevant offline; diskcache pickle RCE requires attacker write access to local cache dir) — re-check on next releases
- Leaner runner minutes: per-job timeouts (10/30/10), pip cache for the audit job, push-only `paths-ignore` for docs-only work (PRs still always run required checks)

### chores
- Removed stale root artifacts (June–Aug 2025 scratch files, legacy `config.yaml` not loaded by any code, benchmark logs) — authoritative docs now live in `docs/`
- Moved `RAG_SYSTEM_DESIGN.md`, `DATASETS.md`, `METADATA_SCHEMA.md`, `HOW_TO_PROCESS.md`, `PROJECT_STRUCTURE.md` into `docs/`
- Untracked ChromaDB index pickles (`satya_data/chroma_db/`) — graph data is regenerated by `scripts/ingest_content.py`, never committed
- Rewrote `.gitignore` (removed self-contradictory negation rules and `.gitignore`-ignoring-itself entries)

### packaging
- Split dependencies: `requirements.txt` (runtime core), `requirements-ocr.txt`, `requirements-nlp.txt`, `requirements-dev.txt`
- Added `pyproject.toml` (PEP 621 metadata, Black/isort/ruff/mypy/pytest/coverage config, Python floor >= 3.11)

### tooling / agentic build
- Added GitHub Actions CI: lint (ruff+black+isort), tests on Python 3.11/3.12 with coverage gate (`not requires_model`; gate re-baselined to a measured model-free floor in 2.3.0), dependency audit
- Added PR template + bug/feature issue templates aligned with `docs/PROJECT_STANDARDS.md`
- Added repo-level `AGENTS.md` (agent contract incl. codebase-memory graph workflow)

### code
- Removed unused `log_performance_metric` from `system/performance/performance_utils.py` (0 callers verified; the other two graph-flagged functions are in active use and intentionally kept)
- Fixed model-path drift: unified model dir on `satya_data/models/phi15/` (readme + `scripts/load_models_offline.py`; the loader scans only `phi15` — the `phi_1_5` path would have downloaded weights where the app cannot read them)
- Fixed context-window doc drift: 2048 confirmed from `phi15_handler.py`; corrected README version-history claim
- Fixed license badge drift: MIT badge → PolyForm Noncommercial badge (matches LICENSE)
- Removed retired "NEBedu" naming from `docs/PROJECT_STANDARDS.md`
- Fixed version drift — single version source: `pyproject.toml` (2.2.0); `ai_model.__version__` now reads installed metadata (graceful fallback in plain checkouts)
- Moved `USER_GUIDE.md` → `docs/USER_GUIDE.md` (GUI view updated with root fallback)
- `docs/PROJECT_STRUCTURE.md` rewritten as the authoritative, graph-verified directory map (adds optional `OpenAi_Proxy/` service, dependency-direction rules, runtime-data layout)
