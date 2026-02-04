# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
Lightweight RAG Retrieval Engine for Satya Learning System
"""

import logging
import time
from typing import Dict, List, Any
import chromadb
from concurrent.futures import ThreadPoolExecutor, as_completed

from system.rag.anti_confusion_engine import AntiConfusionEngine
from system.rag.ascii_diagram_library import ASCIIDiagramLibrary
from system.rag.user_edge_case_handler import UserEdgeCaseHandler
from system.rag.rag_cache import RAGCache
from system.input_processing.adaptive_normalizer import AdaptiveNormalizer
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator
from ai_model.model_utils.model_handler import ModelHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGRetrievalEngine:
    """RAG orchestrator for Satya."""

    def __init__(
        self,
        chroma_db_path: str = "satya_data/chroma_db",
        model_path: str = "satya_data/models/phi15",
        llm_handler=None
    ):
        logger.info("Initializing Satya RAG Engine...")

        self.chroma_db_path = chroma_db_path
        self.edge_case_handler = UserEdgeCaseHandler()
        self.anti_confusion = AntiConfusionEngine()
        self.diagram_library = ASCIIDiagramLibrary()
        self.cache = RAGCache(max_size=100, ttl_seconds=3600)
        self.input_normalizer = AdaptiveNormalizer(enable_spell_check=True)
        self.embedding_gen = EmbeddingGenerator(device='cpu')

        # ChromaDB init
        try:
            self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
            logger.info(f"ChromaDB connected at {chroma_db_path}")
        except Exception as e:
            logger.error(f"ChromaDB connection failed: {e}")
            self.chroma_client = None

        # LLM init
        if llm_handler:
            self.llm = llm_handler
            logger.info("LLM Model connected (pre-loaded)")
        else:
            try:
                self.llm = ModelHandler(model_path=model_path)
                logger.info("LLM Model connected")
            except Exception as e:
                logger.error(f"LLM connection failed: {e}")
                self.llm = None
        
        logger.info("RAG Engine initialized")
    
    def warm_up(self):
        """
        Warms up RAG engine by pre-loading embedding generator and ChromaDB.
        This reduces first query latency.
        """
        logger.info("Warming up RAG engine...")
        try:
            # Warms up embedding generator with dummy query
            dummy_query = "test query"
            self.embedding_gen.generate_embedding(dummy_query)
            
            # Warms up ChromaDB by accessing a collection
            if self.chroma_client:
                collections = self.chroma_client.list_collections()
                if collections:
                    # Queries first collection with dummy to load indexes
                    test_coll = self.chroma_client.get_collection(collections[0].name)
                    test_embedding = self.embedding_gen.generate_embedding(dummy_query)
                    test_coll.query(
                        query_embeddings=[test_embedding],
                        n_results=1
                    )
            
            logger.info("RAG engine warmed up!")
        except Exception as e:
            logger.warning(f"RAG warm-up failed (non-critical): {e}")

    def _get_relevant_collections(self, subject: str, grade: str) -> List[str]:
        """
        Selects relevant collections based on subject and grade.
        
        Strategy:
        1. NEB collections: Filter by BOTH subject AND grade
        2. HuggingFace collections: Filter by SUBJECT ONLY (ignore grade)
        
        Returns max 3 collections for performance.
        """
        if not self.chroma_client:
            return []

        all_colls = [c.name for c in self.chroma_client.list_collections()]
        collections = []
        
        # 1. NEB Collections (grade-specific)
        # Format: neb_{subject}_grade_{grade}
        neb_key = f"neb_{subject.lower()}_grade_{grade}"
        for name in all_colls:
            if neb_key in name.lower():
                collections.append(name)
                logger.info(f"Selected NEB collection (grade {grade}): {name}")
        
        # 2. HuggingFace Collections (subject-based, all grades)
        # Maps subjects to appropriate general knowledge collections
        subject_map = {
            "biology": ["openstax_science", "scienceqa"],
            "physics": ["openstax_science", "scienceqa"],
            "chemistry": ["openstax_science", "scienceqa"],
            "science": ["openstax_science", "scienceqa"],
            
            "mathematics": ["finemath", "gsm8k"],
            "math": ["finemath", "gsm8k"],
            
            "computer": ["cs_stanford"],
            "computer science": ["cs_stanford"],
            "cs": ["cs_stanford"],
            
            "english": ["fineweb_edu", "khanacademy_pedagogy"],
            "grammar": ["fineweb_edu"],
            "writing": ["fineweb_edu"],
        }
        
        # Adds HuggingFace collections for this subject (ignore grade)
        subject_lower = subject.lower()
        if subject_lower in subject_map:
            for target in subject_map[subject_lower]:
                if target in all_colls and target not in collections:
                    collections.append(target)
                    logger.info(f"Selected HuggingFace collection (all grades): {target}")
                    if len(collections) >= 3:  # Max 3 collections for performance
                        break
        
        # 3. Fallback: General education collections
        if not collections:
            fallback = ["khanacademy_pedagogy", "fineweb_edu"]
            for fb in fallback:
                if fb in all_colls:
                    collections.append(fb)
                    logger.info(f"Selected fallback collection: {fb}")
                    if len(collections) >= 2:
                        break
        
        logger.info(f"Total collections selected: {len(collections)}")
        return collections[:3]  

    def query(
        self,
        query_text: str,
        subject: str,
        n_results: int = 3,
        stream_callback=None 
    ) -> Dict[str, Any]:
        """Main query method, with streaming support."""
        start_time = time.time()

        # Edge case check
        edge_response = self.edge_case_handler.check_edge_cases(query_text)
        if edge_response:
            if stream_callback:
                stream_callback(edge_response)
            return {
                "answer": edge_response,
                "sources": [],
                "processing_time": time.time() - start_time,
                "type": "edge_case"
            }

        if not self.chroma_client:
            error_msg = "Error: Database not connected."
            if stream_callback:
                stream_callback(error_msg)
            return {"answer": error_msg, "type": "error"}
        
        normalization_result = self.input_normalizer.normalize(query_text)
        clean_question = normalization_result["clean_question"]
        
        if normalization_result["notes"]:
            logger.info(f"Normalization applied: {normalization_result['notes']}")
            logger.info(f"Intent: {normalization_result['intent']}, Confidence: {normalization_result['confidence']:.2f}")
        
        effective_query = clean_question if clean_question else query_text

        cached_result = self.cache.get(query_text, subject, "")
        if cached_result:
            logger.info(f"Cache HIT (exact)")
            if stream_callback:
                # Streams cached answer word by word for smooth UX
                answer = cached_result.get("answer", "")
                words = answer.split()
                for i, word in enumerate(words):
                    stream_callback(word + (" " if i < len(words) - 1 else ""))
            return {**cached_result, "processing_time": time.time() - start_time}

        if stream_callback:
            stream_callback("🔍 Searching knowledge base...\n\n")

        if stream_callback:
            stream_callback("📊 Analyzing your question...\n\n")
        
        query_embedding = self.embedding_gen.generate_embeddings(effective_query)

        semantic_hit = self.cache.find_similar(query_embedding, subject, "", threshold=0.88)
        if semantic_hit:
            logger.info(f"Cache HIT (semantic)")
            if stream_callback:
                answer = semantic_hit.get("answer", "")
                words = answer.split()
                for i, word in enumerate(words):
                    stream_callback(word + (" " if i < len(words) - 1 else ""))
            return {**semantic_hit, "processing_time": time.time() - start_time}

        target_collections = self._get_relevant_collections(subject, "")
        if not target_collections:
            logger.warning(f"No collections found for {subject}")
        
        if stream_callback:
            stream_callback("🎯 Finding best matches...\n\n")

        raw_results = []
        
        def query_collection(coll_name):
            try:
                coll = self.chroma_client.get_collection(coll_name)
                res = coll.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=min(2, n_results)  
                )
                results = []
                if res['documents']:
                    for i in range(len(res['documents'][0])):
                        results.append({
                            'text': res['documents'][0][i],
                            'metadata': res['metadatas'][0][i],
                            'score': 1.0 - res['distances'][0][i],
                            'collection': coll_name
                        })
                return results
            except Exception as e:
                logger.error(f"Error querying {coll_name}: {e}")
                return []

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(query_collection, name) for name in target_collections]
            for future in as_completed(futures):
                raw_results.extend(future.result())

        ranked_chunks = self.anti_confusion.rank_results(raw_results, query_text)
        final_context_chunks = []
        current_len = 0
        limit = 400
        
        for chunk in ranked_chunks:
            if chunk['final_score'] < 0.35:
                continue
            text = chunk['text']
            if current_len + len(text) < limit:
                final_context_chunks.append(chunk)
                current_len += len(text)
            else:
                break

        ordered_chunks = self.anti_confusion.resolve_conflicts(final_context_chunks)
        context_texts = [c['text'] for c in ordered_chunks]
        full_context_str = "\n\n".join(context_texts)
 
        if stream_callback:
            stream_callback("✨ Generating answer...\n\n")

        answer = "Unable to generate answer."
        confidence = 0.0
        
        if self.llm:
            try:
                if stream_callback:
                    answer = ""
                    token_count = 0
                    for token in self.llm.handler.get_answer_stream(effective_query, full_context_str):
                        answer += token
                        stream_callback(token)  
                        token_count += 1                   
                    
                    confidence = self._calculate_confidence(answer, effective_query, final_context_chunks)
                else:
                    answer, confidence = self.llm.simple_handler.get_answer(effective_query, full_context_str)
            except Exception as e:
                logger.error(f"LLM generation error: {e}")
                if stream_callback:
                    stream_callback("Error generating answer.")

        diagram = self.diagram_library.find_diagram_by_text(query_text)

        result = {
            "answer": answer,
            "context_used": context_texts,
            "sources": [c['metadata'] for c in ordered_chunks],
            "diagram": diagram,
            "confidence": confidence,
            "processing_time": time.time() - start_time,
            "type": "rag_response"
        }

        self.cache.set(query_text, subject, "", result, embedding=query_embedding)

        return result
    
    def _calculate_confidence(self, answer: str, question: str, context_chunks: list = None) -> float:
        """
        Calculate confidence based on answer quality and RAG context.
        
        Factors:
        - Answer length and completeness
        - Relevance to question
        - Quality of RAG context used
        """
        if not answer or len(answer.split()) < 5:
            return 0.3
        
        confidence = 0.5  
        
        word_count = len(answer.split())
        if 50 <= word_count <= 150:
            confidence += 0.2  
        elif 30 <= word_count < 50 or 150 < word_count <= 200:
            confidence += 0.1 
        
        q_words = set(w.lower() for w in question.split() if len(w) > 3)
        a_words = set(w.lower() for w in answer.split())
        if q_words:
            relevance = len(q_words & a_words) / len(q_words)
            confidence += relevance * 0.2
        
        if context_chunks and len(context_chunks) > 0:
            avg_score = sum(c.get('final_score', 0.5) for c in context_chunks) / len(context_chunks)
            confidence += avg_score * 0.1
        
        return min(1.0, confidence)