<!--
Checklist per docs/PROJECT_STANDARDS.md. Remove lines that don't apply.
-->
## Summary
<!-- What does this PR do, and why? -->

## Type of change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Content pipeline
- [ ] Refactor (no behavior change)
- [ ] CI / tooling

## Checklist
- [ ] Keeps the offline-first constraint: no new network calls at runtime
- [ ] Assumes 4GB-RAM / CPU-only target hardware (no heavier inference path)
- [ ] Type hints + Google-style docstrings on touched public functions
- [ ] Tests included (`pytest`) — model-dependent tests marked `@pytest.mark.requires_model`
- [ ] `ruff check .` and `black --check .` pass locally
- [ ] Works with `requirements.txt` only; optional deps degrade gracefully
- [ ] `CHANGELOG.md` updated (or state why not needed)
- [ ] Docs updated if behavior/contracts changed

## Verification
<!-- How was this tested? Include commands and results. -->
