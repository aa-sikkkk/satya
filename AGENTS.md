# AGENTS.md — Satya Learning System

Instructions for AI coding agents and human contributors working in this repository.

## Project identity

**Satya** is an offline-first RAG learning companion for Nepal Grades 8–12 (NEB curriculum).
Target hardware: **4GB RAM, CPU-only i3**. Everything works without internet at runtime.

**Non-negotiable constraints**
1. No new runtime network calls. Dev-time downloads (models, datasets) must be cached and documented.
2. No model swap that exceeds ~1GB inference memory. Inference stays CPU-only (`n_gpu_layers: 0`).
3. Keep `system/`, `student_app/`, `ai_model/`, `teacher_tools/`, `scripts/` boundaries clean — `get_architecture` should stay cycle-free.

## Setup (Windows PS / Linux)

```bash
python -m venv venv
source venv/bin/activate          # PS: venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
# Optional: pip install -r requirements-ocr.txt -r requirements-nlp.txt
```

LLM model binaries live in `satya_data/models/` (gitignored, downloaded one-time). CI never needs them.

## Commands

| Action | Command |
|---|---|
| Run tests (CI-safe) | `pytest -m "not requires_model"` |
| Run full tests (local, needs model) | `pytest` |
| Lint | `ruff check .` |
| Format check / apply | `black --check .` / `black .` |
| Type baseline | `mypy .` (see pyproject excludes) |
| Student CLI | `python -m student_app.interface.cli_interface` |
| Student GUI | `python -m student_app.gui_app.main_window` |
| Ingest content | `python scripts/ingest_content.py --ocr-mode auto` |

## Code map (entry points)

- `student_app/main.py` — app entry; `student_app/interface/` CLI; `student_app/gui_app/` CustomTkinter GUI
- `system/rag/rag_retrieval_engine.py` — RAG core; `system/rag/rag_cache.py` — semantic cache
- `system/diagrams/` — ASCII diagram engine (service/library/renderer/config)
- `system/input_processing/` — query normalization
- `ai_model/model_utils/phi15_handler.py` — Phi-1.5 GGUF handler (llama-cpp-python)
- `scripts/ingest_content.py` — universal content ingestion
- `tests/` — pytest suite (`requires_model` marker for model-dependent tests)

## Working with the knowledge graph (codebase-memory-mcp)

This repo is usually indexed into a codebase-memory-mcp graph. Prefer graph queries over grep for structural questions:

- Structural search: `search_graph`, `search_code` (indexed files only)
- Call tracking: `trace_path(function_name=..., direction="both")`
- Change impact: `detect_changes()` after editing
- Dead-code candidates: `search_graph(max_degree=0, exclude_entry_points=true)`

Rules:
1. After making candidate-path claims, run `check_index_coverage` before making negative or exhaustive claims.
2. If the index is stale after large edits, re-run `index_repository` before concluding "no callers".
3. Indexing needs no API key; it reads `.gitignore` for scope.

## Cleanup policy

Root directory contains only project-level files (readme, LICENSE, requirements*, pyproject, config-era docs live in `docs/`). Do not create scratch files at root; use `plan/` for proposals (one markdown per plan; existing example: `plan/plan.md`, `plan/upgrade_plan.md`).

`plan/` is intentionally untracked: it is excluded via `.git/info/exclude` (local, not in `.gitignore`), so plan documents stay local working notes and never enter commit history. Keep agents' proposal drafts there; reference them in PRs by content, not by file path.

**Never mention `plan/` in commit messages, PR titles, or PR bodies** — plans are the maintainer's private working notes. **Always ask the user before pushing** any branch or force-update; never push proactively.

## CHANGELOG

Public changes must append a bullet to `CHANGELOG.md` (create if missing, section per version).

## Branch & merge policy (enforced on GitHub)

`master` and `develop` are protected — **even for the maintainer**. Never push
directly; work on a feature branch (`feature/<name>`, `fix/<name>`) and open a
PR into `master` (or `develop` for batched integration). Protection requires:
PR-only merge, green CI (lint/test-matrix/audit), all conversations resolved,
linear history. CodeRabbit reviews every PR automatically (free for OSS).

## Documentation source-of-truth

`docs/PROJECT_STANDARDS.md` is the standards baseline (PEP 8 @ 88 chars, Google docstrings, 80% coverage, Git-flow reviews). `docs/PROJECT_STRUCTURE.md` mirrors the directory layout. `docs/TECHNICAL_IMPLEMENTATION.md` and `docs/RAG_SYSTEM_DESIGN.md` (moved) explain the internals. `readme.md` is user-facing only.

## Model/config reality check

`config.yaml` was removed as dead weight: it is not loaded by any code and pointed to a BitNet model that contradicted the Phi-1.5 runtime. If you reintroduce runtime configuration, wire it in code AND update `docs/CONFIGURATION.md`-style docs + README in the same PR.
