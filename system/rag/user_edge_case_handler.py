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
        query_lower = query.strip().lower()
        
        # 1. Empty Query
        if not query_lower:
            return "Please type a question. I am here to help you learn!"
            
        # 2. Short Vague Queries
        if len(query_lower) < 4:
            return "Could you please elaborate? Your question is a bit too short for me to understand."
            
        # 3. Greetings
        if query_lower in self.greetings:
            return "Namaste! I am Satya, your learning companion. How can I help you with your studies today?"
            
        for g in self.greetings:
            if query_lower.startswith(g + " "):
                pass

        # 4. Gratitude
        if query_lower in self.gratitude:
            return "You're welcome! Keep studying hard!"
            
        # 5. Apologies
        if query_lower in self.apologies:
            return "No problem at all! Let's continue learning."
            
        # 6. "I don't understand"
        if "don't understand" in query_lower or "confused" in query_lower:
            return None

        return None
        
    def is_math_query(self, query: str) -> bool:
        math_symbols = ['+', '=', '/', '*', '√', '^', 'solve', 'calculate', 'equation']
        count = sum(1 for s in math_symbols if s in query.lower())
        return count >= 1