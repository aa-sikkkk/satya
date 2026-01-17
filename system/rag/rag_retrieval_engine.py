"""
Lightweight RAG Retrieval Engine for Satya Learning System
Optimized for i3 processors
"""

import logging
import time
from typing import Dict, List, Any
import chromadb
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import sub-components
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
    """i3-friendly RAG orchestrator for Satya."""

    def __init__(
        self,
        chroma_db_path: str = "satya_data/chroma_db",
        model_path: str = "satya_data/models/phi15",
        llm_handler=None
    ):
        logger.info("Initializing Satya RAG Engine (i3-optimized)...")

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

    def _get_relevant_collections(self, subject: str, grade: str) -> List[str]:
        """
        Select relevant collections based on subject and grade.
        
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
        # Map subjects to appropriate general knowledge collections
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
        
        # Add HuggingFace collections for this subject (ignore grade)
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
        return collections[:3]  # Limit to 3 for performance
  # Cap for i3 performance

    def query(
        self,
        query_text: str,
        subject: str,
        n_results: int = 3,
        stream_callback=None  # RESTORED for real-time feedback
    ) -> Dict[str, Any]:
        """Main query method, i3-optimized with streaming support."""
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
        
        # ============ INPUT NORMALIZATION (NEW) ============
        # Clean the question BEFORE retrieval
        normalization_result = self.input_normalizer.normalize(query_text)
        clean_question = normalization_result["clean_question"]
        
        # Log normalization for debugging
        if normalization_result["notes"]:
            logger.info(f"Normalization applied: {normalization_result['notes']}")
            logger.info(f"Intent: {normalization_result['intent']}, Confidence: {normalization_result['confidence']:.2f}")
        
        # Use clean question for the rest of the pipeline
        effective_query = clean_question if clean_question else query_text

        # Cache check (exact match) - NO GRADE
        # Use ORIGINAL query for cache key (user may ask same messy question)
        cached_result = self.cache.get(query_text, subject, "")
        if cached_result:
            logger.info(f"Cache HIT (exact)")
            if stream_callback:
                # Stream cached answer word by word for smooth UX
                answer = cached_result.get("answer", "")
                words = answer.split()
                for i, word in enumerate(words):
                    stream_callback(word + (" " if i < len(words) - 1 else ""))
            return {**cached_result, "processing_time": time.time() - start_time}

        # IMMEDIATE FEEDBACK - Show status while processing
        if stream_callback:
            stream_callback("🔍 Searching knowledge base...\n\n")

        # Embedding generation - USE CLEAN QUESTION
        if stream_callback:
            stream_callback("📊 Analyzing your question...\n\n")
        
        query_embedding = self.embedding_gen.generate_embeddings(effective_query)

        # Cache check (semantic match) - NO GRADE
        semantic_hit = self.cache.find_similar(query_embedding, subject, "", threshold=0.88)
        if semantic_hit:
            logger.info(f"Cache HIT (semantic)")
            if stream_callback:
                answer = semantic_hit.get("answer", "")
                words = answer.split()
                for i, word in enumerate(words):
                    stream_callback(word + (" " if i < len(words) - 1 else ""))
            return {**semantic_hit, "processing_time": time.time() - start_time}

        # Collections selection - NO GRADE
        target_collections = self._get_relevant_collections(subject, "")
        if not target_collections:
            logger.warning(f"No collections found for {subject}")
        
        # Show progress
        if stream_callback:
            stream_callback("🎯 Finding best matches...\n\n")

        # Retrieval
        raw_results = []
        
        def query_collection(coll_name):
            try:
                coll = self.chroma_client.get_collection(coll_name)
                res = coll.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=min(2, n_results)  # Reduced for i3
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

        # Reduced threading for i3
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(query_collection, name) for name in target_collections]
            for future in as_completed(futures):
                raw_results.extend(future.result())

        # Ranking & filtering
        ranked_chunks = self.anti_confusion.rank_results(raw_results, query_text)
        final_context_chunks = []
        current_len = 0
        limit = 400  # Smaller context for i3
        
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
        
        # Show progress before generation
        if stream_callback:
            stream_callback("✨ Generating answer...\n\n")

        # LLM generation with STREAMING
        answer = "Unable to generate answer."
        confidence = 0.0
        
        if self.llm:
            try:
                if stream_callback:
                    # STREAM tokens in real-time - NO BUFFERING
                    answer = ""
                    print("🚀 RAG: Starting token streaming...", flush=True)
                    token_count = 0
                    
                    # Use clean question for better Phi inference
                    for token in self.llm.handler.get_answer_stream(effective_query, full_context_str):
                        answer += token
                        print(f"📤 RAG: Sending token #{token_count}: '{token}'", flush=True)
                        stream_callback(token)  # Send immediately
                        token_count += 1
                    
                    print(f"✅ RAG: Streaming complete. Total tokens: {token_count}", flush=True)
                    
                    # Calculate confidence with RAG context quality
                    confidence = self._calculate_confidence(answer, effective_query, final_context_chunks)
                else:
                    # Non-streaming fallback
                    answer, confidence = self.llm.simple_handler.get_answer(effective_query, full_context_str)
            except Exception as e:
                logger.error(f"LLM generation error: {e}")
                if stream_callback:
                    stream_callback("Error generating answer.")

        # ASCII diagrams
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

        # Cache result - NO GRADE
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
        
        confidence = 0.5  # Base confidence
        
        # Factor 1: Answer length (good educational answers are 50-150 words)
        word_count = len(answer.split())
        if 50 <= word_count <= 150:
            confidence += 0.2  # Ideal length
        elif 30 <= word_count < 50 or 150 < word_count <= 200:
            confidence += 0.1  # Acceptable length
        # else: no bonus for too short or too long
        
        # Factor 2: Question-answer relevance
        q_words = set(w.lower() for w in question.split() if len(w) > 3)
        a_words = set(w.lower() for w in answer.split())
        if q_words:
            relevance = len(q_words & a_words) / len(q_words)
            confidence += relevance * 0.2
        
        # Factor 3: RAG context quality (if available)
        if context_chunks and len(context_chunks) > 0:
            # If we have good RAG context, boost confidence
            avg_score = sum(c.get('final_score', 0.5) for c in context_chunks) / len(context_chunks)
            confidence += avg_score * 0.1
        
        return min(1.0, confidence)