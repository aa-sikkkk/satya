"""
RAG Retrieval Engine for Satya Learning System

Simplified for performance on old hardware.
"""

import logging
import time
from typing import Dict, List, Optional, Any
import chromadb
from pathlib import Path

# Import components
from system.rag.anti_confusion_engine import AntiConfusionEngine
from system.rag.ascii_diagram_library import ASCIIDiagramLibrary
from system.rag.user_edge_case_handler import UserEdgeCaseHandler
from system.rag.rag_cache import RAGCache
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator
from ai_model.model_utils.model_handler import ModelHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGRetrievalEngine:
    """Main RAG orchestrator for Satya."""
    
    def __init__(
        self,
        chroma_db_path: str = "satya_data/chroma_db",
        model_path: str = "satya_data/models/phi15",
        llm_handler=None
    ):
        """Initialize the RAG Engine."""
        logger.info("Initializing Satya RAG Engine...")
        
        self.chroma_db_path = chroma_db_path
        
        # Sub-components
        self.edge_case_handler = UserEdgeCaseHandler()
        self.anti_confusion = AntiConfusionEngine()
        self.diagram_library = ASCIIDiagramLibrary()
        self.cache = RAGCache(max_size=100, ttl_seconds=3600)
        
        # Embedding model
        self.embedding_gen = EmbeddingGenerator(device='cpu')
        
        # ChromaDB
        try:
            self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
            logger.info(f"ChromaDB connected at {chroma_db_path}")
        except Exception as e:
            logger.error(f"ChromaDB connection failed: {e}")
            self.chroma_client = None

        # LLM
        if llm_handler:
            self.llm = llm_handler
            logger.info("LLM connected (reused)")
        else:
            try:
                self.llm = ModelHandler(model_path=model_path)
                logger.info("LLM connected")
            except Exception as e:
                logger.error(f"LLM connection failed: {e}")
                self.llm = None
        
        logger.info("RAG Engine initialized")

    def _get_relevant_collections(self, subject: str, grade: str) -> List[str]:
        """Determine which collections to query."""
        collections = []
        
        if not self.chroma_client:
            return []
            
        all_colls = [c.name for c in self.chroma_client.list_collections()]
        
        # 1. NEB Collections (exact match)
        neb_key = f"neb_{subject}_grade_{grade}"
        for name in all_colls:
            if neb_key in name:
                collections.append(name)
        
        # 2. Subject collections
        subject_map = {
            "science": ["openstax_science", "scienceqa"],
            "math": ["finemath", "gsm8k"],
            "computer": ["cs_stanford"],
            "english": ["fineweb_edu"]
        }
        
        if subject in subject_map:
            for target in subject_map[subject]:
                if target in all_colls and target not in collections:
                    collections.append(target)
                    if len(collections) >= 2:
                        break
                        
        # 3. Fallback
        if not collections:
            fallbacks = ["fineweb_edu", "khanacademy_pedagogy"]
            for fb in fallbacks:
                if fb in all_colls and fb not in collections:
                    collections.append(fb)
                    if len(collections) >= 2:
                        break
        
        return collections[:3]

    def query(
        self,
        query_text: str,
        subject: str,
        grade: str,
        n_results: int = 5,
        stream_callback=None  # Single callback for streaming
    ) -> Dict[str, Any]:
        """
        Main query entry point.
        Simplified - no phase1/phase2 callbacks, just one stream callback.
        """
        start_time = time.time()
        
        # Edge cases
        edge_response = self.edge_case_handler.check_edge_cases(query_text)
        if edge_response:
            return {
                "answer": edge_response,
                "sources": [],
                "processing_time": time.time() - start_time,
                "type": "edge_case"
            }
            
        if not self.chroma_client:
            return {
                "answer": "Error: Database not connected.",
                "type": "error"
            }

        # Cache check (exact)
        cached_result = self.cache.get(query_text, subject, grade)
        if cached_result:
            logger.info(f"Cache HIT (Exact)")
            if stream_callback:
                self._replay_cached_response(cached_result, stream_callback)
            results = cached_result
            results["processing_time"] = time.time() - start_time
            return results

        # Embedding
        t_embed = time.time()
        query_embedding = self.embedding_gen.generate_embeddings(query_text)
        logger.info(f"Embedding: {time.time() - t_embed:.3f}s")

        # Cache check (semantic)
        semantic_hit = self.cache.find_similar(query_embedding, subject, grade, threshold=0.92)
        if semantic_hit:
            logger.info(f"Cache HIT (Semantic)")
            if stream_callback:
                self._replay_cached_response(semantic_hit, stream_callback)
            results = semantic_hit
            results["processing_time"] = time.time() - start_time
            return results
        
        # Select collections
        target_collections = self._get_relevant_collections(subject, grade)
        if not target_collections:
            logger.warning(f"No collections for {subject} grade {grade}")

        raw_results = []
        
        # Query collections
        t_retrieve = time.time()
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def query_collection(coll_name):
            try:
                coll = self.chroma_client.get_collection(coll_name)
                res = coll.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=min(3, n_results) 
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

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_coll = {executor.submit(query_collection, name): name for name in target_collections}
            for future in as_completed(future_to_coll):
                raw_results.extend(future.result())
                
        logger.info(f"Retrieval: {time.time() - t_retrieve:.3f}s")

        # Ranking & filtering
        t_rank = time.time()
        ranked_chunks = self.anti_confusion.rank_results(raw_results, query_text)
        
        # Build context
        final_context_chunks = []
        current_len = 0
        limit = 600
        
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
        logger.info(f"Ranking: {time.time() - t_rank:.4f}s")
        
        if ordered_chunks:
            top_score = ordered_chunks[0].get('final_score', 0)
            logger.info(f"Top Score: {top_score:.2f}")
        
        context_texts = [c['text'] for c in ordered_chunks]
        full_context_str = "\n\n".join(context_texts)
        logger.info(f"Context: {len(full_context_str)} chars")
        
        # Generation
        answer = "I'm having trouble thinking right now."
        confidence = 0.0
        
        if self.llm:
            try:
                t_gen = time.time()
                
                if stream_callback:
                    # Stream answer
                    answer = ""
                    for token in self.llm.get_answer_stream(query_text, full_context_str):
                        answer += token
                        stream_callback(token)
                    
                    # Calculate confidence from answer
                    confidence = self._calculate_confidence(answer, full_context_str)
                else:
                    # Non-streaming
                    answer, confidence = self.llm.get_answer(query_text, full_context_str)
                
                logger.info(f"Generation: {time.time() - t_gen:.3f}s")
            except Exception as e:
                logger.error(f"LLM error: {e}")
                answer = "Error generating answer."
        
        # Diagrams
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
        
        # Cache
        self.cache.set(query_text, subject, grade, result, embedding=query_embedding)
        
        return result

    def _replay_cached_response(self, cached_result, stream_callback):
        """Simulate streaming for cached answers."""
        answer = cached_result.get("answer", "")
        
        # Stream in word chunks
        words = answer.split(" ")
        chunk_size = 5
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            if i > 0:
                chunk = " " + chunk
            stream_callback(chunk)
    
    def _calculate_confidence(self, answer: str, context: str) -> float:
        """Calculate confidence based on answer quality."""
        if not answer or len(answer) < 10:
            return 0.2
        
        confidence = 0.65
        
        word_count = len(answer.split())
        if word_count >= 20:
            confidence += 0.1
        elif word_count < 10:
            confidence -= 0.2
        
        sentence_count = answer.count('.') + answer.count('!') + answer.count('?')
        if sentence_count >= 2:
            confidence += 0.1
        
        if context and len(context.strip()) > 30:
            confidence += 0.15
        
        return min(1.0, max(0.1, confidence))