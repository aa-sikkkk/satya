# CLAUDE.md — Satya Learning System (Claude Code entry point)

@AGENTS.md

## Claude Code specifics

- The repo is indexed into a **codebase-memory-mcp** graph. Prefer MCP graph tools
  (`search_graph`, `trace_path`, `get_architecture`, `detect_changes`) over grep/glob
  for structural questions; fall back to exact source reads before claims.
- Model binaries are gitignored and absent in CI. Tests marked
  `@pytest.mark.requires_model` are skipped with: `pytest -m "not requires_model"`.
- Windows PowerShell is the primary shell here. Quote paths that contain spaces;
  avoid `&&` (use `; if ($?) { ... }`).
- Never commit without explicit user request. Never add secrets; `satya.log`,
  `satya_data/` run data, and model files stay untracked (see `.gitignore`).
- Before PRs: `ruff check .`, `black --check .`, `isort --check-only .`, and
  `pytest -m "not requires_model"` must be green locally.
- Scratch/proposal docs go in `plan/` (one markdown per plan), never at root.
