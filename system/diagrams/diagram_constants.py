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
Constants and regex patterns for diagram generation.
Shared across extraction and generation modules.
"""

import re

# Stopwords
STOPWORDS = frozenset({
    "the", "is", "are", "a", "an", "to", "of", "and", "or", "for", "in", "on", "at", "by", "that",
    "this", "it", "as", "be", "with", "from", "into", "their", "its", "they", "them", "can", "will",
    "about", "how", "what", "why", "which", "who", "whose", "when", "where", "than", "then", "also",
    "been", "has", "have", "had", "does", "did", "do", "would", "could", "should"
})

# UI phrases
IGNORED_PREFIXES = (
    'Note:', 'However,', 'In summary,', 
    '🔍', '📊', '🎯', '✨', '🚀', 
    'Searching knowledge', 'Analyzing your', 
    'Finding best', 'Generating answer',
    'GUI:', 'Received token'
)


# 1. Numbered Lists
NUMBERED_PATTERN = re.compile(
    r'(?:\**\(?\d+[\.\)]\s*\**\s*)([\w\s]{3,50}?)' 
    r'(?:\s*[-–—:]\s*|\n|$)',               
    re.MULTILINE
)

# 2. Named Steps
STEP_PREFIX_PATTERN = re.compile(
    r'(?:\**\s*(?:Step|Stage|Phase)\s+\d+[:\.]?\s*\**\s*)'
    r'([\w\s]{3,50}?)'
    r'(?:\s*[-–—:]\s*|\n|$)', 
    re.MULTILINE | re.IGNORECASE
)

# 3. Bullet Points
BULLET_POINT_PATTERN = re.compile(
    r'^\s*[\-\*\u2022]\s*\**\s*([\w\s]{3,50}?)'
    r'(?:\s*[-–—:]\s*|\n|$)',
    re.MULTILINE
)

# 4. List Extraction: Extracts lists after specific trigger words
PROCESS_LIST_PATTERN = re.compile(r'(?:consists of|includes|involves|comprises)[:\s]+([^\.]+)', re.IGNORECASE)
STAGE_LIST_PATTERN = re.compile(r'(?:stages?|steps?|phases?|processes?)[:\s]+([^\.]+)', re.IGNORECASE)

# 5. Cleaning Patterns
LEADING_NUMBERS_PATTERN = re.compile(r'^[\d\-\.\)\*]+\s*')
TRAILING_PUNCTUATION_PATTERN = re.compile(r'[.,;:]+$')

# 6. Logic & Decision Patterns
DECISION_KEYWORDS_PATTERN = re.compile(r'\b(if|else|condition|decision|check|whether|depending|based on)\b', re.IGNORECASE)
CONDITION_MATCH_PATTERN = re.compile(r'(?:if|when|whether)\s+([^,\.]+?)(?:,|\.|then|is)', re.IGNORECASE)

# 7. Cycle & Iteration Patterns
ITERATION_PATTERN = re.compile(r'(?:for|each|every)\s+(\w+)', re.IGNORECASE)
ITERATION_OVER_PATTERN = re.compile(r'(?:iterate|repeat|cycle)\s+(?:over|through|on)\s+(\w+)', re.IGNORECASE)
CYCLE_PATTERN = re.compile(
    r'\b(cycle|circular|continuous|repeating|recurring|ongoing|perpetual|'
    r'returns?|goes back|comes back|repeats?|loops?|recur|'
    r'continuous\s+(?:movement|process|flow|sequence)|'
    r'cycle\s+(?:of|in|continues?|repeats?)|'
    r'again|once more|repeatedly|continuously|'
    r'restart|begin again|start over)',
    re.IGNORECASE
)

# 8. Structure & Component Patterns
COMPONENT_PATTERN_1 = re.compile(r'(?:consists|composed|made)\s+of\s+([^\.]+?)(?:\.|$)', re.IGNORECASE)
COMPONENT_PATTERN_2 = re.compile(r'(?:has|contains|includes|comprises)\s+([^\.]+?)(?:\.|$)', re.IGNORECASE)
COMPONENT_PATTERN_3 = re.compile(r'(?:components?|parts?|elements?)\s+(?:are|is|include|consist of)\s+([^\.]+?)(?:\.|$)', re.IGNORECASE)

# 9. Sequential Flow
SEQUENTIAL_KEYWORDS_PATTERN = re.compile(r'\b(first|second|third|fourth|fifth|sixth|then|next|after|finally)', re.IGNORECASE)