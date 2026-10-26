# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""Flatten tracked curriculum JSON into deterministic vectordb items.

Pure logic (no chroma/embedding imports) so it is unit-testable and
reusable by both the release pipeline and ``ingest_content.py``.

Item identity is a content hash of subject/grade/topic path + concept
name, which makes re-ingestion idempotent: rebuilt ingests or re-run
builds replace stale chunks instead of duplicating them.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Iterator, List


class ContentValidationError(ValueError):
    """Raised when a tracked content file violates the expected shape."""


def _require(cond: bool, message: str) -> None:
    if not cond:
        raise ContentValidationError(message)


def flattener_item_id(subject: str, grade: str, path: List[str]) -> str:
    """Stable content id for a concept (replace safety across revisions)."""
    key = "|".join([subject, grade, *path])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def _walk_concepts(
    node: Dict, subject: str, grade: str, path: List[str]
) -> Iterator[Dict]:
    name = node.get("name")
    _require(isinstance(name, str) and name.strip(), f"node missing name: {path!r}")

    child_path = path + [name]

    concepts = node.get("concepts")
    if concepts is not None:
        _require(
            isinstance(concepts, list),
            f"concepts not a list: {path!r}",
        )
    if isinstance(concepts, list):
        for concept in concepts:
            _require(isinstance(concept, dict), f"concept not object: {child_path!r}")
            cname = concept.get("name")
            _require(
                isinstance(cname, str) and cname.strip(),
                f"concept missing name: {child_path!r}",
            )
            parts = []
            summary = concept.get("summary", "")
            _require(isinstance(summary, str), f"summary not string: {child_path!r}")
            if summary.strip():
                parts.append(summary.strip())
            for step in _validated_steps(concept, child_path):
                parts.append(f"- {step.strip()}")
            text = "\n".join(parts)
            full_path = child_path + [cname]
            _require(text.strip(), f"empty concept (no summary/steps): {full_path!r}")
            yield {
                "id": flattener_item_id(subject, grade, full_path),
                "text": text,
                "collection": f"neb_{subject.lower().replace(' ', '_')}_grade_{grade}",
                "metadata": {
                    "subject": subject,
                    "grade": grade,
                    "topic": child_path[0] if child_path else "",
                    "concept": cname,
                    "source_path": "/".join(full_path),
                    "type": "neb_curriculum",
                },
            }

    subtopics = node.get("subtopics")
    if subtopics is not None:
        _require(
            isinstance(subtopics, list),
            f"subtopics not a list: {path!r}",
        )
    if isinstance(subtopics, list):
        for sub in subtopics:
            yield from _walk_concepts(sub, subject, grade, child_path)


def _validated_steps(concept: Dict, path: List[str]) -> List[str]:
    """steps key, when present, must be a list of nonempty strings."""
    steps = concept.get("steps", [])
    _require(
        isinstance(steps, list),
        f"steps not a list: {path!r}",
    )
    for step in steps:
        _require(
            isinstance(step, str) and step.strip(),
            f"step not string: {path!r}",
        )
    return steps


def flatten_content_json(payload: Dict, source_name: str = "<memory>") -> List[Dict]:
    """Convert one parsed content file into deterministic study chunks."""
    subject = payload.get("subject")
    _require(
        isinstance(subject, str) and subject.strip(),
        f"{source_name}: missing top-level subject",
    )
    grade = payload.get("grade")
    _require(grade is not None, f"{source_name}: missing top-level grade")
    _require(
        isinstance(grade, int) and not isinstance(grade, bool),
        f"{source_name}: grade not an integer: {grade!r}",
    )
    _require(
        8 <= grade <= 12,
        f"{source_name}: grade outside NEB range 8-12: {grade!r}",
    )
    grade_str = str(grade)

    topics = payload.get("topics")
    _require(isinstance(topics, list), f"{source_name}: topics not a list")

    items: List[Dict] = []
    for topic in topics:
        _require(isinstance(topic, dict), f"{source_name}: topic not object: {topic!r}")
        items.extend(_walk_concepts(topic, subject, grade_str, []))

    _require(bool(items), f"{source_name}: produced no concept chunks")
    return items


def flatten_content_file(path: Path) -> List[Dict]:
    """Flatten a tracked .json curriculum file."""
    with open(Path(path), "r", encoding="utf-8") as f:
        try:
            payload = json.load(f)
        except json.JSONDecodeError as e:
            raise ContentValidationError(f"{path}: invalid JSON - {e}") from e
    return flatten_content_json(payload, str(Path(path).name))
