"""
RAG Data Preparation Pipeline

This pipeline processes PDFs directly to chunks without intermediate text extraction files.
Optimized for performance and minimal storage usage.
"""

import os
import logging
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from datetime import datetime
import re
import io
import base64  # For Chroma database embeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Efficient PDF processor that extracts text and creates chunks in one pass.
    No intermediate files are saved.
    """
    
    def __init__(self, output_dir: str, language: str = "en", chunk_size: int = 600, overlap: int = 100):
        """
        Initialize PDF processor.
        
        Args:
            output_dir: Directory to save chunks
            language: Language for OCR (en, ne, hi)
            chunk_size: Target chunk size in words
            overlap: Overlap size in words
        """
        self.output_dir = output_dir
        self.language = language
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = 200
        
        # OCR configuration
        self.ocr_config = self._get_ocr_config()
        
        # Create output directories
        self._create_output_dirs()
    
    def _create_output_dirs(self):
        """Create necessary output directories."""
        dirs = [
            self.output_dir,
            f"{self.output_dir}/chunks",
            f"{self.output_dir}/images",
            f"{self.output_dir}/reports",
            f"{self.output_dir}/logs"
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def _get_ocr_config(self) -> str:
        """Get OCR configuration based on language."""
        configs = {
            "en": "--oem 3 --psm 6",
            "ne": "--oem 3 --psm 6 -l nep",
            "hi": "--oem 3 --psm 6 -l hin"
        }
        return configs.get(self.language, configs["en"])
    
    def process_pdf_to_chunks(self, pdf_path: str, subject: str, grade: str) -> Dict:
        """
        Process PDF directly to chunks in one pass.
        
        Args:
            pdf_path: Path to PDF file
            subject: Subject name
            grade: Grade level
            
        Returns:
            Dictionary containing chunks and metadata
        """
        logger.info(f"Processing PDF to chunks: {pdf_path}")
        
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            
            # Extract basic metadata
            metadata = self._extract_pdf_metadata(doc, subject, grade)
            
            # Process each page and create chunks
            all_chunks = []
            all_images = []
            page_metadata = []
            chunk_id = 1
            
            for page_num in range(len(doc)):
                logger.info(f"Processing page {page_num + 1}/{len(doc)}")
                
                page = doc.load_page(page_num)
                
                # Extract text from page
                text_content = self._extract_page_text(page, page_num)
                
                # Extract images from page
                images = self._extract_page_images(page, page_num, subject)
                
                # Create chunks from this page
                page_chunks = []  # Initialize page_chunks
                if text_content.strip():
                    page_chunks = self._chunk_page_text(
                        text_content, page_num + 1, chunk_id, subject, grade, metadata
                    )
                    all_chunks.extend(page_chunks)
                    chunk_id += len(page_chunks)
                
                # Store page metadata
                page_metadata.append({
                    "page_number": page_num + 1,
                    "text_length": len(text_content),
                    "image_count": len(images),
                    "chunks_created": len(page_chunks)
                })
                
                all_images.extend(images)
            
            # Save chunks with image references
            chunks_file = self._save_chunks(all_chunks, all_images, subject, grade)
            
            # Store total pages before closing document
            total_pages = len(doc)
            
            # Save metadata
            metadata_file = self._save_metadata(metadata, page_metadata, all_chunks, all_images)
            
            doc.close()
            
            logger.info(f"Successfully processed {pdf_path} to {len(all_chunks)} chunks")
            
            return {
                "success": True,
                "chunks_file": chunks_file,
                "metadata_file": metadata_file,
                "total_chunks": len(all_chunks),
                "total_images": len(all_images),
                "total_pages": total_pages,
                "chunks": all_chunks,
                "images": all_images,  # Image data ready for Chroma
                "ready_for_chroma": True
            }
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            raise
    
    def _extract_pdf_metadata(self, doc, subject: str, grade: str) -> Dict:
        """Extract metadata from PDF."""
        metadata = doc.metadata
        
        return {
            "subject": subject,
            "grade": grade,
            "language": self.language,
            "total_pages": len(doc),
            "title": metadata.get("title", f"{subject}_grade_{grade}"),
            "author": metadata.get("author", "Unknown"),
            "creator": metadata.get("creator", "Unknown"),
            "producer": metadata.get("producer", "Unknown"),
            "creation_date": metadata.get("creationDate", ""),
            "modification_date": metadata.get("modDate", ""),
            "processing_date": datetime.now().isoformat(),
            "file_size_mb": os.path.getsize(doc.name) / (1024 * 1024) if doc.name else 0
        }
    
    def _extract_page_text(self, page, page_num: int) -> str:
        """Extract text from a page with OCR fallback."""
        # Try direct text extraction first
        text = page.get_text()
        
        # If no text found, use OCR
        if not text.strip():
            logger.info(f"Using OCR for page {page_num + 1}")
            text = self._ocr_page_text(page)
        
        return text
    
    def _ocr_page_text(self, page) -> str:
        """Extract text using OCR."""
        try:
            # Convert page to image
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            img = Image.open(io.BytesIO(img_data))
            
            # Perform OCR
            text = pytesseract.image_to_string(img, config=self.ocr_config)
            
            return text
            
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return ""
    
    def _extract_page_images(self, page, page_num: int, subject: str) -> List[Dict]:
        """Extract images from a page and save as files."""
        images = []
        
        try:
            # Get image list
            image_list = page.get_images()
            logger.info(f"Found {len(image_list)} images on page {page_num + 1}")
            
            for img_index, img in enumerate(image_list):
                logger.info(f"Processing image {img_index + 1} on page {page_num + 1}")
                # Get image data
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                
                if pix.n - pix.alpha < 4:  # Skip alpha channel
                    # Convert to RGB
                    pix1 = fitz.Pixmap(fitz.csRGB, pix)
                    img_data = pix1.tobytes("png")
                    
                    # Create subject-specific image folder and filename
                    subject_img_folder = os.path.join(self.output_dir, "images", subject)
                    os.makedirs(subject_img_folder, exist_ok=True)
                    
                    img_filename = f"page_{page_num + 1}_img_{img_index + 1}.png"
                    img_filepath = os.path.join(subject_img_folder, img_filename)
                    
                    # Save image to file
                    with open(img_filepath, 'wb') as img_file:
                        img_file.write(img_data)
                    
                    logger.info(f"Successfully saved image {img_index + 1}: {subject}/{img_filename} ({pix1.width}x{pix1.height}, {len(img_data)} bytes)")
                    
                    # Store image metadata with both file path and base64 data
                    images.append({
                        "image_filename": img_filename,
                        "image_path": img_filepath,
                        "image_folder": subject,
                        "image_data": base64.b64encode(img_data).decode('utf-8'),  # Base64 for Chroma
                        "page_number": page_num + 1,
                        "image_index": img_index + 1,
                        "size_bytes": len(img_data),
                        "width": pix1.width,
                        "height": pix1.height,
                        "subject": subject,
                        "chunk_id": f"{subject}_page_{page_num + 1}_img_{img_index + 1}"
                    })
                    
                    pix1 = None
                else:
                    logger.info(f"Skipping image {img_index + 1} (alpha channel)")
                
                pix = None
            
        except Exception as e:
            logger.warning(f"Image extraction failed for page {page_num + 1}: {e}")
        
        logger.info(f"Extracted and saved {len(images)} images from page {page_num + 1}")
        return images
    
    def _chunk_page_text(self, page_text: str, page_num: int, start_chunk_id: int,
                        subject: str, grade: str, metadata: Dict) -> List[Dict]:
        """Chunk a single page of text."""
        
        # Clean and normalize text
        cleaned_text = self._clean_text(page_text)
        
        # Split into sentences for better chunking
        sentences = self._split_into_sentences(cleaned_text)
        
        # Create chunks with overlap
        chunks = []
        current_chunk = []
        current_word_count = 0
        chunk_id = start_chunk_id
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # If adding this sentence would exceed chunk size
            if current_word_count + sentence_words > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                if len(chunk_text.split()) >= self.min_chunk_size:
                    chunk_data = self._create_chunk_data(
                        chunk_text, page_num, chunk_id, subject, grade, metadata
                    )
                    chunks.append(chunk_data)
                    chunk_id += 1
                
                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(current_chunk)
                current_chunk = overlap_sentences + [sentence]
                current_word_count = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_words
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text.split()) >= self.min_chunk_size:
                chunk_data = self._create_chunk_data(
                    chunk_text, page_num, chunk_id, subject, grade, metadata
                )
                chunks.append(chunk_data)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page headers/footers
        text = re.sub(r'Page \d+', '', text)
        
        # Clean up common OCR artifacts
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]]+', ' ', text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        
        # Clean up sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence.split()) > 2:  # Minimum 3 words
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get sentences for overlap based on word count."""
        overlap_words = 0
        overlap_sentences = []
        
        for sentence in reversed(sentences):
            sentence_words = len(sentence.split())
            if overlap_words + sentence_words <= self.overlap:
                overlap_sentences.insert(0, sentence)
                overlap_words += sentence_words
            else:
                break
        
        return overlap_sentences
    
    def _create_chunk_data(self, chunk_text: str, page_num: int, chunk_id: int,
                          subject: str, grade: str, metadata: Dict) -> Dict:
        """Create chunk data with metadata."""
        
        return {
            "chunk_id": f"{subject}_grade{grade}_chunk_{chunk_id:04d}",
            "text": chunk_text,
            "word_count": len(chunk_text.split()),
            "page_number": page_num,
            "subject": subject,
            "grade": grade,
            "language": metadata.get("language", "en"),
            "metadata": {
                "source_pdf": metadata.get("title", ""),
                "creation_date": metadata.get("creation_date", ""),
                "processing_date": datetime.now().isoformat(),
                "chunk_size": self.chunk_size,
                "overlap": self.overlap
            }
        }
    
    def _save_chunks(self, chunks: List[Dict], images: List[Dict], subject: str, grade: str) -> str:
        """Save chunks to JSON file with complete metadata and image data for Chroma."""
        filename = f"{subject}_grade_{grade}_chunks.json"
        filepath = os.path.join(self.output_dir, "chunks", filename)
        
        # Create complete chunks data with everything needed for Chroma
        chunks_data = {
            "text_chunks": chunks,
            "image_metadata": images,  # Complete image data with base64
            "processing_metadata": {
                "subject": subject,
                "grade": grade,
                "total_chunks": len(chunks),
                "total_images": len(images),
                "chunking_parameters": {
                    "chunk_size": self.chunk_size,
                    "overlap": self.overlap,
                    "min_chunk_size": self.min_chunk_size
                },
                "processing_date": datetime.now().isoformat()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _save_metadata(self, metadata: Dict, page_metadata: List[Dict], 
                       chunks: List[Dict], images: List[Dict]) -> str:
        """Save basic processing statistics only."""
        filename = f"{metadata['subject']}_grade_{metadata['grade']}_processing_report.json"
        filepath = os.path.join(self.output_dir, "reports", filename)
        
        # Only save basic processing statistics, not the actual content
        processing_report = {
            "processing_summary": {
                "subject": metadata['subject'],
                "grade": metadata['grade'],
                "language": metadata['language'],
                "total_pages": metadata.get('total_pages', 0),
                "total_chunks": len(chunks),
                "total_images": len(images),
                "processing_date": datetime.now().isoformat()
            },
            "file_locations": {
                "chunks_file": f"chunks/{metadata['subject']}_grade_{metadata['grade']}_chunks.json",
                "images_folder": f"images/{metadata['subject']}/",
                "total_image_files": len(images)
            },
            "chunking_parameters": {
                "chunk_size": self.chunk_size,
                "overlap": self.overlap,
                "min_chunk_size": self.min_chunk_size
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(processing_report, f, indent=2, ensure_ascii=False)
        
        return filepath

    def prepare_for_chroma(self, chunks: List[Dict], images: List[Dict]) -> Dict:
        """
        Prepare data for Chroma database integration.
        
        Args:
            chunks: List of text chunks
            images: List of image data
            
        Returns:
            Dictionary ready for Chroma database
        """
        chroma_data = {
            "documents": [],
            "metadatas": [],
            "ids": [],
            "images": []
        }
        
        # Prepare text chunks for Chroma
        for chunk in chunks:
            chroma_data["documents"].append(chunk["text"])
            chroma_data["metadatas"].append({
                "chunk_id": chunk["chunk_id"],
                "subject": chunk["subject"],
                "grade": chunk["grade"],
                "language": chunk["language"],
                "page_number": chunk["page_number"],
                "word_count": chunk["word_count"],
                "type": "text"
            })
            chroma_data["ids"].append(chunk["chunk_id"])
        
        # Prepare images for Chroma (will be converted to embeddings)
        for img in images:
            with open(img["image_path"], "rb") as img_file:
                img_data_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            chroma_data["images"].append({
                "image_data": img_data_base64,
                "chunk_id": img["chunk_id"],
                "metadata": {
                    "chunk_id": img["chunk_id"],
                    "subject": img["subject"],
                    "grade": "10",
                    "language": self.language,
                    "page_number": img["page_number"],
                    "image_index": img["image_index"],
                    "size_bytes": img["size_bytes"],
                    "width": img["width"],
                    "height": img["height"],
                    "type": "image"
                }
            })
        
        return chroma_data 

    def run_pipeline(self, subjects: List[str] = None) -> Dict:
        """
        Run the complete pipeline for Grade 10 content processing.
        
        Args:
            subjects: List of subjects to process (computer_science, english, science)
            
        Returns:
            Dictionary containing pipeline results
        """
        if subjects is None:
            subjects = ["computer_science", "english", "science"]
        
        logger.info(f"Starting Grade 10 content processing for subjects: {subjects}")
        
        # Pipeline results
        results = {
            "pipeline_start": datetime.now().isoformat(),
            "language": self.language,
            "subjects_processed": [],
            "total_chunks": 0,
            "total_images": 0,
            "errors": []
        }
        
        for subject in subjects:
            try:
                logger.info(f"Processing subject: {subject}")
                
                # Process subject directly to chunks
                subject_result = self._process_subject(subject, "10")
                
                # Update results
                results["subjects_processed"].append(subject_result)
                results["total_chunks"] += subject_result.get("total_chunks", 0)
                results["total_images"] += subject_result.get("total_images", 0)
                
                logger.info(f"✅ Completed processing {subject}")
                
            except Exception as e:
                error_msg = f"Error processing {subject}: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        # Generate final report
        self._generate_final_report(results)
        
        logger.info("🎉 Data preparation pipeline completed!")
        return results
    
    def _process_subject(self, subject: str, grade: str) -> Dict:
        """
        Process a single subject directly to chunks.
        
        Args:
            subject: Subject name
            grade: Grade level
            
        Returns:
            Dictionary containing processing results
        """
        logger.info(f"Processing {subject} for grade {grade}")
        
        # Find PDF file for this subject
        pdf_file = self._find_pdf_file(subject, grade)
        if not pdf_file:
            raise FileNotFoundError(f"PDF file not found for {subject} grade {grade}")
        
        # Process PDF directly to chunks (no intermediate files)
        logger.info(f"Processing PDF directly to chunks: {pdf_file}")
        result = self.process_pdf_to_chunks(pdf_file, subject, grade)
        
        logger.info(f"Created {result['total_chunks']} chunks for {subject} grade {grade}")
        
        return result
    
    def _find_pdf_file(self, subject: str, grade: str) -> str:
        """Find PDF file for the given subject and grade."""
        # Look for PDF files with subject and grade in filename
        possible_names = [
            f"{subject}_grade_{grade}.pdf",
            f"{subject}_grade{grade}.pdf",
            f"{subject}_{grade}.pdf",
            f"{subject}.pdf"
        ]
        
        for filename in possible_names:
            filepath = os.path.join(self.output_dir, "..", "..", "textbooks", filename)
            if os.path.exists(filepath):
                return filepath
        
        # If not found, list available files
        textbooks_dir = os.path.join(self.output_dir, "..", "..", "textbooks")
        if os.path.exists(textbooks_dir):
            available_files = [f for f in os.listdir(textbooks_dir) if f.endswith('.pdf')]
            logger.warning(f"PDF not found for {subject} grade {grade}. Available files: {available_files}")
        
        return None
    
    def _generate_final_report(self, results: Dict):
        """Generate final pipeline report."""
        results["pipeline_end"] = datetime.now().isoformat()
        
        # Calculate statistics
        total_subjects = len(results["subjects_processed"])
        successful_subjects = len([s for s in results["subjects_processed"] if "error" not in s])
        
        results["statistics"] = {
            "total_subjects": total_subjects,
            "successful_subjects": successful_subjects,
            "failed_subjects": total_subjects - successful_subjects,
            "total_chunks": results["total_chunks"],
            "total_images": results["total_images"],
            "average_chunks_per_subject": results["total_chunks"] / successful_subjects if successful_subjects > 0 else 0
        }
        
        # Save final report
        report_file = os.path.join(self.output_dir, "reports", "pipeline_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Final report saved to {report_file}")
        
        # Print summary
        self._print_summary(results)
    
    def _print_summary(self, results: Dict):
        """Print pipeline summary."""
        stats = results["statistics"]
        
        print("\n" + "="*60)
        print("🎓 RAG DATA PREPARATION PIPELINE SUMMARY")
        print("="*60)
        print(f"📚 Subjects Processed: {stats['successful_subjects']}/{stats['total_subjects']}")
        print(f"📝 Total Chunks Created: {stats['total_chunks']:,}")
        print(f"🖼️  Total Images Extracted: {stats['total_images']:,}")
        print(f"📊 Average Chunks per Subject: {stats['average_chunks_per_subject']:.1f}")
        
        if results["errors"]:
            print(f"\n❌ Errors Encountered: {len(results['errors'])}")
            for error in results["errors"]:
                print(f"   - {error}")
        
        print(f"\n📁 Output Directory: {self.output_dir}")
        print("🚀 No intermediate files - direct PDF to chunks!")
        print("="*60) 