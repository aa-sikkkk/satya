#!/usr/bin/env python3
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
Enhanced Chunker for Satya Learning System

Math-aware chunking with overlap to prevent formula splitting.

Features:
- 20% overlap between chunks
- LaTeX/formula preservation
- Sentence-boundary splitting
- Math marker detection ($, $$, \\[, \\])
- Preserves code blocks
- Metadata tagging
"""

import os
import re
import logging
from typing import List, Dict, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedChunker:
    """
    Math-aware text chunking with overlap.
    
    Prevents splitting of mathematical formulas and code blocks.
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        overlap_ratio: float = 0.2,
        min_chunk_size: int = 100
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target chunk size in characters
            overlap_ratio: Overlap between chunks (0.0-0.5)
            min_chunk_size: Minimum chunk size
        """
        self.chunk_size = chunk_size
        self.overlap_ratio = overlap_ratio
        self.overlap_size = int(chunk_size * overlap_ratio)
        self.min_chunk_size = min_chunk_size
        
        logger.info(f"Enhanced chunker initialized:")
        logger.info(f"   Chunk size: {chunk_size} chars")
        logger.info(f"   Overlap: {overlap_ratio*100:.0f}% ({self.overlap_size} chars)")
    
    def find_math_regions(self, text: str) -> List[Tuple[int, int]]:
        """
        Find all math regions in text (LaTeX, inline math, etc.).
        
        Args:
            text: Input text
            
        Returns:
            List of (start, end) positions for math regions
        """
        math_regions = []
        
        # LaTeX display math: $$...$$
        for match in re.finditer(r'\$\$.*?\$\$', text, re.DOTALL):
            math_regions.append((match.start(), match.end()))
        
        # LaTeX inline math: $...$
        for match in re.finditer(r'\$[^\$]+?\$', text):
            math_regions.append((match.start(), match.end()))
        
        # LaTeX brackets: \[...\]
        for match in re.finditer(r'\\\[.*?\\\]', text, re.DOTALL):
            math_regions.append((match.start(), match.end()))
        
        # LaTeX parentheses: \(...\)
        for match in re.finditer(r'\\\(.*?\\\)', text):
            math_regions.append((match.start(), match.end()))
        
        # Common math expressions (e.g., "E = mc²", "x² + 5x + 6 = 0")
        for match in re.finditer(r'[a-zA-Z]\s*[²³⁴⁵⁶⁷⁸⁹⁰₁₂₃₄₅₆₇₈₉₀\^]\s*[+\-=]', text):
            # Extend to full expression
            start = match.start()
            end = match.end()
            
            # Extend backwards to start of expression
            while start > 0 and text[start-1] not in ['.', '\n', '?', '!']:
                start -= 1
            
            # Extend forwards to end of expression
            while end < len(text) and text[end] not in ['.', '\n', '?', '!']:
                end += 1
            
            math_regions.append((start, end))
        
        # Merge overlapping regions
        if math_regions:
            math_regions.sort()
            merged = [math_regions[0]]
            
            for start, end in math_regions[1:]:
                if start <= merged[-1][1]:
                    # Overlapping - merge
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            
            return merged
        
        return []
    
    def find_code_blocks(self, text: str) -> List[Tuple[int, int]]:
        """
        Find code blocks in text.
        
        Args:
            text: Input text
            
        Returns:
            List of (start, end) positions for code blocks
        """
        code_regions = []
        
        # Markdown code blocks: ```...```
        for match in re.finditer(r'```.*?```', text, re.DOTALL):
            code_regions.append((match.start(), match.end()))
        
        # Inline code: `...`
        for match in re.finditer(r'`[^`]+?`', text):
            code_regions.append((match.start(), match.end()))
        
        return code_regions
    
    def is_in_protected_region(
        self,
        position: int,
        protected_regions: List[Tuple[int, int]]
    ) -> bool:
        """
        Check if position is inside a protected region.
        
        Args:
            position: Character position
            protected_regions: List of (start, end) tuples
            
        Returns:
            True if position is protected
        """
        for start, end in protected_regions:
            if start <= position <= end:
                return True
        return False
    
    def find_sentence_boundaries(self, text: str) -> List[int]:
        """
        Find sentence boundaries (safe split points).
        
        Args:
            text: Input text
            
        Returns:
            List of character positions for sentence boundaries
        """
        boundaries = []
        
        # Find all potential sentence endings
        for match in re.finditer(r'[.!?]\s+', text):
            boundaries.append(match.end())
        
        # Add paragraph breaks
        for match in re.finditer(r'\n\n+', text):
            boundaries.append(match.start())
        
        return sorted(set(boundaries))
    
    def smart_chunk_with_overlap(
        self,
        text: str,
        metadata: Dict = None
    ) -> List[Dict]:
        """
        Chunk text with math-aware splitting and overlap.
        
        Args:
            text: Input text
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of chunk dictionaries
        """
        if not text or len(text) < self.min_chunk_size:
            return [{
                'text': text,
                'chunk_id': 0,
                'start_pos': 0,
                'end_pos': len(text),
                'metadata': metadata or {}
            }]
        
        # Find protected regions (math and code)
        math_regions = self.find_math_regions(text)
        code_regions = self.find_code_blocks(text)
        protected_regions = sorted(math_regions + code_regions)
        
        # Find sentence boundaries
        sentence_boundaries = self.find_sentence_boundaries(text)
        
        chunks = []
        current_pos = 0
        chunk_id = 0
        loop_counter = 0
        
        while current_pos < len(text):
            # Safety check for infinite loops
            if loop_counter > len(text) + 1000: # Generous buffer
                logger.error(f"Infinite loop detected in chunking! Breaking safely.")
                break
            loop_counter += 1

            # Calculate target end position
            target_end = current_pos + self.chunk_size
            
            if target_end >= len(text):
                # Last chunk
                chunk_text = text[current_pos:]
                chunks.append({
                    'text': chunk_text,
                    'chunk_id': chunk_id,
                    'start_pos': current_pos,
                    'end_pos': len(text),
                    'metadata': metadata or {}
                })
                break
            
            # Find safe split point near target_end
            # Priority: sentence boundary > paragraph > word boundary
            
            # Check if target_end is in protected region
            if self.is_in_protected_region(target_end, protected_regions):
                # Find end of protected region
                for start, end in protected_regions:
                    if start <= target_end <= end:
                        target_end = end
                        break
            
            # Find nearest sentence boundary before target_end
            safe_split = target_end
            for boundary in reversed(sentence_boundaries):
                if boundary <= target_end and boundary > current_pos:
                    # Make sure boundary is not in protected region
                    if not self.is_in_protected_region(boundary, protected_regions):
                        safe_split = boundary
                        break
            
            # If no good sentence boundary, try word boundary
            if safe_split == target_end:
                # Find last space before target_end
                last_space = text.rfind(' ', current_pos, target_end)
                if last_space > current_pos:
                    safe_split = last_space
            
            # Create chunk
            chunk_text = text[current_pos:safe_split].strip()
            
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append({
                    'text': chunk_text,
                    'chunk_id': chunk_id,
                    'start_pos': current_pos,
                    'end_pos': safe_split,
                    'metadata': metadata or {}
                })
                chunk_id += 1
            
            # Ensure we made progress
            if safe_split <= current_pos:
                safe_split = current_pos + self.chunk_size

            # Move to next position with overlap
            next_pos = safe_split - self.overlap_size
            
            # Make sure we're strictly moving forward
            if chunks:
                last_start = chunks[-1]['start_pos']
                if next_pos <= last_start:
                    next_pos = safe_split # Give up overlap to ensure progress
            else:
                 if next_pos <= 0:
                     next_pos = safe_split

            # Absolute final safety: if we haven't moved, force move
            if next_pos <= current_pos:
                next_pos = current_pos + max(1, int(self.chunk_size * 0.5))

            current_pos = next_pos
        
        logger.info(f"Created {len(chunks)} chunks from {len(text)} chars")
        logger.info(f"   Math regions protected: {len(math_regions)}")
        logger.info(f"   Code blocks protected: {len(code_regions)}")
        
        return chunks
    
    def chunk_markdown_file(
        self,
        markdown_file: str,
        output_dir: str = None
    ) -> List[Dict]:
        """
        Chunk a markdown file and optionally save chunks.
        
        Args:
            markdown_file: Path to markdown file
            output_dir: Optional directory to save chunks
            
        Returns:
            List of chunks
        """
        logger.info(f"Chunking: {markdown_file}")
        
        # Read file
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract metadata from YAML frontmatter (if present)
        metadata = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # Parse YAML frontmatter
                frontmatter = parts[1]
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip().strip('"\'')
                
                # Use content after frontmatter
                content = parts[2].strip()
        
        # Add source file to metadata
        metadata['source_file'] = os.path.basename(markdown_file)
        
        # Chunk content
        chunks = self.smart_chunk_with_overlap(content, metadata)
        
        # Save chunks if output directory specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            base_name = Path(markdown_file).stem
            
            for chunk in chunks:
                chunk_file = output_path / f"{base_name}_chunk_{chunk['chunk_id']:03d}.txt"
                
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    # Write metadata as comments
                    f.write(f"# Chunk {chunk['chunk_id']}\n")
                    f.write(f"# Source: {metadata.get('source_file', 'unknown')}\n")
                    f.write(f"# Grade: {metadata.get('grade', 'unknown')}\n")
                    f.write(f"# Subject: {metadata.get('subject', 'unknown')}\n")
                    f.write(f"# Chapter: {metadata.get('chapter', 'unknown')}\n")
                    f.write(f"# Position: {chunk['start_pos']}-{chunk['end_pos']}\n")
                    f.write("\n")
                    f.write(chunk['text'])
            
            logger.info(f"Saved {len(chunks)} chunks to {output_dir}")
        
        return chunks
    
    def batch_chunk_directory(
        self,
        input_dir: str,
        output_dir: str,
        file_pattern: str = "*.md"
    ) -> Dict:
        """
        Batch chunk all files in a directory.
        
        Args:
            input_dir: Directory containing markdown files
            output_dir: Directory to save chunks
            file_pattern: File pattern to match (default: *.md)
            
        Returns:
            Processing results
        """
        input_path = Path(input_dir)
        files = list(input_path.glob(file_pattern))
        
        logger.info(f"Found {len(files)} files to chunk")
        
        results = {
            'processed': 0,
            'total_chunks': 0,
            'failed': []
        }
        
        for i, file in enumerate(files, 1):
            try:
                logger.info(f"\n[{i}/{len(files)}] Processing {file.name}...")
                
                chunks = self.chunk_markdown_file(str(file), output_dir)
                
                results['processed'] += 1
                results['total_chunks'] += len(chunks)
                
            except Exception as e:
                logger.error(f"Failed to chunk {file.name}: {e}")
                results['failed'].append({
                    'file': str(file),
                    'error': str(e)
                })
        
        logger.info(f"\nChunking complete!")
        logger.info(f"   Files processed: {results['processed']}")
        logger.info(f"   Total chunks: {results['total_chunks']}")
        logger.info(f"   Failed: {len(results['failed'])}")
        
        return results


def main():
    """CLI interface for enhanced chunker."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Math-aware chunking for educational content")
    parser.add_argument('input_dir', help="Directory containing markdown files")
    parser.add_argument('output_dir', help="Directory to save chunks")
    parser.add_argument('--chunk-size', type=int, default=512, help="Target chunk size (default: 512)")
    parser.add_argument('--overlap', type=float, default=0.2, help="Overlap ratio (default: 0.2)")
    parser.add_argument('--pattern', default="*.md", help="File pattern (default: *.md)")
    
    args = parser.parse_args()
    
    # Initialize chunker
    chunker = EnhancedChunker(
        chunk_size=args.chunk_size,
        overlap_ratio=args.overlap
    )
    
    # Batch process
    results = chunker.batch_chunk_directory(
        args.input_dir,
        args.output_dir,
        args.pattern
    )
    
    # Print summary
    print(f"\n✅ Processing complete!")
    print(f"Files processed: {results['processed']}")
    print(f"Total chunks: {results['total_chunks']}")
    print(f"Failed: {len(results['failed'])}")


if __name__ == "__main__":
    main()
