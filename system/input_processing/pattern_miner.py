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
Pattern Miner - Automated Noise Discovery
Analyzes logs to find repeated patterns for learning.
"""

import json
import logging
import re
from typing import List, Dict
from collections import Counter

logger = logging.getLogger(__name__)


class PatternMiner:
    """Discovers new noise phrases from production logs."""
    
    def __init__(self, min_frequency: int = 10, min_confidence: float = 0.6):
        self.min_frequency = min_frequency
        self.min_confidence = min_confidence
        self.noise_indicators = [
            'please', 'can you', 'help me', 'tell me', 'like', 'basically',
            'actually', 'just', 'really', 'bro', 'bruh', 'sir'
        ]
    
    def mine_new_patterns(self, feedback_logs: List[Dict]) -> List[Dict]:
        """Discovers patterns from low-confidence cases."""
        low_conf = [log for log in feedback_logs if log.get('confidence', 1.0) < 0.7]
        
        if not low_conf:
            logger.info("No low-confidence cases to analyze")
            return []
        
        logger.info(f"Analyzing {len(low_conf)} cases...")
        
        ngrams = self._extract_ngrams(low_conf)
        ngram_counts = Counter(ngrams)
        suggestions = []
        
        for phrase, count in ngram_counts.most_common(100):
            if count >= self.min_frequency and self._is_likely_noise(phrase):
                confidence = self._calculate_confidence(phrase, low_conf, count)
                if confidence >= self.min_confidence:
                    suggestions.append({
                        'phrase': phrase,
                        'frequency': count,
                        'confidence': confidence,
                        'examples': self._get_examples(phrase, low_conf, 3)
                    })
        
        suggestions.sort(key=lambda x: x['confidence'] * x['frequency'], reverse=True)
        logger.info(f"Found {len(suggestions)} pattern suggestions")
        return suggestions
    
    def generate_report(self, suggestions: List[Dict], output_file: str):
        """Generates a human-readable report."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# Pattern Mining Report\n\n")
                f.write(f"Total suggestions: {len(suggestions)}\n\n---\n\n")
                
                for i, s in enumerate(suggestions, 1):
                    f.write(f"## {i}. \"{s['phrase']}\"\n\n")
                    f.write(f"- **Frequency**: {s['frequency']}\n")
                    f.write(f"- **Confidence**: {s['confidence']:.2f}\n")
                    f.write(f"- **Examples**:\n")
                    for ex in s['examples']:
                        f.write(f"  - \"{ex}\"\n")
                    f.write("\n---\n\n")
            logger.info(f"Report written to {output_file}")
        except Exception as e:
            logger.error(f"Could not write report: {e}")
    
    @staticmethod
    def load_feedback_logs(log_file: str) -> List[Dict]:
        """Loads feedback logs from JSONL file."""
        logs = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
            logger.info(f"Loaded {len(logs)} log entries")
            return logs
        except Exception as e:
            logger.error(f"Could not load logs: {e}")
            return []
    
    # Private Methods 
    
    def _extract_ngrams(self, logs: List[Dict], n_range: tuple = (2, 4)) -> List[str]:
        """Extracts n-grams from logs."""
        ngrams = []
        for log in logs:
            words = log.get('original', '').lower().split()
            for n in range(n_range[0], n_range[1] + 1):
                for i in range(len(words) - n + 1):
                    ngram = ' '.join(words[i:i+n])
                    if len(ngram) > 5:
                        ngrams.append(ngram)
        return ngrams
    
    def _is_likely_noise(self, phrase: str) -> bool:
        """Checks if phrase is likely noise."""
        phrase_lower = phrase.lower()
        
        if any(ind in phrase_lower for ind in self.noise_indicators):
            return True
        
        patterns = [
            r'^(can|could|would) you',
            r'^please',
            r'help me',
            r'with reference',
            r'according to',
            r'in brief'
        ]
        
        return any(re.search(p, phrase_lower) for p in patterns)
    
    def _calculate_confidence(self, phrase: str, logs: List[Dict], frequency: int) -> float:
        """Calculates confidence that phrase is noise."""
        confidence = 0.5
        
        if frequency > 50:
            confidence += 0.2
        elif frequency > 20:
            confidence += 0.1
        
        start_count = sum(1 for log in logs 
                         if phrase in log.get('original', '').lower() 
                         and log.get('original', '').lower().startswith(phrase))
        
        if start_count > frequency * 0.7:
            confidence += 0.15
        
        if any(ind in phrase.lower() for ind in self.noise_indicators):
            confidence += 0.15
        
        return min(1.0, confidence)
    
    def _get_examples(self, phrase: str, logs: List[Dict], limit: int) -> List[str]:
        """Gets example questions containing phrase."""
        examples = []
        for log in logs:
            original = log.get('original', '')
            if phrase in original.lower():
                examples.append(original)
                if len(examples) >= limit:
                    break
        return examples
