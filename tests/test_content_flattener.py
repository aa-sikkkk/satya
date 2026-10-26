"""Deterministic curriculum flattener tests (pure logic, no chroma/model)."""

import json
from pathlib import Path

import pytest

from scripts.rag_data_preparation.content_flattener import (
    ContentValidationError,
    flatten_content_file,
    flatten_content_json,
    flattener_item_id,
)

STUDY = {
    "subject": "Science",
    "grade": 9,
    "topics": [
        {
            "name": "Motion",
            "subtopics": [
                {
                    "name": "Speed",
                    "concepts": [
                        {
                            "name": "Average speed",
                            "summary": "Total distance over total time.",
                            "steps": ["Divide distance by time."],
                        }
                    ],
                }
            ],
        }
    ],
}


def test_flatten_produces_deterministic_items():
    first = flatten_content_json(STUDY)
    second = flatten_content_json(STUDY)
    assert first == second
    assert len(first) == 1

    item = first[0]
    assert item["id"] == flattener_item_id(
        "Science", "9", ["Motion", "Speed", "Average speed"]
    )
    assert item["collection"] == "neb_science_grade_9"
    assert item["metadata"]["topic"] == "Motion"
    assert "Total distance over total time." in item["text"]
    assert "- Divide distance by time." in item["text"]


def test_revision_changes_id():
    revised = json.loads(json.dumps(STUDY))
    revised["topics"][0]["subtopics"][0]["concepts"][0]["summary"] = "changed"
    assert flattener_item_id("Science", "9", ["Motion", "Speed", "Average speed"]) != (
        flattener_item_id("Science", "9", ["Motion", "Speed", "OTHER"])
    )


def test_nested_topics_via_real_file():
    seed = (
        Path(__file__).parent.parent
        / "scripts/data_collection/data/content/English_Grammar.json"
    )
    items = flatten_content_file(seed)
    assert items, "tracked seed produced no chunks"
    assert all(i["collection"].startswith("neb_") for i in items)
    assert len({i["id"] for i in items}) == len(items), "ids must be unique"


def test_empty_concept_rejected():
    bad = {
        "subject": "x",
        "grade": 8,
        "topics": [{"name": "t", "concepts": [{"name": "c"}]}],
    }
    with pytest.raises(ContentValidationError):
        flatten_content_json(bad)


def test_missing_subject_rejected():
    with pytest.raises(ContentValidationError):
        flatten_content_json({"topics": []})


def test_bad_json_file_rejected(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(ContentValidationError):
        flatten_content_file(p)


def test_grade_must_be_numeric():
    bad = json.loads(json.dumps(STUDY))
    bad["grade"] = "nine"
    with pytest.raises(ContentValidationError):
        flatten_content_json(bad)


def test_grade_must_be_in_neb_range():
    for grade in (7, 13, "9", 9.5, True):
        changed = json.loads(json.dumps(STUDY))
        changed["grade"] = grade
        with pytest.raises(ContentValidationError):
            flatten_content_json(changed)


def test_steps_must_be_a_list_of_strings():
    changed = json.loads(json.dumps(STUDY))
    concept = changed["topics"][0]["subtopics"][0]["concepts"][0]
    concept["steps"] = "single string"
    with pytest.raises(ContentValidationError):
        flatten_content_json(changed)


def test_subtopics_must_be_a_list():
    changed = {
        "subject": "x",
        "grade": 9,
        "topics": [{"name": "t", "subtopics": "not-a-list"}],
    }
    with pytest.raises(ContentValidationError):
        flatten_content_json(changed)


def test_concepts_must_be_a_list():
    changed = {
        "subject": "x",
        "grade": 9,
        "topics": [{"name": "t", "concepts": "not-a-list"}],
    }
    with pytest.raises(ContentValidationError):
        flatten_content_json(changed)
