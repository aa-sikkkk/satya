#!/usr/bin/env python3
# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Answer-quality evaluation harness for Satya (offline, local, model-gated).

Measures retrieval + generation quality on curated NEB-style questions with a
key-term rubric, so prompt/retrieval changes are judged by numbers, not vibes.

Usage (requires the Phi-1.5 GGUF in satya_data/models/phi15/ and local KB):
    python scripts/eval/eval_answer_quality.py                # all subjects
    python scripts/eval/eval_answer_quality.py --subject science --grade 9
    python scripts/eval/eval_answer_quality.py --json out.json

No network: the harness never downloads anything.
"""

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SUBJECT_KEY = "science"
GRADE_KEY = "9"

# Curated question set: (subject, grade, question, required_key_terms).
# Key terms = words an expert reader expects in a correct, specific answer.
QUESTIONS = [
    (
        "science",
        "9",
        "What is a cell and what are its main parts?",
        ["cell", "nucleus", "membrane", "cytoplasm"],
    ),
    (
        "science",
        "9",
        "Define photosynthesis.",
        ["photosynthesis", "light", "chlorophyll", "oxygen"],
    ),
    (
        "science",
        "9",
        "Explain the process of respiration in cells.",
        ["respiration", "glucose", "oxygen", "energy"],
    ),
    (
        "science",
        "10",
        "What is a food chain?",
        ["food chain", "producer", "consumer", "energy"],
    ),
    (
        "science",
        "10",
        "What is a digital circuit?",
        ["digital", "circuit", "signal", "logic"],
    ),
    (
        "mathematics",
        "10",
        "What is a quadratic equation?",
        ["quadratic", "equation", "roots", "degree"],
    ),
    (
        "mathematics",
        "10",
        "Explain what a rational number is.",
        ["rational", "fraction", "integer", "ratio"],
    ),
    ("computer science", "10", "What is a binary number?", ["binary", "bit", "1", "0"]),
    (
        "computer science",
        "10",
        "What is an algorithm?",
        ["algorithm", "steps", "problem", "instruction"],
    ),
]


def term_flags(answer: str, key_terms) -> dict:
    lowered = answer.lower()
    flags = {term: float(term in lowered) for term in key_terms}
    return flags


def band_ltob(value: float) -> str:
    """Marks coverage band for a quick console table."""
    if value >= 0.75:
        return "high"
    if value >= 0.45:
        return "mid"
    return "low"


def run(question_filter=None):
    from system.rag.rag_retrieval_engine import RAGRetrievalEngine

    engine = RAGRetrievalEngine()
    rows = []
    for subject, grade, question, key_terms in QUESTIONS:
        if question_filter and (subject, grade) != tuple(question_filter):
            continue
        start = time.time()
        result = engine.query(question, subject=subject, grade=grade)
        answer = result.get("answer", "")
        flags = term_flags(answer, key_terms)
        coverage = sum(flags.values()) / len(key_terms)
        rows.append(
            {
                "subject": subject,
                "grade": grade,
                "question": question,
                "term_coverage": round(coverage, 3),
                "band": band_ltob(coverage),
                "confidence": round(float(result.get("confidence", 0.0)), 3),
                "sources": len(result.get("sources", [])),
                "latency_s": round(time.time() - start, 2),
                "terms": flags,
                "answer_len_words": len(answer.split()),
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", help="Subject filter, e.g. science")
    parser.add_argument("--grade", help="Grade filter, e.g. 9")
    parser.add_argument("--json", dest="json_out", help="Write JSON report to path")
    args = parser.parse_args()

    rows = run((args.subject, args.grade) if args.subject or args.grade else None)
    if not rows:
        print("No questions matched the filter / model not available.")
        return
    print(
        f"\n{'subject':<18}{'grade':<6}{'coverage':<10}{'band':<6}{'conf':<6}{'sec':<7}"
    )
    for r in rows:
        print(
            f"{r['subject']:<18}{r['grade']:<6}{r['term_coverage']:<10.2f}"
            f"{r['band']:<6}{r['confidence']:<6.2f}{r['latency_s']:<7}"
        )
    avg = sum(r["term_coverage"] for r in rows) / len(rows)
    print(f"\nmean key-term coverage: {avg:.2f} over {len(rows)} questions")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"report written to {args.json_out}")


if __name__ == "__main__":
    main()
