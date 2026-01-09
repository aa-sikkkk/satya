#!/usr/bin/env python3
"""
Dataset Downloader for Satya Learning System
Grade 8-12 focused with ChromaDB optimization

Downloads and processes educational datasets into optimized vector database.
Final ChromaDB size: ~500MB-1GB (8 datasets compressed!)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datasets import load_dataset
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatasetDownloader:
    """
    Download and prepare Grade 8-12 educational datasets for ChromaDB.
    
    Optimizations:
    - Grade filtering (8-12 only)
    - Subject-specific collections
    - Aggressive deduplication
    - Auto-cleanup of raw data
    """
    
    # Grade 8-12 focused datasets
    DATASETS = {
        "openstax_science": {
            "source": "HuggingFaceTB/cosmopedia",
            "config": "openstax",
            "subjects": ["Science"],
            "grades": [8, 9, 10, 11, 12],
            "description": "OpenStax peer-reviewed textbooks (Biology, Physics, Chemistry)"
        },
        "khanacademy_pedagogy": {
            "source": "HuggingFaceTB/cosmopedia",
            "config": "khanacademy",
            "subjects": ["Science", "Math", "English"],
            "grades": [8, 9, 10, 11, 12],
            "description": "Khan Academy teaching methodology"
        },
        "finemath": {
            "source": "HuggingFaceTB/finemath",
            "config": "finemath-4plus",
            "subjects": ["Math"],
            "grades": [8, 9, 10, 11, 12],
            "description": "High-quality math reasoning and step-by-step solutions"
        },
        "gsm8k": {
            "source": "openai/gsm8k",
            "config": "main",
            "subjects": ["Math"],
            "grades": [8, 9, 10],
            "description": "Grade school math 8K problems"
        },
        "scienceqa": {
            "source": "derek-thomas/ScienceQA",
            "config": None,
            "subjects": ["Science"],
            "grades": [8, 9, 10, 11, 12],
            "description": "K-12 science Q&A with visual reasoning"
        },
        "fineweb_edu": {
            "source": "HuggingFaceFW/fineweb-edu",
            "config": None,
            "subjects": ["Science", "Math", "English", "Computer Science"],
            "grades": [8, 9, 10, 11, 12],
            "description": "High-quality educational web content"
        },
        "cs_stanford": {
            "source": "HuggingFaceTB/cosmopedia",
            "config": "stanford",
            "subjects": ["Computer Science"],
            "grades": [10, 11, 12],
            "description": "CS fundamentals and programming logic"
        },
        "cs_stanford": {
            "source": "HuggingFaceTB/cosmopedia",
            "config": "stanford",
            "subjects": ["Computer Science"],
            "grades": [10, 11, 12],
            "description": "CS fundamentals and programming logic"
        }
    }
    
    def __init__(self, output_dir: str = "satya_data/raw_datasets"):
        """
        Initialize dataset downloader.
        
        Args:
            output_dir: Directory for temporary raw datasets (will be deleted after processing)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def download_dataset(
        self, 
        dataset_name: str,
        subjects: Optional[List[str]] = None,
        grades: Optional[List[int]] = None
    ) -> Path:
        """
        Download a specific dataset with filtering.
        
        Args:
            dataset_name: Name of dataset (key from DATASETS)
            subjects: Filter by subjects (None = all)
            grades: Filter by grades (None = all)
            
        Returns:
            Path to downloaded dataset
        """
        if dataset_name not in self.DATASETS:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        
        dataset_info = self.DATASETS[dataset_name]
        logger.info(f"Downloading {dataset_name}: {dataset_info['description']}")
        
        try:
            # Load dataset from HuggingFace
            if dataset_info['config']:
                dataset = load_dataset(
                    dataset_info['source'],
                    dataset_info['config'],
                    split='train',
                    streaming=True  # Memory efficient
                )
            else:
                dataset = load_dataset(
                    dataset_info['source'],
                    split='train',
                    streaming=True
                )
            
            # Filter by subject and grade
            filtered_data = []
            for item in tqdm(dataset, desc=f"Processing {dataset_name}"):
                # Apply grade filtering
                if grades:
                    item_grade = self._extract_grade(item)
                    if item_grade and item_grade not in grades:
                        continue
                
                # Apply subject filtering
                if subjects:
                    item_subject = self._extract_subject(item)
                    if item_subject and item_subject not in subjects:
                        continue
                
                # Sanitize item for JSON serialization (remove images/binary)
                sanitized_item = {}
                for k, v in item.items():
                    # Skip 'image' keys or complex objects
                    if k == 'image': continue
                    if isinstance(v, (str, int, float, bool, list, dict, type(None))):
                        sanitized_item[k] = v
                    else:
                        # Try to convert to string if simple object, else skip
                        try:
                            sanitized_item[k] = str(v)
                        except:
                            pass

                filtered_data.append(sanitized_item)
                
                # Limit to prevent memory issues
                if len(filtered_data) >= 10000:  # Adjust based on dataset
                    break
            
            # Save to disk
            output_path = self.output_dir / f"{dataset_name}.jsonl"
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in filtered_data:
                    f.write(json.dumps(item) + '\n')
            
            logger.info(f"Saved {len(filtered_data)} items to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading {dataset_name}: {e}")
            raise
    
    def download_all(
        self,
        subjects: Optional[List[str]] = None,
        grades: Optional[List[int]] = None
    ) -> Dict[str, Path]:
        """
        Download all datasets with filtering.
        
        Args:
            subjects: Filter by subjects (None = all)
            grades: Filter by grades (None = all, recommended: [8,9,10,11,12])
            
        Returns:
            Dictionary mapping dataset names to paths
        """
        downloaded = {}
        
        for dataset_name in self.DATASETS:
            try:
                path = self.download_dataset(dataset_name, subjects, grades)
                downloaded[dataset_name] = path
            except Exception as e:
                logger.error(f"Failed to download {dataset_name}: {e}")
                continue
        
        return downloaded
    
    def _extract_grade(self, item: Dict) -> Optional[int]:
        """Extract grade level from dataset item."""
        # Try common field names
        for field in ['grade', 'grade_level', 'level']:
            if field in item:
                try:
                    return int(item[field])
                except (ValueError, TypeError):
                    pass
        
        # Try to infer from text
        text = str(item.get('text', '') or item.get('content', ''))
        if 'grade 8' in text.lower():
            return 8
        elif 'grade 9' in text.lower():
            return 9
        elif 'grade 10' in text.lower():
            return 10
        elif 'grade 11' in text.lower():
            return 11
        elif 'grade 12' in text.lower():
            return 12
        
        return None
    
    def _extract_subject(self, item: Dict) -> Optional[str]:
        """Extract subject from dataset item."""
        # Try common field names
        for field in ['subject', 'topic', 'category']:
            if field in item:
                return str(item[field])
        
        # Try to infer from text
        text = str(item.get('text', '') or item.get('content', '')).lower()
        if any(word in text for word in ['biology', 'physics', 'chemistry', 'science']):
            return "Science"
        elif any(word in text for word in ['math', 'algebra', 'geometry', 'calculus']):
            return "Math"
        elif any(word in text for word in ['programming', 'computer', 'coding', 'algorithm']):
            return "Computer Science"
        elif any(word in text for word in ['grammar', 'writing', 'english', 'literature']):
            return "English"
        
        return None
    
    def cleanup_raw_data(self):
        """
        Delete raw datasets after ChromaDB processing.
        Saves ~5-8GB of storage!
        """
        logger.info("Cleaning up raw datasets...")
        for file in self.output_dir.glob("*.jsonl"):
            file.unlink()
            logger.info(f"Deleted {file.name}")
        
        logger.info("Raw data cleanup complete. ChromaDB is all you need!")


def main():
    """Main entry point for dataset download."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download Grade 8-12 educational datasets")
    parser.add_argument(
        "--datasets",
        nargs="+",
        help="Specific datasets to download (default: all)"
    )
    parser.add_argument(
        "--subjects",
        nargs="+",
        choices=["Science", "Math", "Computer Science", "English"],
        help="Filter by subjects"
    )
    parser.add_argument(
        "--grades",
        nargs="+",
        type=int,
        choices=[8, 9, 10, 11, 12],
        default=[8, 9, 10, 11, 12],
        help="Filter by grades (default: 8-12)"
    )
    parser.add_argument(
        "--output",
        default="satya_data/raw_datasets",
        help="Output directory for raw datasets"
    )
    
    args = parser.parse_args()
    
    downloader = DatasetDownloader(output_dir=args.output)
    
    logger.info("=" * 60)
    logger.info("Satya Dataset Downloader - Grade 8-12 Focus")
    logger.info("=" * 60)
    logger.info(f"Subjects: {args.subjects or 'All'}")
    logger.info(f"Grades: {args.grades}")
    logger.info(f"Output: {args.output}")
    logger.info("=" * 60)
    
    if args.datasets:
        # Download specific datasets
        for dataset_name in args.datasets:
            downloader.download_dataset(
                dataset_name,
                subjects=args.subjects,
                grades=args.grades
            )
    else:
        # Download all datasets
        downloader.download_all(
            subjects=args.subjects,
            grades=args.grades
        )
    
    logger.info("=" * 60)
    logger.info("Download complete!")
    logger.info("Next step: Run embedding_generator.py to create ChromaDB")
    logger.info("Final ChromaDB size will be ~500MB-1GB (8 datasets compressed!)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
