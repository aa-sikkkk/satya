# Changelog

All notable changes to the Satya Learning System are documented here.
Format follows the same spirit as [Keep a Changelog](https://keepachangelog.com/); project uses calendar-agnostic semantic-ish release numbering.

## Unreleased

- Model asset flow — release pipeline downloads the pinned `phi-1_5.Q4_K_M.gguf` (sha256 + size verified in CI), zips and attaches `Satya_Phi_1_5_Model_Win.zip` at publish (immutable-release safe); QUICKSTART + installer reference the exact asset name; `package_model.ps1` kept for manual mirroring; release checklist updated in CONTRIBUTING

## [2.4.0] — 2026-10-27

- Knowledge-base pipeline — vectordb is a reproducible build artifact: deterministic hash-ID flattener (`content_flattener.py`), one-command `build_vectordb.py` (validate/rebuild), `.json` curriculum support in `ingest_content.py`, release pipeline builds + bundles the knowledge base (updates idempotent), content-contribution flow documented

## [2.3.0] — 2026-10-26

- Student offline packaging — wheel+sdist build, fully offline Windows installer bundle (`Satya_Student_Offline_Win.zip`), `satya`/`satya-gui` console commands, `install_satya.ps1` + QUICKSTART shipped with releases
- Release process — manual, tag-driven releases (protocol in CONTRIBUTING.md); automated per-merge release PRs removed
- Resource resolution — `SATYA_BASE_PATH` env override so pip-installed launchers resolve `satya_data/` in the student workspace (with tests)
- CI hardening — master-only branch flow, trimmed Actions minutes (weekly py3.11 compat instead of per-PR), pinned lint toolstack installed straight from `requirements-dev.txt`, idempotent release-asset uploads
- Input normalization — vocative-only casual address handling with punctuation separators; query-term preservation for `bro`/`dude` subjects
- Bot-gated dependency bumps merged: black 25.12.0, ruff 0.17.2 pins, pandas floor 2.3.3, tqdm floor 4.70.1, actions group (checkout v7, setup-python v6, labeler v7, stale v11), release action leftovers (now in repo history channel)

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

## [2.2.0] — 2026-02

- Diagram System Overhaul — modular `system/diagrams` package with grade-aware library (Grades 8–12) and natural triggering logic
- CLI/GUI parity — reconciled AI grading logic, robust fallback for missing `correct_answer` fields
- Input Normalization System — rule-based 4-layer noise removal, pattern mining from production logs
- Enhanced RAG architecture — 7 HuggingFace datasets, subject/grade-based collection routing, semantic cache
- Single Phi 1.5 model runtime (Q4_K_M GGUF, CPU-only)
- Universal content ingestion (`scripts/ingest_content.py`) with OCR support
- Progressive UX status updates during retrieval
