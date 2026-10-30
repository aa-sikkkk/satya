# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
CI-safe unit tests for RAGRetrievalEngine.

No models, no ChromaDB data, no network: every heavy dependency is faked
(embedder, LLM facade, Chroma client). The engine's orchestration logic
(grade-aware collection selection, cache integration, LLM facade use,
normalizer opt-in policy) is what's under test.
"""

import numpy as np
import pytest

import system.rag.rag_retrieval_engine as rag_engine_module
from system.rag.rag_retrieval_engine import RAGRetrievalEngine

EMB_DIM = 8


class FakeEmbedder:
    def __init__(self, *args, **kwargs):
        pass

    def generate_embedding(self, text, *args, **kwargs):
        return np.zeros(EMB_DIM, dtype=np.float32)

    def generate_embeddings(self, texts, *args, **kwargs):
        if isinstance(texts, str):
            return np.zeros(EMB_DIM, dtype=np.float32)
        return np.zeros((len(texts), EMB_DIM), dtype=np.float32)


class FakeChromaCollection:
    def __init__(self, name):
        self.name = name
        self.queried = 0

    def query(self, query_embeddings=None, n_results=2, **kwargs):
        self.queried += 1
        return {
            "documents": [[f"{self.name} explains the topic with sufficient detail"]],
            "metadatas": [[{"source": self.name, "type": "neb_curriculum"}]],
            "distances": [[0.2]],
        }


class FakeChromaClient:
    def __init__(self, names):
        self._colls = {name: FakeChromaCollection(name) for name in names}

    def list_collections(self):
        return list(self._colls.values())

    def get_collection(self, name):
        return self._colls[name]


class FakeLLM:
    """Stands in for ModelHandler: the unified facade the engine must use."""

    def __init__(self):
        self.mode_calls = []
        self.received_context = None

    def get_answer(self, question, context=""):
        self.mode_calls.append("non_stream")
        self.received_context = context
        return f"Non-stream answer to: {question}", 0.7

    def get_answer_stream(self, question, context="", **kwargs):
        self.mode_calls.append("stream")
        self.received_context = context
        for word in f"Stream answer to: {question}".split():
            yield word + " "


class RecordingNormalizer(rag_engine_module.AdaptiveNormalizer):
    """Captures constructor kwargs to assert caller behavior."""

    last_kwargs = {}

    def __init__(self, **kwargs):
        RecordingNormalizer.last_kwargs = kwargs
        super().__init__(**kwargs)


@pytest.fixture
def make_engine(monkeypatch, tmp_path):
    """Builds an engine with all heavy deps faked out."""

    def _make(collection_names, llm=None):
        monkeypatch.setattr(rag_engine_module, "EmbeddingGenerator", FakeEmbedder)
        monkeypatch.setattr(
            rag_engine_module, "AdaptiveNormalizer", RecordingNormalizer
        )
        engine = RAGRetrievalEngine(
            chroma_db_path=str(tmp_path / "fake_chroma"),
            llm_handler=llm or FakeLLM(),
        )
        engine.chroma_client = FakeChromaClient(collection_names)
        return engine

    return _make


class TestNormalizerPolicy:
    def test_spell_check_not_forced_on(self, make_engine):
        """Regression guard: 2.3.0 made spell-check opt-in; the engine must
        not force-enable it again (LanguageTool spawns network processes)."""
        make_engine(["cs_stanford"])
        assert "enable_spell_check" not in RecordingNormalizer.last_kwargs
        assert not RecordingNormalizer.last_kwargs.get("enable_spell_check")


class TestGradeAwareCollectionSelection:
    def test_exact_grade_collection_preferred(self, make_engine):
        engine = make_engine(
            ["neb_science_grade_9", "neb_science_grade_10", "openstax_science"]
        )
        selected = engine._get_relevant_collections("Science", "Grade 9")
        assert selected[0] == "neb_science_grade_9"
        assert "neb_science_grade_10" not in selected

    def test_numeric_grade_normalized(self, make_engine):
        engine = make_engine(["neb_math_grade_10", "openstax_science"])
        selected = engine._get_relevant_collections("Mathematics", 10)
        assert "neb_math_grade_10" in selected

    def test_no_grade_falls_back_to_subject_level(self, make_engine):
        engine = make_engine(
            ["neb_science_grade_9", "neb_science_grade_10", "openstax_science"]
        )
        selected = engine._get_relevant_collections("Science", "")
        assert "neb_science_grade_9" in selected
        assert "neb_science_grade_10" in selected

    def test_subject_spaces_canonicalized(self, make_engine):
        engine = make_engine(["neb_computer_science_grade_10", "cs_stanford"])
        selected = engine._get_relevant_collections("Computer Science", "10")
        assert "neb_computer_science_grade_10" in selected
        assert "cs_stanford" in selected

    def test_unknown_subject_uses_general_fallback(self, make_engine):
        engine = make_engine(["khanacademy_pedagogy", "fineweb_edu"])
        selected = engine._get_relevant_collections("Unknown Subject", "")
        assert len(selected) >= 1


class TestQueryWiring:
    def test_streaming_uses_llm_facade(self, make_engine):
        llm = FakeLLM()
        engine = make_engine(["cs_stanford"], llm=llm)
        tokens = []
        result = engine.query(
            "What is a cell?",
            subject="Science",
            grade="9",
            stream_callback=tokens.append,
        )
        assert llm.mode_calls == ["stream"]
        assert result["answer"].startswith("Stream answer")
        assert "Stream answer" in "".join(tokens)

    def test_non_streaming_uses_llm_facade(self, make_engine):
        llm = FakeLLM()
        engine = make_engine(["cs_stanford"], llm=llm)
        result = engine.query("What is a cell?", subject="Science")
        assert llm.mode_calls == ["non_stream"]
        assert result["answer"].startswith("Non-stream answer")

    def test_grade_reaches_collection_queries_and_cache(self, make_engine):
        llm = FakeLLM()
        engine = make_engine(
            ["neb_science_grade_9", "neb_science_grade_10", "openstax_science"],
            llm=llm,
        )
        result = engine.query("What is a cell?", subject="Science", grade="Grade 9")
        queried = {
            name
            for name, coll in engine.chroma_client._colls.items()
            if coll.queried > 0
        }
        assert "neb_science_grade_9" in queried
        assert "neb_science_grade_10" not in queried
        # Cache entry tagged with the grade that was asked
        cached = engine.cache.get("What is a cell?", "Science", "Grade 9")
        assert cached is not None and cached["answer"]
        assert result["processing_time"] >= 0

    def test_second_identical_query_hits_cache(self, make_engine):
        llm = FakeLLM()
        engine = make_engine(["cs_stanford"], llm=llm)
        result1 = engine.query(
            "What is a cell?",
            subject="Science",
            grade="9",
            stream_callback=lambda t: None,
        )
        result2 = engine.query("What is a cell?", subject="Science", grade="9")
        assert llm.mode_calls == ["stream"]  # second call never reached the LLM
        assert result1["answer"] == result2["answer"]
