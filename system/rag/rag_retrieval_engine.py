"""
RAG Retrieval Engine for Satya Learning System

The core orchestrator that connects all system components:
- User inputs -> Edge Case Handler
- Query -> Embedding -> ChromaDB Retrieval
- Results -> Anti-Confusion Engine (Filtering & Ranking)
- Context -> BitNet Model -> Answer Generation
- Output -> ASCII Diagram integration
"""

import logging
import time
from typing import Dict, List, Optional, Any
import chromadb
from pathlib import Path

# Import our new components
from system.rag.anti_confusion_engine import AntiConfusionEngine
from system.rag.ascii_diagram_library import ASCIIDiagramLibrary
from system.rag.user_edge_case_handler import UserEdgeCaseHandler
from system.rag.rag_cache import RAGCache
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator
from ai_model.model_utils.model_handler import ModelHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGRetrievalEngine:
    """
    Main RAG orchestrator for Satya.
    """
    
    def __init__(
        self,
        chroma_db_path: str = "satya_data/chroma_db",
        model_path: str = "satya_data/models/phi15",  # Point to specific model folder
        llm_handler=None  # Optional: pass pre-loaded model to avoid double loading
    ):
        """Initialize the RAG Engine and all sub-components."""
        logger.info("Initializing Satya RAG Engine...")
        
        self.chroma_db_path = chroma_db_path
        
        # 1. Initialize Sub-components
        self.edge_case_handler = UserEdgeCaseHandler()
        self.anti_confusion = AntiConfusionEngine()
        self.diagram_library = ASCIIDiagramLibrary()
        self.cache = RAGCache(max_size=100, ttl_seconds=3600)  # 1 hour TTL
        
        # 2. Initialize Embedding Model (for query encoding)
        # We reuse the utility class but in inference mode
        self.embedding_gen = EmbeddingGenerator(device='cpu') # Force CPU for inference stability
        
        # 3. Initialize ChromaDB
        try:
             self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
             logger.info(f"ChromaDB connected at {chroma_db_path}")
        except Exception as e:
            logger.error(f"ChromaDB connection failed: {e}")
            self.chroma_client = None

        # 4. Initialize LLM (reuse if provided, otherwise create new)
        if llm_handler:
            self.llm = llm_handler
            logger.info("LLM Model connected (reused pre-loaded model)")
        else:
            try:
                 self.llm = ModelHandler(model_path=model_path) # Changed to ModelHandler
                 logger.info("LLM Model connected")
            except Exception as e:
                logger.error(f"LLM connection failed: {e}")
                self.llm = None
        
        logger.info("RAG Engine initialized successfully")


        
    def _get_relevant_collections(self, subject: str, grade: str) -> List[str]:
        """
        Determine which collections to query based on filters.
        Implements LAYER 1: Mandatory Filtering.
        """
        collections = []
        
        if not self.chroma_client:
            return []
            
        # Get all available collections
        all_colls = [c.name for c in self.chroma_client.list_collections()]
        
        # 1. High Priority: NEB Collections (Exact Match)
        neb_key = f"neb_{subject}_grade_{grade}"
        for name in all_colls:
            if neb_key in name:
                collections.append(name)
        
        # 2. Medium Priority: Curated Subject Collections (Broad Match)
        # Check standard names: openstax_science, finemath, etc.
        subject_map = {
            "science": ["openstax_science", "scienceqa"],
            "math": ["finemath", "gsm8k"],
            "computer": ["cs_stanford"],
            "english": ["fineweb_edu"]
        }
        
        # Add mapped collections if they exist (Limit to top 1-2)
        if subject in subject_map:
            for target in subject_map[subject]:
                if target in all_colls and target not in collections:
                    collections.append(target)
                    # If we have NEB + 1 external, that's enough for speed
                    if len(collections) >= 2:
                        break
                        
        # 3. Low Priority / Broad Fallback (Only if we have NOTHING else)
        if not collections:
            fallbacks = ["fineweb_edu", "khanacademy_pedagogy"]
            for fb in fallbacks:
                if fb in all_colls and fb not in collections:
                    collections.append(fb)
                    if len(collections) >= 2: # Keep it light
                         break
        
        # Hard cap to prevent "using all sources"
        return collections[:3]

    def query(
        self,
        query_text: str,
        subject: str,
        grade: str,
        n_results: int = 5,
        phase1_callback=None,  # Callback to send Phase 1 answer immediately
        phase2_callback=None   # Callback for Phase 2 token streaming
    ) -> Dict[str, Any]:
        """
        Main query entry point.
        """
        start_time = time.time()
        
        # --- Pre-processing & Edge Cases ---
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

        # --- Cache Check (Layer 1: Exact Match) ---
        cached_result = self.cache.get(query_text, subject, grade)
        if cached_result:
            logger.info(f"Cache HIT (Exact) for '{query_text[:50]}...'")
            self._replay_cached_response(cached_result, phase1_callback, phase2_callback)
            results = cached_result
            results["processing_time"] = time.time() - start_time
            return results

        # --- Embedding Generation ---
        t_embed = time.time()
        query_embedding = self.embedding_gen.generate_embeddings(query_text)
        logger.info(f"Embedding Time: {time.time() - t_embed:.3f}s")

        # --- Cache Check (Layer 2: Semantic Match) ---
        # Threshold 0.92 ensures very high similarity (same meaning)
        semantic_hit = self.cache.find_similar(query_embedding, subject, grade, threshold=0.92)
        if semantic_hit:
            logger.info(f"Cache HIT (Semantic) for '{query_text[:50]}...'")
            self._replay_cached_response(semantic_hit, phase1_callback, phase2_callback)
            results = semantic_hit
            results["processing_time"] = time.time() - start_time
            return results
        
        # 2. Select Collections (Layer 1 Defense)
        target_collections = self._get_relevant_collections(subject, grade)
        if not target_collections:
            logger.warning(f"No collections found for {subject} grade {grade}")

        raw_results = []
        
        # Query each collection (Parallelized)
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

        # Use 3 threads to prevent IO contention blocking
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_coll = {executor.submit(query_collection, name): name for name in target_collections}
            for future in as_completed(future_to_coll):
                raw_results.extend(future.result())
                
        logger.info(f"Retrieval Time: {time.time() - t_retrieve:.3f}s (Collections: {len(target_collections)})")

        # --- Ranking & Filtering Phase ---
        t_rank = time.time()
        
        # Apply Layers 2 & 3: Prioritization and Ranking
        ranked_chunks = self.anti_confusion.rank_results(raw_results, query_text)
        
        # Select top k for context window
        final_context_chunks = []
        current_len = 0
        limit = 600 # Balanced: Enough for 1 good paragraph, small enough for <10s TTFT
        
        for chunk in ranked_chunks:
            if chunk['final_score'] < 0.35: # Slightly lower threshold to be safe
                continue
                
            text = chunk['text']
            if current_len + len(text) < limit:
                final_context_chunks.append(chunk)
                current_len += len(text)
            else:
                break
        
        # Re-order for Layer 5 (Priority Handling)
        ordered_chunks = self.anti_confusion.resolve_conflicts(final_context_chunks)
        ranking_time = time.time() - t_rank
        logger.info(f"Ranking Time: {ranking_time:.4f}s")
        
        if ordered_chunks:
            top_score = ordered_chunks[0].get('final_score', 0)
            logger.info(f"Top Rank Score: {top_score:.2f} (Source: {ordered_chunks[0]['metadata'].get('source', 'N/A')})")
        
        # Extract text list for LLM
        context_texts = [c['text'] for c in ordered_chunks]
        full_context_str = "\n\n".join(context_texts)
        logger.info(f"Final Context Length: {len(full_context_str)} chars")
        
        # --- Generation Phase ---
        answer = "I'm having trouble thinking right now."
        confidence = 0.0
        
        if self.llm:
            try:
                t_gen = time.time()
                
                # PHASE 1: Fast framing (call immediately and send via callback)
                phase1_answer, phase1_conf = self.llm.phi15_handler.get_answer_phase1(query_text)
                
                # Send Phase 1 to GUI immediately via callback
                if phase1_callback:
                    phase1_callback(phase1_answer, phase1_conf)
                
                # PHASE 2: Structured depth (with RAG context)
                phase2_answer, phase2_conf = self.llm.phi15_handler.get_answer_phase2(
                    query_text, full_context_str, phase1_answer, stream_callback=phase2_callback
                )
                
                # Combine for final answer
                answer = f"{phase1_answer}\n\n{phase2_answer}"
                confidence = max(phase1_conf, phase2_conf)
                
                logger.info(f"LLM Gen Time (Two-Phase): {time.time() - t_gen:.3f}s")
            except Exception as e:
                logger.error(f"LLM generation error: {e}")
                answer = "Error generating answer from AI model."
        
        # --- Post-Processing ---
        
        # Check for Diagrams
        diagram = self.diagram_library.find_diagram_by_text(query_text)
        
        result = {
            "answer": answer,
            "context_used": context_texts,
            "sources": [c['metadata'] for c in ordered_chunks],
            "diagram": diagram,
            "confidence": confidence,
            "processing_time": time.time() - start_time,
            "type": "rag_response",
            # Store components for cache replay
            "answer_phase1": phase1_answer if 'phase1_answer' in locals() else "",
            "answer_phase2": phase2_answer if 'phase2_answer' in locals() else "",
            "confidence_phase1": phase1_conf if 'phase1_conf' in locals() else confidence,
            "confidence_phase2": phase2_conf if 'phase2_conf' in locals() else confidence
        }
        
        # Cache the result for future queries (with embedding)
        self.cache.set(query_text, subject, grade, result, embedding=query_embedding)
        
        return result

    def _replay_cached_response(self, cached_result, phase1_callback, phase2_callback):
        """Helper to simulate streaming for cache hits."""
        # Simulate Phase 1 Callback (Immediate)
        if phase1_callback and "answer_phase1" in cached_result:
            p1_conf = cached_result.get("confidence_phase1", cached_result.get("confidence", 0.8))
            phase1_callback(cached_result["answer_phase1"], p1_conf)
        
        # Simulate Phase 2 Stream (Burst)
        if phase2_callback and "answer_phase2" in cached_result:
            p2_text = cached_result["answer_phase2"]
            words = p2_text.split(" ")
            if words:
                chunk_size = 5
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i+chunk_size])
                    if i > 0: chunk = " " + chunk
                    phase2_callback(chunk)
