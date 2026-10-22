# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Pytest configuration: sys-path setup and test markers.

Markers (register any new one here):
- ``requires_model``: test needs GGUF/ChromaDB binaries from
  ``satya_data/models/`` (gitignored, downloaded one-time). CI runs
  ``pytest -m "not requires_model"``; local full runs need the model.
"""
import os
import sys

import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Tests must never attempt runtime network calls (offline-first):
# keep the optional LanguageTool spell checker off unless explicitly enabled
os.environ.setdefault("SATYA_SPELL_CHECK", "0")


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "requires_model: test requires downloaded model binaries (skipped in CI)",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Deselect ``requires_model`` tests when explicitly skipped via env var."""
    if not os.environ.get("SATYA_SKIP_HEAVY_TESTS"):
        return
    remaining = [item for item in items if "requires_model" not in item.keywords]
    deselected = [item for item in items if "requires_model" in item.keywords]
    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = remaining
