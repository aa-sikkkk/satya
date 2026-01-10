"""
User Edge Case Handler for Satya Learning System

Handles common user interaction edge cases to improve user experience
and save inference computation.
"""

import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class UserEdgeCaseHandler:
    """
    Detects and handles special cases in user queries
    before they reach the heavy RAG/LLM pipeline.
    """
    
    def __init__(self):
        self.greetings = {
            "hi", "hello", "namaste", "namaskar", "hey",
            "good morning", "good afternoon", "good evening"
        }
        
        self.apologies = {
            "sorry", "i'm sorry", "my bad", "apologies"
        }
        
        self.gratitude = {
            "thank you", "thanks", "thx", "dhanyabad"
        }

    def check_edge_cases(self, query: str) -> Optional[str]:
        """
        Check if the query matches a known edge case.
        Returns a pre-canned response if matched, else None.
        
        Args:
            query: User's raw input string
            
        Returns:
            Response string or None
        """
        query_lower = query.strip().lower()
        
        # 1. Empty Query
        if not query_lower:
            return "Please type a question. I am here to help you learn!"
            
        # 2. Short Vague Queries
        if len(query_lower) < 4:
            return "Could you please elaborate? Your question is a bit too short for me to understand."
            
        # 3. Greetings
        # Check exact match or start
        if query_lower in self.greetings:
            return "Namaste! I am Satya, your learning companion. How can I help you with your studies today?"
            
        for g in self.greetings:
            if query_lower.startswith(g + " "):
                 # Let it pass to LLM if it's "Hello, what is an atom?"
                 # But if it's just a greeting, we might want to be nicer?
                 # ideally, let LLM handle mixed queries.
                 pass

        # 4. Gratitude
        if query_lower in self.gratitude:
            return "You're welcome! Keep studying hard!"
            
        # 5. Apologies
        if query_lower in self.apologies:
            return "No problem at all! Let's continue learning."
            
        # 6. "I don't understand"
        if "don't understand" in query_lower or "confused" in query_lower:
            # We can prompt them to be specific, or this might be handled better by keeping context
            # For now, return None to let LLM handle it with context
            return None

        return None
        
    def is_math_query(self, query: str) -> bool:
        """Simple heuristic to detect math queries for specialized prompt injection."""
        math_symbols = ['+', '=', '/', '*', '√', '^', 'solve', 'calculate', 'equation']
        count = sum(1 for s in math_symbols if s in query.lower())
        return count >= 1