# Copyright (C) 2026 Aashik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Production-Accurate End-to-End Benchmarks for Satya Learning System

Measures real-world performance with cold start initialization.
"""

import pytest
import time
import psutil
import os
import gc
from pathlib import Path
from typing import Dict, List
import numpy as np

from system.rag.rag_retrieval_engine import RAGRetrievalEngine
from ai_model.model_utils.model_handler import ModelHandler


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / (1024 * 1024)


class ProductionBenchmark:
    """Container for benchmark results with statistical analysis."""
    
    def __init__(self):
        self.ttft_times: List[float] = []
        self.full_response_times: List[float] = []
        self.total_pipeline_times: List[float] = []
        self.memory_usage: List[float] = []
        self.token_counts: List[int] = []
    
    def add_measurement(
        self,
        ttft: float,
        full_response: float,
        total_time: float,
        memory: float,
        tokens: int
    ):
        self.ttft_times.append(ttft)
        self.full_response_times.append(full_response)
        self.total_pipeline_times.append(total_time)
        self.memory_usage.append(memory)
        self.token_counts.append(tokens)
    
    def get_summary(self) -> Dict:
        """Calculate mean, std, min, max for all metrics."""
        def stats(data):
            if not data:
                return {"mean": 0, "std": 0, "min": 0, "max": 0}
            return {
                "mean": float(np.mean(data)),
                "std": float(np.std(data)),
                "min": float(np.min(data)),
                "max": float(np.max(data))
            }
        
        return {
            "ttft": stats(self.ttft_times),
            "full_response": stats(self.full_response_times),
            "total_pipeline": stats(self.total_pipeline_times),
            "memory_mb": stats(self.memory_usage),
            "tokens": stats(self.token_counts)
        }


@pytest.fixture(scope="session")
def model_path():
    base = Path(__file__).resolve().parents[1]
    path = base / "satya_data" / "models" / "phi15"
    if not path.exists():
        pytest.skip("Model path missing; skipping benchmarks.")
    return str(path)


@pytest.fixture(scope="session")
def chroma_path():
    base = Path(__file__).resolve().parents[1]
    path = base / "satya_data" / "chroma_db"
    if not path.exists():
        pytest.skip("ChromaDB missing; skipping benchmarks.")
    return str(path)


@pytest.fixture
def cold_start_rag(model_path, chroma_path):
    """Create fresh RAG engine instance with cold start."""
    gc.collect()
    
    model_handler = ModelHandler(model_path)
    rag_engine = RAGRetrievalEngine(
        chroma_db_path=chroma_path,
        llm_handler=model_handler
    )
    
    yield rag_engine
    
    model_handler.cleanup()


def test_cold_start_initialization(model_path, chroma_path):
    """Benchmark cold start initialization time including model and RAG warm-up."""
    gc.collect()
    initial_memory = get_memory_usage()
    
    print(f"\n=== COLD START INITIALIZATION (Production Flow) ===")
    
    start_time = time.time()
    
    model_start = time.time()
    model_handler = ModelHandler(model_path)
    model_time = time.time() - model_start
    print(f"Model Handler (with warm-up): {model_time:.2f}s")
    
    rag_start = time.time()
    rag_engine = RAGRetrievalEngine(
        chroma_db_path=chroma_path,
        llm_handler=model_handler
    )
    rag_init_time = time.time() - rag_start
    print(f"RAG Engine (init): {rag_init_time:.2f}s")
    
    warmup_start = time.time()
    rag_engine.warm_up()
    warmup_time = time.time() - warmup_start
    print(f"RAG Engine (warm-up): {warmup_time:.2f}s")
    
    total_time = time.time() - start_time
    final_memory = get_memory_usage()
    
    print(f"\nTotal initialization: {total_time:.2f}s")
    print(f"Memory usage: {final_memory - initial_memory:.2f} MB")
    
    model_handler.cleanup()
    
    # Updated expectations with both warm-ups
    assert total_time < 45.0, f"Init took {total_time:.2f}s (should be < 45s with warm-ups)"
    assert final_memory - initial_memory < 2000, "Memory usage too high"


def test_production_pipeline_single_query(cold_start_rag):
    """
    Benchmark complete production pipeline for a single query.
    
    TTFT = Time from query start to first answer token (skipping progress messages).
    """
    rag_engine = cold_start_rag
    
    question = "What is photosynthesis and how does it work in plants?"
    subject = "Science"
    
    print(f"\n=== PRODUCTION PIPELINE BENCHMARK ===")
    print(f"Query: {question}")
    print(f"Subject: {subject}")
    
    pipeline_start = time.time()
    initial_memory = get_memory_usage()
    
    first_token_time = None
    token_count = 0
    tokens_received = []
    answer_started = False
    
    def on_token(token):
        nonlocal first_token_time, token_count, answer_started
        
        # Skip progress messages to measure actual TTFT
        if not answer_started and any(emoji in token for emoji in ['✨', '🔍', '📊', '🎯']):
            return
        
        if first_token_time is None:
            first_token_time = time.time() - pipeline_start
            answer_started = True
        
        token_count += 1
        tokens_received.append(token)
    
    response = rag_engine.query(
        query_text=question,
        subject=subject,
        stream_callback=on_token
    )
    
    total_time = time.time() - pipeline_start
    final_memory = get_memory_usage()
    
    confidence = response.get('confidence', 0.5)
    answer_length = len(''.join(tokens_received))
    
    print(f"\n=== RESULTS ===")
    print(f"TTFT (Time To First Token): {first_token_time:.2f}s")
    print(f"  ^ Includes: normalization + RAG retrieval + model loading + first token")
    print(f"Total Pipeline Time: {total_time:.2f}s")
    print(f"Tokens streamed: {token_count}")
    print(f"Answer length: {answer_length} chars")
    print(f"Confidence: {confidence:.2f}")
    print(f"Memory used: {final_memory - initial_memory:.2f} MB")
    
    assert first_token_time < 15.0, f"TTFT too slow: {first_token_time:.2f}s"
    assert total_time < 30.0, f"Total pipeline too slow: {total_time:.2f}s"
    assert token_count > 0, "No tokens received"


def test_production_pipeline_multiple_queries(cold_start_rag):
    """Benchmark pipeline consistency across multiple queries."""
    rag_engine = cold_start_rag
    benchmark = ProductionBenchmark()
    
    test_queries = [
        ("What is a computer?", "Computer Science"),
        ("Explain photosynthesis", "Science"),
        ("What is an algorithm?", "Mathematics"),
        ("Define binary number", "Computer Science"),
        ("How does DNA replication work?", "Science"),
    ]
    
    print(f"\n=== MULTIPLE QUERY BENCHMARK (Production Flow) ===")
    print(f"Testing {len(test_queries)} queries...")
    
    for i, (query, subject) in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] {query} ({subject})")
        
        pipeline_start = time.time()
        initial_memory = get_memory_usage()
        
        first_token_time = None
        token_count = 0
        
        def on_token(token):
            nonlocal first_token_time, token_count
            if first_token_time is None:
                first_token_time = time.time() - pipeline_start
            token_count += 1
        
        response = rag_engine.query(
            query_text=query,
            subject=subject,
            stream_callback=on_token
        )
        
        total_time = time.time() - pipeline_start
        final_memory = get_memory_usage()
        
        benchmark.add_measurement(
            first_token_time if first_token_time else 0,
            total_time,
            total_time,
            final_memory - initial_memory,
            token_count
        )
        
        print(f"  TTFT: {first_token_time*1000:.0f}ms | Total: {total_time:.1f}s | Tokens: {token_count}")
    
    summary = benchmark.get_summary()
    
    print(f"\n=== PERFORMANCE SUMMARY ===")
    print(f"TTFT:             {summary['ttft']['mean']*1000:.0f}ms "
          f"(±{summary['ttft']['std']*1000:.0f}ms)")
    print(f"Total Pipeline:   {summary['total_pipeline']['mean']:.2f}s "
          f"(±{summary['total_pipeline']['std']:.2f}s)")
    print(f"Tokens per query: {summary['tokens']['mean']:.0f} "
          f"(±{summary['tokens']['std']:.0f})")
    print(f"Memory per query: {summary['memory_mb']['mean']:.0f} MB "
          f"(±{summary['memory_mb']['std']:.0f} MB)")
    
    assert summary['ttft']['mean'] < 15.0, "TTFT too slow on average"
    assert summary['total_pipeline']['mean'] < 30.0, "Pipeline too slow on average"


def test_cache_performance(cold_start_rag):
    """Test cache speedup on repeated queries."""
    rag_engine = cold_start_rag
    
    query = "What is photosynthesis?"
    subject = "Science"
    
    print(f"\n=== CACHE PERFORMANCE TEST (Production) ===")
    
    first_token_time_cold = None
    
    def on_token_cold(token):
        nonlocal first_token_time_cold
        if first_token_time_cold is None:
            first_token_time_cold = time.time()
    
    start = time.time()
    response1 = rag_engine.query(query, subject=subject, stream_callback=on_token_cold)
    first_time = time.time() - start
    
    print(f"First query (cold):  {first_time:.2f}s")
    
    first_token_time_warm = None
    
    def on_token_warm(token):
        nonlocal first_token_time_warm
        if first_token_time_warm is None:
            first_token_time_warm = time.time()
    
    start = time.time()
    response2 = rag_engine.query(query, subject=subject, stream_callback=on_token_warm)
    second_time = time.time() - start
    
    print(f"Second query (warm): {second_time:.2f}s")
    
    speedup = first_time / second_time if second_time > 0 else 1.0
    print(f"Speedup: {speedup:.1f}x")
    
    assert second_time <= first_time, "Cache should not slow down queries"
    assert speedup >= 1.0, "Cache should provide at least 1x speedup"


def test_memory_stability(cold_start_rag):
    """Test for memory leaks over sustained load."""
    rag_engine = cold_start_rag
    
    query = "Explain this concept"
    subject = "Science"
    
    print(f"\n=== MEMORY STABILITY TEST (Production) ===")
    
    memory_readings = []
    
    for i in range(10):
        initial_memory = get_memory_usage()
        response = rag_engine.query(query, subject=subject)
        final_memory = get_memory_usage()
        memory_delta = final_memory - initial_memory
        memory_readings.append(final_memory)
        
        if i % 3 == 0:
            print(f"Iteration {i+1}: {final_memory:.0f} MB (Δ{memory_delta:+.0f} MB)")
    
    first_half_avg = np.mean(memory_readings[:5])
    second_half_avg = np.mean(memory_readings[5:])
    memory_growth = second_half_avg - first_half_avg
    
    print(f"\nMemory growth: {memory_growth:+.0f} MB")
    
    assert memory_growth < 200, f"Possible memory leak: {memory_growth:.0f} MB growth"


def test_subject_specific_performance(cold_start_rag):
    """Test performance across different subjects."""
    rag_engine = cold_start_rag
    
    subjects = {
        "Computer Science": "What is a binary number?",
        "Science": "What is photosynthesis?",
        "Mathematics": "What is an algorithm?"
    }
    
    print(f"\n=== SUBJECT-SPECIFIC PERFORMANCE ===")
    
    for subject, query in subjects.items():
        first_token_time = None
        
        def on_token(token):
            nonlocal first_token_time
            if first_token_time is None:
                first_token_time = time.time()
        
        start = time.time()
        response = rag_engine.query(query, subject=subject, stream_callback=on_token)
        total_time = time.time() - start
        
        print(f"{subject:20s} - TTFT: {(first_token_time-start)*1000:.0f}ms, Total: {total_time:.2f}s")
        
        assert total_time < 30.0, f"{subject} too slow: {total_time:.2f}s"