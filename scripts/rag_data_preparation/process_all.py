#!/usr/bin/env python3
"""
Process All Content: Textbooks + Notes

This script processes both textbooks and notes, then adds them to ChromaDB.
It's a one-stop solution for setting up your RAG system.

Usage:
    python process_all.py                    # Process everything
    python process_all.py --textbooks-only   # Only textbooks
    python process_all.py --notes-only      # Only notes
    python process_all.py --skip-embeddings # Process but don't add to ChromaDB
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.rag_data_preparation.pdf_processor import PDFProcessor
from scripts.rag_data_preparation.embedding_generator import EmbeddingGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_textbooks(output_dir: str = "processed_data_new", generate_embeddings: bool = True):
    """
    Process all textbooks from textbooks/grade_10/ directory.
    
    Args:
        output_dir: Output directory for processed chunks
        generate_embeddings: Whether to generate embeddings and add to ChromaDB
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("📚 PROCESSING TEXTBOOKS")
    logger.info("=" * 60)
    
    try:
        # Initialize PDF processor
        processor = PDFProcessor(
            output_dir=output_dir,
            language="en",
            chunk_size=400,
            overlap=50
        )
        
        # Run pipeline for all subjects
        logger.info("Processing textbooks from: textbooks/grade_10/")
        results = processor.run_pipeline(
            subjects=["computer_science", "english", "science"]
        )
        
        if not results.get("subjects_processed"):
            logger.error("❌ No textbooks processed!")
            return False
        
        logger.info(f"✅ Processed {results['total_chunks']} textbook chunks")
        logger.info(f"✅ Extracted {results['total_images']} images")
        
        # Generate embeddings and add to ChromaDB
        if generate_embeddings:
            logger.info("\n" + "=" * 60)
            logger.info("🔗 GENERATING EMBEDDINGS FOR TEXTBOOKS")
            logger.info("=" * 60)
            
            generator = EmbeddingGenerator()
            
            # Process each subject's chunks
            for subject_result in results.get("subjects_processed", []):
                if not subject_result.get("success"):
                    continue
                
                subject = subject_result.get("subject", "unknown")
                chunks_file = subject_result.get("chunks_file")
                
                if chunks_file and os.path.exists(chunks_file):
                    logger.info(f"Processing embeddings for {subject}...")
                    success = generator.process_text_chunks(
                        chunks_file=chunks_file,
                        subject=subject,
                        content_type="book"
                    )
                    
                    if success:
                        logger.info(f"✅ {subject} textbook embeddings added to ChromaDB")
                    else:
                        logger.error(f"❌ Failed to add {subject} textbook embeddings")
                else:
                    logger.warning(f"⚠️  Chunks file not found for {subject}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error processing textbooks: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def process_notes(output_dir: str = "processed_data_new", generate_embeddings: bool = True):
    """
    Process all notes from notes/grade_10/ directory.
    
    Args:
        output_dir: Output directory for processed chunks
        generate_embeddings: Whether to generate embeddings and add to ChromaDB
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("📝 PROCESSING NOTES")
    logger.info("=" * 60)
    
    try:
        notes_dir = Path("notes/grade_10")
        
        if not notes_dir.exists():
            logger.warning(f"⚠️  Notes directory not found: {notes_dir}")
            logger.info("💡 Create notes/grade_10/ and add your notes PDFs there")
            return True  # Not an error, just no notes to process
        
        # Find all PDF files
        pdf_files = list(notes_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"⚠️  No PDF files found in {notes_dir}")
            logger.info("💡 Add your notes PDFs to notes/grade_10/")
            return True  # Not an error, just no notes to process
        
        logger.info(f"Found {len(pdf_files)} notes files to process")
        
        # Initialize processors
        processor = PDFProcessor(
            output_dir=output_dir,
            language="en",
            chunk_size=400,
            overlap=50
        )
        
        generator = EmbeddingGenerator() if generate_embeddings else None
        
        subjects = ["computer_science", "english", "science"]
        processed_count = 0
        
        for pdf_file in pdf_files:
            # Try to infer subject from filename
            filename_lower = pdf_file.stem.lower()
            subject = None
            
            for subj in subjects:
                if subj.replace("_", "") in filename_lower or subj in filename_lower:
                    subject = subj
                    break
            
            if not subject:
                # Default to first subject if can't infer
                subject = subjects[0]
                logger.warning(f"⚠️  Could not infer subject from {pdf_file.name}, using: {subject}")
            
            logger.info(f"\n📄 Processing: {pdf_file.name} (Subject: {subject})")
            
            # Process PDF
            result = processor.process_pdf_to_chunks(
                pdf_path=str(pdf_file),
                subject=subject,
                grade="10"
            )
            
            if not result.get("success"):
                logger.error(f"❌ Failed to process {pdf_file.name}")
                continue
            
            logger.info(f"✅ Processed {result['total_chunks']} chunks from {pdf_file.name}")
            
            # Generate embeddings
            if generate_embeddings and generator:
                chunks_file = result.get('chunks_file')
                if chunks_file and os.path.exists(chunks_file):
                    success = generator.process_text_chunks(
                        chunks_file=chunks_file,
                        subject=subject,
                        content_type="notes"
                    )
                    
                    if success:
                        logger.info(f"✅ {pdf_file.name} notes added to ChromaDB")
                        processed_count += 1
                    else:
                        logger.error(f"❌ Failed to add {pdf_file.name} to ChromaDB")
        
        if processed_count > 0:
            logger.info(f"\n✅ Successfully processed {processed_count} notes files")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error processing notes: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Process all content (textbooks + notes) for RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process everything (textbooks + notes)
  python process_all.py
  
  # Only process textbooks
  python process_all.py --textbooks-only
  
  # Only process notes
  python process_all.py --notes-only
  
  # Process but don't generate embeddings
  python process_all.py --skip-embeddings
        """
    )
    
    parser.add_argument(
        "--textbooks-only",
        action="store_true",
        help="Only process textbooks, skip notes"
    )
    
    parser.add_argument(
        "--notes-only",
        action="store_true",
        help="Only process notes, skip textbooks"
    )
    
    parser.add_argument(
        "--skip-embeddings",
        action="store_true",
        help="Process PDFs but don't generate embeddings (useful for testing)"
    )
    
    parser.add_argument(
        "--output-dir",
        default="processed_data_new",
        help="Output directory for processed chunks (default: processed_data_new)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🚀 SATYA RAG CONTENT PROCESSING")
    logger.info("=" * 60)
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Generate embeddings: {not args.skip_embeddings}")
    logger.info("")
    
    success = True
    
    # Process textbooks
    if not args.notes_only:
        success = process_textbooks(
            output_dir=args.output_dir,
            generate_embeddings=not args.skip_embeddings
        ) and success
    
    # Process notes
    if not args.textbooks_only:
        success = process_notes(
            output_dir=args.output_dir,
            generate_embeddings=not args.skip_embeddings
        ) and success
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 PROCESSING SUMMARY")
    logger.info("=" * 60)
    
    if not args.skip_embeddings:
        try:
            generator = EmbeddingGenerator()
            info = generator.get_collection_info()
            
            logger.info("\nChromaDB Collections:")
            for collection_name, data in info.items():
                count = data.get("count", 0)
                logger.info(f"  📚 {collection_name}: {count} chunks")
        except Exception as e:
            logger.warning(f"Could not get collection info: {e}")
    
    if success:
        logger.info("\n✅ All processing completed successfully!")
        logger.info("\n💡 Next steps:")
        logger.info("   - Your content is now in ChromaDB")
        logger.info("   - Start using the RAG system in your application")
        logger.info("   - Both books and notes are searchable together")
        return 0
    else:
        logger.error("\n❌ Some processing failed. Check logs above.")
        return 1

if __name__ == "__main__":
    exit(main())

